"""Apply an explicitly curated, hash-pinned review batch; never infer approvals."""
from collections import Counter
from pathlib import Path
from .state import ROOT, read, write, digest, now, load_master, save_master
from .documents import parse_document
from .validation import validate_master
from .tiers import APPROVED


def apply_batch(path, root=ROOT):
    root=Path(root); batch=read(path); master=load_master(root)
    idx=validate_master(master,root)
    expected={c['candidate_id']:c['candidate_hash'] for c in batch['candidates']}
    decisions=batch['decisions']
    if len(expected)!=len(batch['candidates']) or len(decisions)!=len(expected) or {d['candidate_id'] for d in decisions}!=set(expected):
        raise ValueError('Every snapshot candidate needs exactly one explicit decision')
    receipt_path=root/'relationships_data/review'/('receipt-'+batch['batch_id']+'.json')
    previous=read(receipt_path,{})
    if previous.get('batch_hash')==digest(batch):return previous
    if previous:raise ValueError('Applied batch is immutable; create a new batch for revisions')
    overrides=read(root/'relationships_data/overrides.json',{'decisions':{},'merges':{}})
    documents={}; stamp=now()
    for d in decisions:
        rid=d['candidate_id']; row=idx['relationships'][rid]
        if digest(row)!=expected[rid] or row['verification'] not in ('candidate','needs_review'):
            raise ValueError('Candidate changed or is already approved; re-review required')
        if d['outcome'] not in ('added','enriched','duplicate','excluded','held') or not d['reason'].strip():
            raise ValueError('Explicit outcome and reason required')
        for linked in d['relationship_ids']:
            if idx['relationships'][linked]['verification'] not in APPROVED:raise ValueError('Replacement must be verified first')
        if d['outcome'] in ('added','enriched','duplicate') and not d['relationship_ids']:raise ValueError('Replacement missing')
        hashes={}
        for p in d['proofs']:
            s=idx['sources'][p['source_id']];sid=s['source_id']
            if s['content_hash']!=p['content_hash'] or s['canonical_url']!=p['url']:raise ValueError('Review source changed')
            if sid not in documents:
                raw=(root/'.cache/relationships/documents'/f'{sid}.html').read_bytes()
                if digest(raw)!=s['content_hash']:raise ValueError('Pinned raw source required')
                documents[sid]={b['locator']:b['text'] for b in parse_document(raw)['blocks']}
            if digest(documents[sid][p['locator']])!=p['block_hash']:raise ValueError('Review paragraph changed')
            hashes[sid]=s['content_hash']
        if not hashes or not {idx['evidence'][e]['source_id'] for e in row['evidence_ids']}<=hashes.keys():raise ValueError('Candidate source not reviewed')
        meta=dict(reviewer=None,rule_id=batch['batch_id'],rule_version=digest(batch),verified_at=stamp,reason=d['reason'],evidence_hashes=hashes)
        if d['outcome']=='held':continue
        row.update(verification='rejected',verification_metadata=meta)
        for event in master['events']:
            if rid not in event['relationship_ids']:continue
            event.update(verification='rejected',verification_metadata=meta)
            for f in event['field_verification'].values():f['verification']='rejected'
            for a in event['amounts']:a['verification']='rejected'
        overrides['decisions'][rid]=dict(decision='rejected',fields=[],**meta,review_outcome=d['outcome'],replaced_by=d['relationship_ids'])
    validate_master(master,root)
    save_master(master,root);write(root/'relationships_data/overrides.json',overrides)
    result=dict(batch_id=batch['batch_id'],batch_hash=digest(batch),applied_at=stamp,human_reviewed=False,counts=dict(Counter(d['outcome'] for d in decisions)))
    write(receipt_path,result)
    from .review import refresh_queue, review_report
    refresh_queue(root);review_report(root)
    return result
