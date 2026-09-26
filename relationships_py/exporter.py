"""Content-addressed static releases; pointer changes only after full validation."""
from copy import deepcopy
from pathlib import Path
import shutil
import re
from .state import ROOT, read, write, digest, now, load_master
from .config import settings, universe
from .validation import validate_master, ID
from .tiers import APPROVED, rating

EXPORT_VERSION='1.5.1'

THEME_SIGNALS={
    'ai_models':r'\b(?:AI models?|artificial intelligence|generative AI|LLM|Claude|GPT)\b|生成AI|人工知能',
    'enterprise_ai':r'\b(?:enterprise AI|AI agents?|business software|enterprise software|CRM)\b|企業向けAI',
    'gpu_compute':r'\b(?:GPU|CUDA|compute accelerators?|AI accelerators?)\b|計算アクセラレータ',
    'custom_silicon':r'\b(?:custom silicon|custom chips?|ASICs?)\b|カスタム半導体',
    'memory':r'\b(?:HBM|DRAM|LPDDR|SOCAMM|memory modules?)\b|メモリ',
    'semiconductor_manufacturing':r'\b(?:semiconductor|wafer|foundry|chip fabrication|advanced packaging)\b|半導体|ウエハ|ウェハ',
    'data_center_cloud':r'\b(?:data cent(?:er|re)|cloud infrastructure|cloud services|cloud computing|AI compute infrastructure)\b|データセンター|クラウド基盤',
    'networking':r'\b(?:Ethernet|networking|network infrastructure|switching|wireless connectivity|telecom)\b|ネットワーク|通信',
    'pharma_biotech':r'\b(?:pharmaceutical|pharma|biotech|clinical trial|drug development|therapeutics?)\b|医薬品|バイオ医薬',
    'healthcare':r'\b(?:healthcare|medical device|patient care|hospital)\b|医療|ヘルスケア',
    'food_retail':r'\b(?:grocery|food retail|retail stores?|restaurant|food products?)\b|食品|小売|食料品',
    'financial_services':r'\b(?:payment processing|financial services|banking|credit card|brokerage)\b|決済|金融サービス|銀行',
    'energy_power':r'\b(?:power generation|electricity|renewable energy|nuclear power|grid infrastructure|solar power)\b|発電|電力|再生可能エネルギー|原子力',
    'automotive_batteries':r'\b(?:electric vehicles?|EV batteries|battery cells|automotive)\b|電気自動車|車載電池|自動車',
    'industrial_aerospace':r'\b(?:aerospace|aircraft|defense systems?|industrial equipment|flight control)\b|航空宇宙|防衛|産業機器',
    'consumer_media':r'\b(?:streaming|consumer electronics|smartphones?|digital advertising|media content)\b|ストリーミング|消費者向け電子機器|スマートフォン',
}

def relationship_themes(row):
    business=row.get('business') or {}
    text=' '.join(str(value) for value in (row.get('description',''),business.get('headline',''),business.get('products','')) if value)
    return [theme for theme,pattern in THEME_SIGNALS.items() if re.search(pattern,text,re.I)]

EMPTY_TERM = dict(duration_value=None,duration_unit=None,start_basis=None,start_date=None,end_date=None,renewal=None,evidence_ids=[])

def public_subset(master):
    data=deepcopy(master)
    data['relationships']=[r for r in data['relationships'] if r['verification'] in APPROVED]
    rids={r['relationship_id'] for r in data['relationships']}
    data['events']=[e for e in data['events'] if e['verification'] in APPROVED and set(e['relationship_ids'])<=rids]
    eids={e['event_id'] for e in data['events']}
    for r in data['relationships']:
        r['latest_event_ids']=[i for i in r['latest_event_ids'] if i in eids]
    for e in data['events']:
        e['amounts']=[a for a in e['amounts'] if a['verification'] in APPROVED and e['field_verification'].get('amounts',{}).get('verification') in APPROVED]
        if not e['amounts'] and e['amount_disclosure']=='disclosed':e['amount_disclosure']='ambiguous'
        if e['field_verification'].get('term',{}).get('verification') not in APPROVED:e['term']=deepcopy(EMPTY_TERM)
        if e['field_verification'].get('conditions',{}).get('verification') not in APPROVED:e['conditions']=''
    used=set()
    for r in data['relationships']+data['events']:used.update(r['evidence_ids'])
    for e in data['events']:
        used.update(e['term']['evidence_ids'])
        for a in e['amounts']:used.update(a['evidence_ids'])
        for field in e['field_verification'].values():used.update(field['evidence_ids'])
    data['evidence']=[v for v in data['evidence'] if v['evidence_id'] in used]
    sids={v['source_id'] for v in data['evidence']}
    data['sources']=[v for v in data['sources'] if v['source_id'] in sids]
    # Do not publish unresolved names imported from configuration.
    parties={r[k] for r in data['relationships'] for k in ('source_company_id','target_company_id')}
    data['companies']=[c for c in data['companies'] if c['entity_status']=='resolved' or c['company_id'] in parties]
    return data

def coverage(root, cfg, master, data):
    state=read(Path(root)/'relationships_data/state/processed_documents.json',{})
    docs=state.get('documents',{})
    statuses={s:sum(d.get('status')==s for d in docs.values()) for s in ('discovered','downloaded','parsed','candidate_created','reviewed','published','retryable_error','unsupported')}
    group=universe(root,cfg['universe'])
    inbox=read(Path(root)/'relationships_data/review/statements.json',{})
    return {'statement_review_count':len(inbox.get('statements',[])),'statement_deferred_count':inbox.get('deferred_statements',0),'universe':cfg['universe'],'target_companies':len({s['company_id'] for s in group['securities']}),'indexed_companies':len(data['companies']),'published_relationships':len(data['relationships']),'pending_review':sum(r['verification'] in ('candidate','needs_review') for r in master['relationships']),'documents':statuses,'company_checks':state.get('companies',{}),'last_run':state.get('last_run'),'supported_forms':['8-K','8-K/A','10-K','10-K/A','10-Q','10-Q/A','6-K','6-K/A','20-F','20-F/A'],'backfill_months':cfg['backfill_months'],'limitations':['Selected-company coverage only; absence of a line does not imply absence of a relationship.','Historical source status is not a statement of current status.','Only explicit, complete official announcements are included automatically; other extractions remain pending.','SEC live collection requires SEC_USER_AGENT.']}

def export(root=ROOT, allow_removal=False):
    root=Path(root); cfg=settings(root); master=load_master(root)
    validate_master(master,root)
    data=public_subset(master)
    idx=validate_master(data,root,public=True)
    theme_catalog=read(root/'relationships_config/company_themes.json',{'themes':[],'company_themes':{}})
    theme_names={item['id'] for item in theme_catalog['themes']}
    for company in data['companies']:
        assigned=theme_catalog.get('company_themes',{}).get(company['company_id'],[])
        if any(theme not in theme_names for theme in assigned):raise ValueError('Unknown company theme: '+company['company_id'])
        company['themes']=assigned
    cov=coverage(root,cfg,master,data)
    dest=root/'output_json/relationships'; previous=read(dest/'latest.json',{})
    pending=sum(r['verification'] in ('candidate','needs_review') for r in master['relationships'])
    if pending>cfg['max_candidates_per_run']:raise ValueError('Review queue exceeds configured ceiling; publication held')
    if previous:
        old=read(dest/previous['manifest'])
        old_count=old['relationship_count']
        if old_count and len(data['relationships'])<old_count*(1-cfg['max_removal_fraction']) and not allow_removal:
            raise ValueError('Abnormal relationship removal; keep previous build. Review and use --allow-removal explicitly.')
    build=digest({'export_version':EXPORT_VERSION,'data':data,'coverage':cov,'tiers':cfg['tiers'],'limits':[cfg['initial_nodes'],cfg['expanded_nodes']]})[:24]
    directory=dest/'versions'/build
    if previous.get('build_id')==build:
        validate_public(root); return previous
    files={}
    def put(name,value):
        payload={'schema_version':'1.0','build_id':build,**value};write(directory/name,payload)
        files[name]=digest((directory/name).read_bytes())
    def summary(r):
        events=[idx['events'][i] for i in r['latest_event_ids']]
        events.sort(key=lambda e:(e['announced_date'] or e['filed_date'] or '',e['event_id']),reverse=True)
        amounts=events[0]['amounts'] if events else []
        classification=rating(amounts,cfg['tiers'],events[0]['amount_disclosure'] if events else 'ambiguous')
        return {k:r[k] for k in ('relationship_id','source_company_id','target_company_id','relationship_type','direction','description','lifecycle_status','status_as_of','last_observed_at')} | classification | {'has_amount':bool(amounts),'event_date':(events[0]['announced_date'] or events[0]['filed_date']) if events else None,'amounts':amounts,'business':r.get('business'),'themes':relationship_themes(r)}
    summaries=[summary(r) for r in data['relationships']]
    put('companies.json',{'companies':data['companies'],'themes':theme_catalog['themes']})
    for company in data['companies']:
        cid=company['company_id'];rels=[r for r in summaries if cid in (r['source_company_id'],r['target_company_id'])]
        neighbors={r[k] for r in rels for k in ('source_company_id','target_company_id')}
        peers=neighbors-{cid}
        cross=[r for r in summaries if {r['source_company_id'],r['target_company_id']}<=peers]
        put(f'companies/{cid}.json',{'company':company,'companies':[idx['companies'][i] for i in sorted(neighbors|{cid})],'relationships':rels,'peer_relationships':cross,'total_peer_relationships':len(cross),'total_relationships':len(rels),'total_counterparties':len(peers),'source_dates':sorted({r['status_as_of'] for r in rels if r['status_as_of']})})
    for rel in data['relationships']:
        evs=[e for e in data['events'] if rel['relationship_id'] in e['relationship_ids']]
        evidence_ids=set(rel['evidence_ids'])
        for e in evs:
            evidence_ids.update(e['evidence_ids'])
            for a in e['amounts']:evidence_ids.update(a['evidence_ids'])
            evidence_ids.update(e['term']['evidence_ids'])
            for decision in e['field_verification'].values():evidence_ids.update(decision['evidence_ids'])
        evidence=[idx['evidence'][i] for i in sorted(evidence_ids)]
        sources=[idx['sources'][i] for i in sorted({e['source_id'] for e in evidence})]
        put('relationships/'+rel['relationship_id']+'.json',{'relationship':rel,'summary':summary(rel),'events':evs,'evidence':evidence,'sources':sources})
    # Discovered historical records are kept separate regardless of the ingest date.
    dated=sorted(data['events'],key=lambda e:e['announced_date'] or e['filed_date'] or '',reverse=True)
    def short(e):
        rels=[idx['relationships'][rid] for rid in e['relationship_ids']]
        return {k:e[k] for k in ('event_id','relationship_ids','event_type','announced_date','filed_date','detected_at','amounts','amount_disclosure','term','conditions')} | {
            'company_ids':sorted({r[key] for r in rels for key in ('source_company_id','target_company_id')}),
            'relationship_types':sorted({r['relationship_type'] for r in rels}),
            'statuses':sorted({r['lifecycle_status'] for r in rels}),
            'description':rels[0]['description'] if rels else '',
            'source_count':len({idx['evidence'][eid]['source_id'] for eid in e['evidence_ids']})}

    put('recent_events.json',{'events':[short(e) for e in dated if e['event_type']!='newly_indexed' and (e['announced_date'] or e['filed_date'])][:100],'newly_indexed':[short(e) for e in dated if e['event_type']=='newly_indexed'][:100],'undated':[short(e) for e in dated if not e['announced_date'] and not e['filed_date']][:100],'timeline':[short(e) for e in dated]})
    put('coverage.json',{'coverage':cov})
    manifest={'schema_version':'1.0','build_id':build,'generated_at':now(),'data_as_of':max((s['published_date'] or s['filed_date'] or '' for s in data['sources']),default='') or None,'files':files,'relationship_count':len(summaries),'company_ids':[c['company_id'] for c in data['companies']],'relationship_ids':[r['relationship_id'] for r in data['relationships']],'tiers':cfg['tiers'],'initial_nodes':cfg['initial_nodes'],'expanded_nodes':cfg['expanded_nodes']}
    write(directory/'manifest.json',manifest)
    pointer={'schema_version':'1.0','build_id':build,'manifest':f'versions/{build}/manifest.json','manifest_hash':digest((directory/'manifest.json').read_bytes()),'previous':{k:previous[k] for k in ('build_id','manifest','manifest_hash')} if previous else None}
    validate_public(root,pointer)
    write(dest/'latest.json',pointer)
    # Retain all immutable builds by default; explicit cleanup is an operator task.
    return pointer

def validate_public(root=ROOT,pointer=None):
    base=Path(root)/'output_json/relationships';p=pointer or read(base/'latest.json')
    if not re_path(p['manifest']) or p['manifest']!=f"versions/{p['build_id']}/manifest.json":raise ValueError('Unsafe manifest path')
    directory=base/'versions'/p['build_id']; manifest=read(directory/'manifest.json')
    if digest((directory/'manifest.json').read_bytes())!=p['manifest_hash'] or manifest['build_id']!=p['build_id']:raise ValueError('Manifest hash/build mismatch')
    if manifest.get('schema_version')!='1.0':raise ValueError('Unsupported schema version')
    for key in ('company_ids','relationship_ids'):
        if len(set(manifest[key]))!=len(manifest[key]) or any(not ID.fullmatch(i) for i in manifest[key]):raise ValueError('Invalid manifest IDs')
    required={'companies.json','recent_events.json','coverage.json'}|{f'companies/{i}.json' for i in manifest['company_ids']}|{f'relationships/{i}.json' for i in manifest['relationship_ids']}
    if set(manifest['files'])!=required or manifest['relationship_count']!=len(manifest['relationship_ids']):raise ValueError('Incomplete manifest file list')
    for name,h in manifest['files'].items():
        if not re_path(name):raise ValueError('Unsafe public path')
        path=directory/name
        if digest(path.read_bytes())!=h or read(path).get('build_id')!=p['build_id'] or read(path).get('schema_version')!='1.0':raise ValueError('Corrupt or mixed build')
    companies=read(directory/'companies.json')['companies']; cids={c['company_id'] for c in companies}
    if cids!=set(manifest['company_ids']):raise ValueError('Company index mismatch')
    # Theme tags are an optional presentation extension, not part of the
    # evidence-backed legal-company master schema.
    master={'companies':[{k:v for k,v in company.items() if k!='themes'} for company in companies],'relationships':[],'events':[],'sources':[],'evidence':[]}
    merge={name:{} for name in ('events','sources','evidence')}
    for rid in manifest['relationship_ids']:
        item=read(directory/f'relationships/{rid}.json');master['relationships'].append(item['relationship'])
        for table,key in (('events','event_id'),('sources','source_id'),('evidence','evidence_id')):
            for row in item[table]:
                if row[key] in merge[table] and merge[table][row[key]]!=row:raise ValueError('Conflicting duplicate')
                merge[table][row[key]]=row
    for table in merge:master[table]=list(merge[table].values())
    validate_master(master,root,public=True)
    for cid in cids:
        neighbor=read(directory/f'companies/{cid}.json')
        expected={r['relationship_id'] for r in master['relationships'] if cid in (r['source_company_id'],r['target_company_id'])}
        if {r['relationship_id'] for r in neighbor['relationships']}!=expected or neighbor['total_relationships']!=len(expected):raise ValueError('Incomplete adjacency')
        # Older immutable releases remain readable/rollbackable. New shards include
        # only already-verified edges whose two endpoints are direct neighbors.
        if 'peer_relationships' in neighbor:
            peers={r[k] for r in master['relationships'] if r['relationship_id'] in expected for k in ('source_company_id','target_company_id')}-{cid}
            cross={r['relationship_id'] for r in master['relationships'] if {r['source_company_id'],r['target_company_id']}<=peers}
            actual=[r['relationship_id'] for r in neighbor['peer_relationships']]
            if set(actual)!=cross or len(actual)!=len(cross) or neighbor['total_peer_relationships']!=len(cross):raise ValueError('Incomplete peer adjacency')
            if {c['company_id'] for c in neighbor['companies']}!=peers|{cid}:raise ValueError('Incorrect neighborhood companies')
        if neighbor['company']!=next(c for c in companies if c['company_id']==cid):raise ValueError('Company shard mismatch')
        for edge in neighbor['relationships']+neighbor.get('peer_relationships',[]):
            original=next(r for r in master['relationships'] if r['relationship_id']==edge['relationship_id'])
            if any(edge[k]!=original[k] for k in ('source_company_id','target_company_id','relationship_type','direction','lifecycle_status')):raise ValueError('Adjacency does not match relationship')
            detail=read(directory/f"relationships/{edge['relationship_id']}.json")
            if 'summary' in detail and edge!=detail['summary']:raise ValueError('Conflicting relationship summary')
        if any(r['relationship_id'] not in manifest['relationship_ids'] for r in neighbor['relationships']):raise ValueError('Broken adjacency')
        if any(c['company_id'] not in cids for c in neighbor['companies']):raise ValueError('Broken company')
    return {'valid':True,'build_id':p['build_id'],'files':len(manifest['files'])}

def re_path(path):
    return isinstance(path,str) and path.endswith('.json') and all(ID.fullmatch(part) for part in path[:-5].split('/'))
