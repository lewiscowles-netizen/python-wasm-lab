from pathlib import Path
import json
import shutil
import subprocess
base=Path(__file__).resolve().parent
sdk='emscripten/emsdk:2.0.2@sha256:d2daf8d497c38f69e854239b06679184dcb676580fcb56146a3ad6f559b47aa6'
validation='''"""Reject disagreement between shared Buildx arguments and tested family pins."""
import json
import os
from pathlib import Path
manifest = json.loads(Path('/out/manifest.json').read_text())
lock = json.loads(Path('/recipe/versions.json').read_text())
family = json.loads(Path('/recipe/family.json').read_text())
version = manifest['version']
series = '.'.join(version.split('.')[:2])
if series not in family['series']:
    raise SystemExit('Unsupported release family: ' + series)
source = next(v for v in lock['versions'] if v['version'] == version)
expected = {'PYTHON_VERSION': version, 'PYTHON_SERIES': series,
            'PYTHON_URL': source['url'], 'PYTHON_SHA256': source['sha256']}
for key, value in expected.items():
    if os.environ.get(key) and os.environ[key] != value:
        raise SystemExit('Requested ' + key + ' disagrees with the pinned build')
if manifest['source'] != {'url': source['url'], 'sha256': source['sha256']}:
    raise SystemExit('Built source disagrees with shared versions.json')
if not manifest['validation']['node']['version'].startswith(version + ' '):
    raise SystemExit('Runtime version disagrees with source pin')
print('Verified shared source lock and runtime: ' + version)
'''
for directory, recipe, series, name in [('branch27',base,['2.7'],'legacy27'),('branch30_33',base/'early3',['3.0','3.1','3.2','3.3'],'early3')]:
    dest=base/directory
    for p in (dest/'scripts').iterdir():
        if p.name not in ('build.py','export-site.py') and p.is_file(): p.unlink()
    names=['Dockerfile','configure.sh','compile.sh','smoke.mjs','python.mjs','entropy.js','manifest.py','notices.py']
    names += ['build.sh'] if name=='legacy27' else ['link.sh','port.py','fetch.py','sources.json','emscripten-2.0.2.config.site']
    for file in names: shutil.copy2(recipe/file,dest/file)
    if name=='legacy27': shutil.copytree(base/'patches',dest/'patches',dirs_exist_ok=True)
    (dest/'validate-request.py').write_text(validation)
    (dest/'family.json').write_text(json.dumps({'name':name,'series':series,'defaultJobs':2,'platform':'linux/amd64','sdkImage':sdk},indent=2)+'\n')
    docker=(dest/'Dockerfile').read_text().replace('FROM configured AS build\n','FROM configured AS build\nARG JOBS=2\n')
    marker='FROM scratch AS artifacts'
    args='ARG PYTHON_SERIES\nARG PYTHON_URL\n'
    if name=='early3': args+='ARG PYTHON_SHA256\n'
    docker=docker.replace(marker,args+'COPY versions.json family.json validate-request.py /recipe/\nRUN python3 /recipe/validate-request.py\n'+marker)
    (dest/'Dockerfile').write_text(docker)
    allow=names+['versions.json','family.json','validate-request.py']
    if name=='legacy27': allow+=['patches','patches/**']
    (dest/'.dockerignore').write_text('*\n'+''.join('!'+file+'\n' for file in allow))
    (dest/'PORTING.md').write_text((base/'PORTING.md').read_text())
    # Use the common driver as the authoritative input to the committed Bake file.
    baked=json.loads(subprocess.check_output(['python3',str(dest/'scripts/build.py'),*series,'--print']))
    lines=['# Generated from scripts/build.py --print; outputs are repository-relative.','group "default" {','  targets = '+json.dumps(baked['group']['default']['targets']),' }'.lstrip(),'']
    for target,config in baked['target'].items():
        lines+=['target '+json.dumps(target)+' {','  context = "."','  dockerfile = "Dockerfile"','  platforms = '+json.dumps(config['platforms']),'  args = {']
        lines+=['    '+k+' = '+json.dumps(v) for k,v in config['args'].items()]
        lines+=['  }','  output = ["type=local,dest=./builds/build-'+config['args']['PYTHON_VERSION']+'"]','}','']
    (dest/'docker-bake.hcl').write_text('\n'.join(lines))
