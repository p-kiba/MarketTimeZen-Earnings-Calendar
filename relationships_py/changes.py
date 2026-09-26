"""Private triage hints; same parties do not prove the same contract."""
import re
from collections import Counter
from pathlib import Path
from .state import ROOT, write, stable_id, digest
from .tiers import APPROVED

SIGNALS = {
    'termination_wording': r'\b(terminated|expired|termination of)\b',
    'completion_wording': r'\b(completed|consummated|closed the acquisition)\b',
    'amendment_wording': r'\b(amended|amendment|renewed|extended|expanded)\b',
    'termination_clause': r'\b(may terminate|right to terminate)\b',
}

def change_signals(text):
    return [name for name, pattern in SIGNALS.items() if re.search(pattern, text, re.I)]

def write_change_review(master, statements, limit, root=ROOT):
    sources={s['source_id']:s for s in master['sources']}
    evidence={e['evidence_id']:e for e in master['evidence']}
    approved=[r for r in master['relationships'] if r['verification'] in APPROVED]
    items=[]
    for rel in master['relationships']:
        meta=rel.get('verification_metadata') or {}
        changed=[sid for sid,h in meta.get('evidence_hashes',{}).items() if sid not in sources or sources[sid]['content_hash']!=h]
        if changed and rel['verification'] in APPROVED | {'needs_review'}:
            items.append(dict(item_id=stable_id('change',rel['relationship_id'],'source'),kind='source_changed',relationship_id=rel['relationship_id'],source_ids=changed,related_relationship_ids=[rel['relationship_id']],priority=0))
        elif rel['verification'] in ('candidate','needs_review'):
            pair={rel['source_company_id'],rel['target_company_id']}
            matches=[r for r in approved if pair=={r['source_company_id'],r['target_company_id']}]
            same_type=[r['relationship_id'] for r in matches if r['relationship_type']==rel['relationship_type']]
            items.append(dict(item_id=stable_id('change',rel['relationship_id'],'candidate'),kind='possible_duplicate' if same_type else 'related_deal_candidate' if matches else 'new_relationship_candidate',relationship_id=rel['relationship_id'],related_relationship_ids=[r['relationship_id'] for r in matches],same_type_relationship_ids=same_type,evidence_ids=rel['evidence_ids'],source_ids=sorted({evidence[e]['source_id'] for e in rel['evidence_ids']}),priority=3 if matches else 4))
    for statement in statements:
        signals=statement.get('change_signals',[])
        if not signals:continue
        mentioned=set(statement['mentioned_company_ids'])
        matches=[r['relationship_id'] for r in approved if {r['source_company_id'],r['target_company_id']}<=mentioned]
        if not matches:continue
        items.append(dict(item_id=stable_id('change',statement['statement_id'],'wording'),kind='possible_lifecycle_update',statement_id=statement['statement_id'],source_ids=[statement['source_id']],content_hash=statement['content_hash'],locator=statement['locator'],block_hash=statement['block_hash'],signals=signals,related_relationship_ids=matches,priority=1 if 'termination_wording' in signals else 2))
    def order(item):
        dates=[sources[s].get('published_date') or sources[s].get('filed_date') or '' for s in item['source_ids'] if s in sources]
        return (max(dates,default=''),item['item_id'])
    items.sort(key=order,reverse=True)
    items.sort(key=lambda i:i['priority'])
    payload=dict(version='1.0',publication_eligible=False,automatic_decisions=0,warning='Hints only: same parties/type do not prove a duplicate. Wording may describe an option, risk, negation or unrelated agreement. Review scope, dates, parties and the original block before updating.',counts=dict(Counter(i['kind'] for i in items)),items=items[:limit],deferred_items=max(0,len(items)-limit),input_hash=digest({'sources':[(s['source_id'],s['content_hash']) for s in master['sources']], 'relationships':master['relationships']}))
    write(Path(root)/'relationships_data/review/changes.json',payload)
    return dict(items=len(payload['items']),deferred_items=payload['deferred_items'],counts=payload['counts'],automatic_decisions=0)
