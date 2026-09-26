"""Isolated fictional density fixture. NEVER call the production exporter here."""
import json,shutil,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'.cache/relationships-demo'

def put(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n');return hashlib.sha256(path.read_bytes()).hexdigest()

def build():
    OUT.mkdir(parents=True,exist_ok=True)
    for name in ('assets/relationships','assets/logos'):
        shutil.copytree(ROOT/name,OUT/name,dirs_exist_ok=True)
    html=(ROOT/'map.html').read_text().replace('<body>','<body><div role="note" style="padding:12px;background:#fff1cc;font-weight:700">TEST FIXTURE · 架空の企業・取引を使った表示検証。本番情報ではありません。</div>')
    (OUT/'map.html').write_text(html)
    (OUT/'earnings_data.json').write_text('[]')
    # No real logos or tickers are assigned to fictional companies.
    (OUT/'assets/relationships/logos.json').write_text('{}')
    cs=[dict(company_id=f'fixture-co-{i:03}',display_name=f'Example {i:03}',legal_name=f'Example {i:03} Corporation',listings=[],aliases=[],country=None,listing_status='unknown',listing_status_as_of=None) for i in range(170)]
    cfg=json.loads((ROOT/'relationships_config/settings.json').read_text());colors=cfg['tiers']['USD']['colors']
    pairs={(0,i) for i in range(1,170 if '--stress' in sys.argv else 65)}|{(i,(i*17+j)%169+1) for i in range(1,65) for j in range(1,4)}
    rs=[]
    for n,(a,b) in enumerate(sorted(pairs)):
        if a==b:continue
        rs.append(dict(relationship_id=f'fixture-rel-{n}',source_company_id=cs[a]['company_id'],target_company_id=cs[b]['company_id'],relationship_type=['service_provider','investment','partnership'][n%3],direction='undirected' if n%3==2 else 'directed',description='Fictional layout fixture only.',lifecycle_status='active',status_as_of='2026-09-25',last_observed_at='2026-09-25T00:00:00Z',event_date='2026-09-25',has_amount=n%6!=5,tier={'color':colors[n%5],'level':n%5+1} if n%6!=5 else None))
    build='fixture-stress-v1' if '--stress' in sys.argv else 'fixture-dense-v1';base=OUT/'output_json/relationships';dest=base/'versions'/build;files={}
    def emit(name,value):files[name]=put(dest/name,dict(schema_version='1.0',build_id=build,fixture_only=True,**value))
    emit('companies.json',{'companies':cs});emit('recent_events.json',dict(events=[],newly_indexed=[],undated=[]));emit('coverage.json',{'coverage':dict(universe='TEST FIXTURE',indexed_companies=len(cs),published_relationships=len(rs),target_companies=len(cs),pending_review=0,last_run=None,limitations=['Fictional companies and relationships for density testing only.'])})
    for c in cs:
        rows=[r for r in rs if c['company_id'] in (r['source_company_id'],r['target_company_id'])];ids={c['company_id']}|{r[k] for r in rows for k in ('source_company_id','target_company_id')}
        emit('companies/'+c['company_id']+'.json',{'company':c,'companies':[x for x in cs if x['company_id'] in ids],'relationships':rows,'total_relationships':len(rows)})
    for r in rs:
        rel=dict(r,verification='approved_rule',verification_metadata={'verified_at':'TEST FIXTURE'})
        emit('relationships/'+r['relationship_id']+'.json',dict(relationship=rel,events=[],evidence=[],sources=[]))
    manifest=dict(schema_version='1.0',build_id=build,fixture_only=True,data_as_of='2026-09-25',files=files,company_ids=[c['company_id'] for c in cs],relationship_ids=[r['relationship_id'] for r in rs],tiers=cfg['tiers'],initial_nodes=30,expanded_nodes=150)
    h=put(dest/'manifest.json',manifest);put(base/'latest.json',dict(schema_version='1.0',build_id=build,manifest=f'versions/{build}/manifest.json',manifest_hash=h,previous=None))
    print('http://127.0.0.1:8000/.cache/relationships-demo/map.html?company=fixture-co-000&lang=ja')

if __name__=='__main__':build()
