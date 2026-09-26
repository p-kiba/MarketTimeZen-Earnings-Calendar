"""Narrow source-bound rules. Never promote arbitrary regex matches or claim human review."""
from pathlib import Path
from bs4 import BeautifulSoup
from .state import ROOT,read,write,digest,stable_id,now,load_master,save_master
from .documents import parse_document
from .validation import validate_master
from .exporter import EMPTY_TERM


def verify(root=ROOT):
    root=Path(root);master=load_master(root);sources={s['source_id']:s for s in master['sources']};companies={c['company_id']:c for c in master['companies']}
    reports=[];overrides=read(root/'relationships_data/overrides.json',{'decisions':{}})
    for rule in read(root/'relationships_config/pilot_rules.json',[]):
        sid=rule['source_id'];source=sources[sid];raw=(root/'.cache/relationships/documents'/f'{sid}.html').read_bytes()
        if source['source_type']=='test_fixture' or source['canonical_url']!=rule['source_url'] or digest(raw)!=rule['content_hash'] or source['content_hash']!=rule['content_hash']:raise ValueError('Pilot source changed; review required')
        if digest(rule['claims'])!=rule['claims_hash']:raise ValueError('Pilot facts changed without evaluation')
        text=BeautifulSoup(raw,'html.parser').get_text(' ',strip=True)
        if rule['visible_date'] not in text:raise ValueError('Publication date not found on source page')
        parsed=parse_document(raw);blocks={b['locator']:b['text'] for b in parsed['blocks']}
        evidence=[]
        for expected in rule['evidence']:
            block=blocks[expected['locator']]
            if digest(block)!=expected['paragraph_hash'] or expected['excerpt'] not in block:raise ValueError('Evidence paragraph changed')
            eid=stable_id('evidence',rule['rule_id'],expected['locator'],expected['excerpt'])
            ev={'evidence_id':eid,'source_id':sid,'section':'Primary announcement','locator':expected['locator'],'excerpt':expected['excerpt'],'normalized_text_hash':digest(expected['excerpt']),'supports_fields':expected['supports_fields']}
            evidence.append(ev)
        source['published_date']=rule['publication_date'];source['date_precision']='day'
        for ev in evidence:
            master['evidence']=[e for e in master['evidence'] if e['evidence_id']!=ev['evidence_id']]+[ev]
        for claim in rule['claims']:
            a,b=claim['source_company_id'],claim['target_company_id'];kind=claim['relationship_type']
            for cid in (a,b):
                if cid not in companies or companies[cid]['entity_status']!='resolved' or companies[cid]['display_name'] not in text:raise ValueError('Unresolved pilot party')
            rid=stable_id('rel',rule['rule_id'],a,b,kind);eid=stable_id('event',rid);deal=stable_id('deal',rid)
            if rid in overrides['decisions']:continue
            previous=next((r for r in master['relationships'] if r['relationship_id']==rid),None)
            # Unchanged input is a no-op, including verification timestamps.
            if previous and previous['verification']=='approved_rule' and previous['verification_metadata']['evidence_hashes'].get(sid)==source['content_hash']:continue
            stamp=now();eids=[e['evidence_id'] for e in evidence]
            meta={'reviewer':None,'rule_id':rule['rule_id'],'rule_version':rule['version'],'verified_at':stamp,'reason':rule['evaluation_note'],'evidence_hashes':{sid:source['content_hash']}}
            relation={'relationship_id':rid,'source_company_id':a,'target_company_id':b,'relationship_type':kind,'direction':'undirected' if kind=='partnership' else 'directed','description':claim['description'],'deal_ids':[deal],'lifecycle_status':claim['lifecycle_status'],'status_as_of':rule['publication_date'],'first_observed_at':previous['first_observed_at'] if previous else stamp,'last_observed_at':stamp,'latest_event_ids':[eid],'evidence_ids':eids,'verification':'approved_rule','verification_metadata':meta}
            amounts=[]
            if claim['amount']:
                info=claim['amount'];block=blocks[info['locator']]
                # Specific closed IBM equity-value claim: reject revenue, price-per-share,
                # currency ambiguity, changed units, and any different deal/issuer.
                if (a,b,kind,info['value'],info['currency'])!=('co-ibm','co-redhat','acquisition','34000000000','USD') or 'total equity value of approximately USD 34 billion' not in block:raise ValueError('Amount does not satisfy evaluated scope/currency rule')
                amounts=[{k:v for k,v in info.items() if k!='locator'}|{'amount_id':stable_id('amount',eid),'min_value':None,'max_value':None,'payer_company_ids':[a],'payee_company_ids':[],'conditions':'','evidence_ids':[e['evidence_id'] for e in evidence if 'amounts' in e['supports_fields']],'verification':'approved_rule'}]
            event={'event_id':eid,'deal_id':deal,'relationship_ids':[rid],'event_type':'newly_indexed','effective_date':rule['publication_date'] if claim['lifecycle_status']=='completed' else None,'agreement_date':None,'announced_at':None,'announced_date':rule['publication_date'],'filed_date':None,'detected_at':stamp,'evidence_ids':eids,'amounts':amounts,'amount_disclosure':'disclosed' if amounts else 'ambiguous' if kind=='investment' else 'not_stated_in_source','term':dict(EMPTY_TERM),'conditions':'','verification':'approved_rule','verification_metadata':meta,'field_verification':{k:{'verification':'approved_rule','evidence_ids':eids} for k in ('parties','relationship','status','amounts','term','conditions')},'supersedes_event_id':None}
            master['relationships']=[r for r in master['relationships'] if r['relationship_id']!=rid]+[relation]
            master['events']=[e for e in master['events'] if e['event_id']!=eid]+[event]
        reports.append({'rule':rule['rule_id'],'source_id':sid,'claims_evaluated':len(rule['claims']),'source_hash':source['content_hash'],'result':'passed','human_reviewed':False})
    validate_master(master,root);save_master(master,root)
    write(root/'relationships_data/state/pilot_evaluation.json',reports)
    return {'source_bound_rules':len(reports),'claims':sum(r['claims_evaluated'] for r in reports)}
