import json
from pathlib import Path
from .state import ROOT,read,write,load_master,save_master,now,digest
from .extractors import extract
from .documents import VERSION,parse_document
from .validation import validate_master
from .tiers import APPROVED
from .config import settings

def extract_pending(root=ROOT):
    root=Path(root);master=load_master(root);state=read(root/'relationships_data/state/processed_documents.json');count=0
    overrides=read(root/'relationships_data/overrides.json',{'decisions':{},'merges':{}})
    cleared=overrides.get('cleared_candidates',{})
    existing={r['relationship_id']:r for r in master['relationships']}
    for source in master['sources']:
        sid=source['source_id'];item=state['documents'].get(sid,{})
        if item.get('status')!='downloaded' and item.get('extraction_version')==VERSION:continue
        path=root/'.cache/relationships/documents'/f'{sid}.json'
        raw_path=path.with_suffix('.html')
        if not raw_path.exists() or digest(raw_path.read_bytes())!=source['content_hash']:
            item['status']='retryable_error';item['error']='Pinned raw source missing or changed: re-ingest source';continue
        # Reparse pinned bytes so parser upgrades also recover older downloaded
        # documents whose cached JSON contained only a related-story card.
        parsed=parse_document(raw_path.read_bytes());write(path,parsed)
        candidates=extract(source,parsed,master['companies'],read(root/'relationships_config/aliases.json',{}))
        actionable=[v for v in candidates if v[0]['relationship_id'] not in overrides['decisions'] and v[0]['relationship_id'] not in cleared and not (v[0]['relationship_id'] in existing and existing[v[0]['relationship_id']]['verification'] in APPROVED)]
        if count+len(actionable)>settings(root)['max_candidates_per_run']:continue
        for rel,event,evidence in candidates:
            rid=rel['relationship_id']
            if rid in existing and (existing[rid]['verification'] in APPROVED or rid in overrides['decisions'] or rid in cleared):continue
            for table,key,row in (('relationships','relationship_id',rel),('events','event_id',event),('evidence','evidence_id',evidence)):
                old=next((r for r in master[table] if r[key]==row[key]),None)
                if old and key=='relationship_id':row['first_observed_at']=old['first_observed_at']
                master[table]=[r for r in master[table] if r[key]!=row[key]]+[row]
            count+=1
        item.update(status='candidate_created' if candidates else 'parsed',extraction_version=VERSION)
    validate_master(master,root);save_master(master,root);write(root/'relationships_data/state/processed_documents.json',state)
    pending=refresh_queue(root)
    from .discovery import discover_statements
    discovery=discover_statements(root)
    return {'created_or_updated':count,'pending':len(pending),'discovery':discovery}

def refresh_queue(root=ROOT):
    root=Path(root);master=load_master(root)
    pending=[{'candidate_id':r['relationship_id'],'verification':r['verification'],'evidence_ids':r['evidence_ids']} for r in master['relationships'] if r['verification'] in ('candidate','needs_review')]
    path=root/'relationships_data/review/candidates.jsonl';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in pending))
    return pending

def review_report(root=ROOT):
    master=load_master(root);idx=validate_master(master,root);lines=['# Unverified relationship candidates','', 'Not a public feed. Review each party, direction, date, amount scope, conditions and evidence.','']
    for r in master['relationships']:
        if r['verification'] not in ('candidate','needs_review'):continue
        lines+=['## '+r['relationship_id'],'',f"{r['source_company_id']} → {r['target_company_id']} · {r['relationship_type']}",'','```json',json.dumps(r,ensure_ascii=False,indent=2),'```']
        for event in master['events']:
            if r['relationship_id'] in event['relationship_ids']:lines+=['```json',json.dumps(event,ensure_ascii=False,indent=2),'```']
        for eid in r['evidence_ids']:
            e=idx['evidence'][eid];s=idx['sources'][e['source_id']]
            lines += ['',s['canonical_url'],'',s['content_hash'],'',e['excerpt'],'']
    path=Path(root)/'relationships_data/review/report.md';path.write_text('\n'.join(lines)+'\n');return str(path)

def decide(candidate_id,reviewer,reason,decision,fields=(),root=ROOT):
    if not reviewer.strip() or not reason.strip():raise ValueError('Real reviewer and decision reason required')
    master=load_master(root);idx=validate_master(master,root);rel=idx['relationships'][candidate_id]
    if decision=='approved_manual' and not {'parties','relationship','status'}<=set(fields):raise ValueError('Explicit --fields parties,relationship,status required; add amounts,term,conditions only after review')
    hashes={idx['evidence'][e]['source_id']:idx['sources'][idx['evidence'][e]['source_id']]['content_hash'] for e in rel['evidence_ids']}
    meta={'reviewer':reviewer,'rule_id':None,'rule_version':None,'verified_at':now(),'reason':reason,'evidence_hashes':hashes}
    rel['verification']=decision;rel['verification_metadata']=meta
    for event in master['events']:
        if candidate_id not in event['relationship_ids']:continue
        event['verification']=decision
        eh={idx['evidence'][e]['source_id']:idx['sources'][idx['evidence'][e]['source_id']]['content_hash'] for e in event['evidence_ids']}
        event['verification_metadata']=dict(meta,evidence_hashes={**hashes,**eh})
        for field in event['field_verification']:
            if field in fields:event['field_verification'][field]['verification']=decision
        for a in event['amounts']:
            if 'amounts' in fields:a['verification']=decision
    overrides=read(Path(root)/'relationships_data/overrides.json',{'decisions':{},'merges':{}})
    overrides['decisions'][candidate_id]={'decision':decision,**meta,'fields':list(fields)}
    validate_master(master,root);save_master(master,root);write(Path(root)/'relationships_data/overrides.json',overrides)
    return {'candidate_id':candidate_id,'verification':decision}

def link_duplicate(source_id,target_id,reviewer,reason,root=ROOT):
    """Reviewer-confirmed same event; preserve all sources, never add amounts."""
    if not reviewer or not reason:raise ValueError('Reviewer and same-deal reason required')
    master=load_master(root);idx=validate_master(master,root)
    src=idx['relationships'][source_id];dst=idx['relationships'][target_id]
    if source_id==target_id or any(src[k]!=dst[k] for k in ('source_company_id','target_company_id','relationship_type')):raise ValueError('Different parties/type cannot be linked')
    # This invalidates approval for explicit re-review of the combined evidence.
    dst['evidence_ids']=sorted(set(dst['evidence_ids']+src['evidence_ids']));dst['verification']='needs_review'
    for e in master['events']:
        if target_id in e['relationship_ids']:
            e['evidence_ids']=sorted(set(e['evidence_ids']+src['evidence_ids']));e['verification']='needs_review'
        if source_id in e['relationship_ids']:e['verification']='rejected'
    src['verification']='rejected'
    overrides=read(Path(root)/'relationships_data/overrides.json',{'decisions':{},'merges':{}})
    overrides['decisions'][source_id]={'decision':'rejected','merged_into':target_id,'reviewer':reviewer,'reason':reason,'verified_at':now()}
    validate_master(master,root);save_master(master,root);write(Path(root)/'relationships_data/overrides.json',overrides)
    return {'merged_into':target_id,'verification':'needs_review'}
