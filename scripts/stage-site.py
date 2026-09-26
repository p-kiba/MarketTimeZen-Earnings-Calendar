"""Assemble one complete Pages artifact from an explicit allowlist. No deploy."""
import shutil
import importlib.util
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from relationships_py.state import ROOT,read
from relationships_py.exporter import validate_public

def stage(root=ROOT):
    root=Path(root);validate_public(root)
    spec=importlib.util.spec_from_file_location('version_map_assets',root/'scripts/version-map-assets.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.version(root)
    out=root/'.site-build'
    if out.is_symlink():raise ValueError('Unsafe artifact directory')
    if out.exists():shutil.rmtree(out)
    out.mkdir()
    for name in ('index.html','japan.html','map.html','earnings_data.json','earnings_data_jp.json','earnings_history_jp.json','assets','output_json/earnings'):
        src=root/name
        if not src.exists():raise ValueError('Missing site asset: '+name)
        if src.is_dir():
            if any(p.is_symlink() for p in src.rglob('*')):raise ValueError('Symbolic link in public assets')
            shutil.copytree(src,out/name)
        else:
            if src.is_symlink():raise ValueError('Symbolic link in public file')
            shutil.copy2(src,out/name)
    base=root/'output_json/relationships';dest=out/'output_json/relationships';dest.mkdir(parents=True)
    pointer=read(base/'latest.json');p=pointer
    # Publish current + validated immediate predecessor; older archives remain in git.
    for p in [pointer,pointer.get('previous')]:
        if not p:continue
        validate_public(root,p)
        source=base/'versions'/p['build_id']
        shutil.copytree(source,dest/'versions'/p['build_id'])
    shutil.copy2(base/'latest.json',dest/'latest.json')
    for name in ('CNAME','favicon.ico','robots.txt'):
        if (root/name).is_file():shutil.copy2(root/name,out/name)
    (out/'.nojekyll').touch()
    forbidden=('relationships_data','relationships_config','tests','.cache','.git','.github','schemas')
    if any((out/name).exists() for name in forbidden):raise ValueError('Private processing files in public artifact')
    return out

if __name__=='__main__':print(stage())
