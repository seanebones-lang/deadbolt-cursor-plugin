"""Exercise the exported plugin command, never a real account or model."""
import hashlib
from contextlib import closing
import io
import json
import os
from pathlib import Path
import platform
import queue
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import time
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
checks = []
effect_results = []


def passed(name):
    checks.append({"case": name, "passed": True})


def verify():
    source = json.loads((ROOT / "BUNDLE-SOURCE.json").read_text())
    with urlopen(source["url"], timeout=45) as response:
        archive = response.read(10_000_000)
    assert hashlib.sha256(archive).hexdigest() == source["sha256"]
    with ZipFile(io.BytesIO(archive)) as release:
        assert set(release.namelist()) == {str(p.relative_to(ROOT / 'bundle')).replace('\\', '/') for p in (ROOT / 'bundle').rglob('*') if p.is_file()}
        for name in release.namelist():
            assert release.read(name) == (ROOT / 'bundle' / name).read_bytes(), name
    passed("every_bundle_member_matches_the_pinned_published_archive")
    manifest = json.loads((ROOT / '.cursor-plugin/plugin.json').read_text())
    marketplace = json.loads((ROOT / '.cursor-plugin/marketplace.json').read_text())
    assert marketplace['name'] == 'nexteleven-deadbolt'
    assert len(marketplace['plugins']) == 1
    candidate = marketplace['plugins'][0]
    assert candidate['name'] == manifest['name']
    assert candidate['source'] == '.'
    assert (ROOT / candidate['source'] / '.cursor-plugin/plugin.json').resolve() == (ROOT / '.cursor-plugin/plugin.json').resolve()
    passed('local_repository_marketplace_resolves_the_exported_plugin')
    entry = json.loads((ROOT / 'mcp.json').read_text())['mcpServers']['deadbolt']
    assert manifest['variables']['properties']['DEADBOLT_OPERATOR_CONFIG']['default'] == ''
    assert not manifest['variables'].get('required')
    assert entry['args'] == ['${CURSOR_PLUGIN_ROOT}/server/entry.cjs']
    assert entry['env'] == {'DEADBOLT_OPERATOR_CONFIG': '${DEADBOLT_OPERATOR_CONFIG}'}
    assert (ROOT / manifest['logo']).is_file()
    assert not (ROOT / 'hooks').exists(), 'No automatic workspace actions'
    command = [shutil.which(entry['command']), entry['args'][0].replace('${CURSOR_PLUGIN_ROOT}', str(ROOT))]
    assert command[0]
    targets = {('Darwin', 'arm64'): 'aarch64-apple-darwin', ('Darwin', 'x86_64'): 'x86_64-apple-darwin', ('Linux', 'x86_64'): 'x86_64-unknown-linux-gnu', ('Windows', 'AMD64'): 'x86_64-pc-windows-msvc'}
    binary = ROOT / 'bundle/native' / targets[(platform.system(), platform.machine())] / ('deadbolt.exe' if os.name == 'nt' else 'deadbolt')
    if os.name != 'nt': binary.chmod(0o755)
    passed('exported_manifest_paths_variable_and_default_setup_mode')
    with tempfile.TemporaryDirectory(prefix='deadbolt-plugin disposable ') as temporary:
        work = Path(temporary).resolve()
        fixture = work / 'fixture.cjs'
        starts, effects = work / 'started.txt', work / 'effects.txt'
        fixture.write_text("""const fs=require('node:fs'); const readline=require('node:readline');
fs.appendFileSync(process.argv[2],'started\\n');
readline.createInterface({input:process.stdin}).on('line',line=>{
const r=JSON.parse(line); if(!Object.hasOwn(r,'id')) return; let result={};
if(r.method==='initialize') result={protocolVersion:'2025-03-26',capabilities:{tools:{}},serverInfo:{name:'disposable-plugin-fixture',version:'1.0.0'}};
else if(r.method==='tools/list') result={tools:['echo','write_marker','off_list'].map(name=>({name,description:'Disposable tool',inputSchema:{type:'object',properties:{},additionalProperties:true}}))};
else if(r.method==='tools/call'){fs.appendFileSync(process.argv[3],r.params.name+'\\n');result={content:[{type:'text',text:'dummy effect completed'}]};}
process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:r.id,result})+'\\n');});
""")
        config = {'version': 2, 'hard_deadline_at': int(time.time()) + 600, 'renewal_mode': 'activity', 'offline_tools': ['echo', 'write_marker'], 'agent': 'plugin-disposable-run', 'database': str(work / 'state.db'), 'events': str(work / 'events.jsonl'), 'command': command[0], 'args': [str(fixture), str(starts), str(effects)], 'tools': ['echo', 'write_marker'], 'destinations': [], 'irreversible_tools': ['write_marker'], 'spend_cap_usd': 10}
        file = work / 'operator.json'; file.write_text(json.dumps(config))
        processes = []
        def launch(value):
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith('DEADBOLT_')}
            if value is not None: env['DEADBOLT_OPERATOR_CONFIG'] = value
            proc = subprocess.Popen(command, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
            proc.responses = queue.Queue()
            def read():
                for line in proc.stdout: proc.responses.put(line)
            threading.Thread(target=read, daemon=True).start()
            processes.append(proc)
            return proc
        sequence = 0
        def rpc(proc, method, params=None):
            nonlocal sequence
            sequence += 1
            proc.stdin.write(json.dumps({'jsonrpc': '2.0', 'id': sequence, 'method': method, 'params': params or {}}) + '\n'); proc.stdin.flush()
            response = json.loads(proc.responses.get(timeout=15))
            assert response['id'] == sequence
            return response
        def stop(proc):
            proc.stdin.close()
            try: proc.wait(timeout=6)
            except subprocess.TimeoutExpired: proc.kill(); proc.wait(timeout=5)
            proc.stdout.close(); proc.stderr.close()
        def operator(*args):
            env = {k: v for k, v in os.environ.items() if not k.upper().startswith('DEADBOLT_')}
            env.update(DEADBOLT_DB=config['database'], DEADBOLT_EVENTS=config['events'])
            subprocess.run([str(binary), *args], env=env, check=True, capture_output=True, timeout=15)
        try:
            for label, value in [('absent', None), ('blank', ''), ('optional_placeholder', '${DEADBOLT_OPERATOR_CONFIG}')]:
                proc = launch(value)
                assert rpc(proc, 'initialize')['result']['serverInfo']['name'] == 'deadbolt-setup'
                tools = rpc(proc, 'tools/list')['result']['tools']
                assert len(tools) == 2 and all(t['annotations']['readOnlyHint'] for t in tools)
                if label == 'absent':
                    for route in ['claude_desktop', 'stdio_client', 'rust', 'http']:
                        guide = rpc(proc, 'tools/call', {'name': 'deadbolt_get_integration_guide', 'arguments': {'route': route}})['result']['structuredContent']
                        assert guide['route'] == route and guide['steps'] and guide['boundary']
                    passed('all_four_read_only_integration_routes_return_guidance')
                result = rpc(proc, 'tools/call', {'name': 'deadbolt_check_bundle', 'arguments': {}})['result']['structuredContent']
                assert result['checksum_matches'] and result['active_protection'] is False
                assert result['engine_version'] == source['engine_version']
                assert 'error' in rpc(proc, 'tools/call', {'name': 'kill', 'arguments': {}})
                assert not starts.exists() and not Path(config['database']).exists()
                stop(proc); passed('read_only_no_effect_setup_' + label)
            for label, value in [('relative', 'operator.json'), ('missing', str(work / 'missing.json'))]:
                proc = launch(value); proc.wait(timeout=10)
                assert proc.returncode != 0 and not starts.exists()
                stop(proc); passed('invalid_supplied_config_refused_' + label)
            proc = launch(str(file))
            assert rpc(proc, 'initialize')['result']['serverInfo']['name'] == 'disposable-plugin-fixture'
            names = [t['name'] for t in rpc(proc, 'tools/list')['result']['tools']]
            assert 'echo' in names and not any(n.startswith('deadbolt_') for n in names)
            passed('configured_plugin_exposes_only_downstream_tools')
            def call(name, expect_effect, deny=None, arguments=None):
                before = effects.read_text() if effects.exists() else ''
                response = rpc(proc, 'tools/call', {'name': name, 'arguments': arguments or {}})
                after = effects.read_text() if effects.exists() else ''
                if expect_effect:
                    assert 'result' in response and after == before + name + '\n'
                else:
                    assert after == before and 'error' not in response and response['result']['isError'] is True, response
                    meta = response['result']['_meta']['io.github.seanebones-lang/deadbolt']
                    if deny: assert meta['code'] == deny, response
                    assert response['result']['content'][0]['text'].startswith('DeadBolt denied: ' + meta['code'] + '.'), response
                    expected_retry = ('never' if meta['code'] in ('killed', 'lease_expired', 'deadline_exceeded') else 'after_operator_resume' if meta['code'] == 'paused' else 'after_service_recovery' if meta['code'] == 'store_unavailable' else 'after_operator_intervention')
                    assert meta['retry'] == expected_retry, response
                effect_results.append({'tool': name, 'allowed': expect_effect, 'body_ran': before != after, 'deny': deny})
            call('echo', True); passed('allowed_call_performs_actual_marker_effect')
            call('off_list', False, 'purpose_exceeded'); passed('off_policy_call_performs_no_effect')
            call('write_marker', False, 'needs_human'); passed('irreversible_call_requires_operator_grant')
            operator('approve', '--agent', config['agent'], '--tool', 'write_marker')
            call('write_marker', True); call('write_marker', False, 'needs_human'); passed('operator_grant_allows_one_actual_effect_and_refuses_replay')
            operator('pause', '--agent', config['agent']); call('echo', False, 'paused'); passed('pause_blocks_next_effect')
            operator('resume', '--agent', config['agent']); call('echo', True); passed('resume_restores_allowed_effect')
            operator('clip', 'echo', '--agent', config['agent']); call('echo', False, 'purpose_exceeded'); passed('clip_blocks_selected_tool')
            operator('resume', '--agent', config['agent'])
            with closing(sqlite3.connect(config['database'])) as db:
                db.execute('UPDATE leases SET expires_at=0 WHERE agent_id=?', (config['agent'],))
                db.commit()
            call('echo', False, 'lease_expired'); passed('expired_lease_blocks_actual_effect')
            operator('kill', '--agent', config['agent']); call('echo', False, 'killed'); passed('terminal_kill_blocks_actual_effect')
            stop(proc)
            retained = Path(config['database']).read_bytes()
            before_starts = starts.read_text()
            proc = launch(str(file)); proc.wait(timeout=15)
            assert proc.returncode != 0 and starts.read_text() == before_starts
            stop(proc)
            assert Path(config['database']).exists() and retained
            passed('reconnect_does_not_revive_killed_identity_and_retains_operator_state')
            # No old configuration, implicit exception or changed fixed bound
            # may start downstream. These are disposable operator fixtures.
            for mutation in ({'version': 1}, {'tools': []}, {'offline_tools': ['off_list']},
                             {'hard_deadline_at': 0}, {'renewal_mode': 'anything'},
                             {'hard_deadline_at': config['hard_deadline_at'] + 60},
                             {'renewal_mode': 'supervisor'}):
                file.write_text(json.dumps({**config, **mutation}))
                proc = launch(str(file)); proc.wait(timeout=15)
                assert proc.returncode != 0 and starts.read_text() == before_starts
                stop(proc)
            passed('legacy_invalid_and_existing_bound_changes_refused_before_downstream_start')

            config.update(agent='plugin-destination-run', destinations=['allowed.example'],
                          offline_tools=[])
            file.write_text(json.dumps(config)); proc = launch(str(file))
            assert 'result' in rpc(proc, 'initialize')
            call('echo', False, 'purpose_exceeded')
            call('echo', False, 'purpose_exceeded', {'url': 'https://foreign.example/'})
            call('echo', True, arguments={'url': 'https://allowed.example/'})
            stop(proc); passed('all_routed_tools_require_allowed_destination_without_explicit_exception')
            config['offline_tools'] = ['echo']; file.write_text(json.dumps(config))
            proc = launch(str(file)); assert 'result' in rpc(proc, 'initialize')
            call('echo', True)
            call('echo', False, 'purpose_exceeded', {'url': 'https://foreign.example/'})
            stop(proc); passed('explicit_offline_exception_does_not_override_declared_foreign_destination')

            config.update(agent='plugin-supervisor-run', renewal_mode='supervisor')
            file.write_text(json.dumps(config)); proc = launch(str(file))
            assert 'result' in rpc(proc, 'initialize')
            with closing(sqlite3.connect(config['database'])) as db:
                expires = db.execute('SELECT expires_at FROM leases WHERE agent_id=?', (config['agent'],)).fetchone()[0]
            call('echo', True)
            with closing(sqlite3.connect(config['database'])) as db:
                assert db.execute('SELECT expires_at FROM leases WHERE agent_id=?', (config['agent'],)).fetchone()[0] == expires
                db.execute('UPDATE leases SET expires_at=0 WHERE agent_id=?', (config['agent'],)); db.commit()
            call('echo', False, 'lease_expired'); stop(proc)
            count = starts.read_text(); proc = launch(str(file)); proc.wait(timeout=15)
            assert proc.returncode != 0 and starts.read_text() == count; stop(proc)
            passed('supervised_admission_never_renews_and_expired_restart_refused')

            config.update(agent='plugin-deadline-run', renewal_mode='activity', hard_deadline_at=int(time.time())+4)
            file.write_text(json.dumps(config)); proc = launch(str(file))
            assert 'result' in rpc(proc, 'initialize'); call('echo', True)
            while time.time() < config['hard_deadline_at'] + .1: time.sleep(.1)
            call('echo', False, 'deadline_exceeded'); stop(proc)
            count = starts.read_text(); proc = launch(str(file)); proc.wait(timeout=15)
            assert proc.returncode != 0 and starts.read_text() == count; stop(proc)
            passed('real_fixed_deadline_denies_effect_and_restart_does_not_extend_it')

            config.update(agent='plugin-outage-run', hard_deadline_at=int(time.time())+600)
            file.write_text(json.dumps(config)); proc = launch(str(file))
            assert 'result' in rpc(proc, 'initialize'); call('echo', True)
            with closing(sqlite3.connect(config['database'])) as db:
                db.execute('DROP TABLE leases'); db.commit()
            call('echo', False, 'store_unavailable'); stop(proc)
            passed('running_connection_store_outage_denies_without_effect')
        finally:
            for proc in processes:
                if proc.poll() is None: stop(proc)
    return {'passed': True, 'platform': platform.system(), 'architecture': platform.machine(), 'scope': 'Exported Cursor plugin command and disposable protocol effects. No graphical/model-mediated Cursor test, no real accounts.', 'checks': checks, 'effect_calls': effect_results, 'operator_forced_idle_expiry': True, 'real_wall_clock_deadline': True}


if __name__ == '__main__':
    result = verify()
    (ROOT / 'acceptance-report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
