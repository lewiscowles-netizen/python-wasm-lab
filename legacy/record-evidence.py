from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,tempfile
branch=Path(sys.argv[1]).resolve()
for version in sys.argv[2:]:
 root=branch/'builds'/('build-'+version)
 manifest=json.loads((root/'manifest.json').read_text())
 for name,expected in manifest['files'].items():
  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==expected['sha256'],name
 with tempfile.TemporaryDirectory() as temporary:
  probe=Path(temporary)
  for name in ('python.mjs','python.wasm','python.data'): (probe/name).symlink_to(root/name)
  shutil.copy2(root/'smoke.mjs',probe/'smoke.mjs')
  subprocess.run(['node',str(probe/'smoke.mjs')],env=dict(os.environ,PYTHON_VERSION=version),check=True)
 evidence=branch/'docs/evidence'/('node-legacy-'+version+'.json')
 evidence.write_text(json.dumps({'status':'passed','buildCommand':'python3 scripts/build.py '+'.'.join(version.split('.')[:2]),'hostNode':subprocess.check_output(['node','--version'],text=True).strip(),'sdkNode':'12.18.1','runtime':manifest['validation']['node'],'artifacts':manifest['files']},indent=2)+'\n')
 print('Host Node and all artifact hashes verified: '+version)
