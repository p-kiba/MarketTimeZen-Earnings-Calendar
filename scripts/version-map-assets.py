"""Fingerprint the map's module graph to prevent stale module/CSS mixtures."""
import hashlib
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PATTERN=re.compile(r'(\.(?:js|css))(?:\?v=[^"\'\s&?]+)+')

def version(root=ROOT):
    root=Path(root);assets=root/'assets/relationships'
    files=sorted(list(assets.glob('*.js'))+list(assets.glob('*.css'))+list((assets/'vendor').glob('*.js')))
    canonical={p:PATTERN.sub(r'\1',p.read_text()) for p in files}
    digest=hashlib.sha256(''.join(str(p.relative_to(root))+'\n'+canonical[p] for p in files).encode()).hexdigest()[:12]
    for p,text in canonical.items():
        if p.name!='map.js':continue
        updated=re.sub(r"(from ['\"]\./[^'\"]+\.js)(['\"])",lambda m:m[1]+'?v='+digest+m[2],text)
        if p.read_text()!=updated:p.write_text(updated)
    p=root/'map.html';html=PATTERN.sub(r'\1',p.read_text())
    updated=re.sub(r'(assets/relationships/[^"\s]+\.(?:js|css))',lambda m:m[1]+'?v='+digest,html)
    if p.read_text()!=updated:p.write_text(updated)
    return digest

if __name__=='__main__':print(version())
