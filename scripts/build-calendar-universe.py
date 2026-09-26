"""Read literal symbol config without importing a network-active generator."""
import ast,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
tree=ast.parse((root/'generate_html.py').read_text())
node=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='TARGET_MONTHLY' for t in n.targets))
(root/'assets/relationships/calendar-universe.json').write_text(json.dumps(list(dict.fromkeys(ast.literal_eval(node.value))))+'\n')

logos={p.stem:'assets/logos/us/'+p.name for p in sorted((root/'assets/logos/us').glob('*.png'))}
mappings=root/'relationships_config/logo_symbols.json'
if mappings.exists():
    for cid,entry in json.loads(mappings.read_text()).items():
        if entry['symbol'] in logos:logos[cid]=logos[entry['symbol']]
(root/'assets/relationships/logos.json').write_text(json.dumps(logos,indent=2)+'\n')
