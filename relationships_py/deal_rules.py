"""Reproducible, source-bound curation of deal disclosures, never general approval.

Rules pin raw bytes and evidence blocks. A changed disclosure or edited assertion
requires a new evaluation. No amount is inferred from a capacity, valuation or
issuer-wide spending plan. Unknown currencies and conditional amounts stay unrated.
"""
from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import re
from bs4 import BeautifulSoup
from .state import ROOT, read, write, digest, stable_id, now, load_master, save_master
from .documents import parse_document
from .validation import validate_master
from .exporter import EMPTY_TERM

def explicit_currency(currency, basis):
    if not basis:return False
    if currency=='USD':
        return bool(re.search(r'\bUSD\b|\bUS\$|\bU\.S\.\s*(?:dollars|\$)|\bUnited States dollars\b|米ドル|美元',basis,re.I))
    return currency in basis

def verify(root=ROOT):
    root = Path(root)
    master = load_master(root)
    config = read(root/'relationships_config/deal_rules.json', {'companies': [], 'rules': []})
    sources = {s['source_id']: s for s in master['sources']}
    documents = {}
    def document(sid):
        if sid not in documents:
            src = sources[sid]
            raw = (root/'.cache/relationships/documents'/f'{sid}.html').read_bytes()
            if src['source_type'] == 'test_fixture' or digest(raw) != src['content_hash']:
                raise ValueError('Source changed or is a fixture; evaluation required')
            blocks = parse_document(raw)['blocks']
            text = '\n'.join(b['text'] for b in blocks) if raw[:4]==b'%PDF' else BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True)
            documents[sid] = (text, {b['locator']: b['text'] for b in blocks})
        return documents[sid]
    def check_proof(proof):
        src = sources[proof['source_id']]
        if src['canonical_url'] != proof['url'] or src['content_hash'] != proof['content_hash']:
            raise ValueError('Source URL/hash differs from evaluated disclosure')
        text, blocks = document(proof['source_id'])
        block = blocks[proof['locator']]
        if digest(block) != proof['block_hash'] or proof['anchor'] not in block:
            raise ValueError('Evidence anchor changed')
        return block
    # Exact primary-source names only. Ticker mappings need their own proof.
    known = {c['company_id']: c for c in master['companies']}
    sec_identities = read(root/'relationships_data/state/sec_identities.json', {})
    for entry in config['companies']:
        company = entry['company']; text = check_proof(entry['identity_proof'])
        if company['display_name'] not in text or company['entity_status'] != 'resolved':
            raise ValueError('Company identity not supported by evaluated text')
        if company['cik'] is not None or company['country'] is not None or company['aliases']:
            raise ValueError('Additional identity fields require separate resolution')
        if company['listings']:
            listing_text = check_proof(entry['listing_proof'])
            for listing in company['listings']:
                if listing['symbol'] not in listing_text or listing['source_url'] != entry['listing_proof']['url']:
                    raise ValueError('Ticker mapping lacks primary proof')
        cid = company['company_id']
        if cid in known and known[cid] != company:
            # Official SEC enrichment can add listing/CIK fields without
            # invalidating a newsroom's already-verified name or relationships.
            receipt=sec_identities.get(cid,{})
            current=known[cid]
            if (receipt.get('company') != current or not current.get('cik') or
                receipt.get('url') != 'https://data.sec.gov/submissions/CIK'+current['cik']+'.json' or
                any(current[k]!=company[k] for k in ('company_id','display_name','aliases','country','entity_status','merged_into'))):
                raise ValueError('Company already exists with different identity; resolve explicitly')
        if cid not in known:
            master['companies'].append(deepcopy(company)); known[cid] = company
    overrides = read(root/'relationships_data/overrides.json', {'decisions': {}})
    reports = []
    for rule in config['rules']:
        assertions = {k: rule[k] for k in ('date', 'claims')}
        if digest(assertions) != rule['assertions_hash']:
            raise ValueError('Deal assertions changed; evaluation required')
        proof = rule['proof']; check_proof(proof)
        sid = proof['source_id']; source = sources[sid]
        text, blocks = document(sid)
        if rule['visible_date'] not in text and source.get('published_date') != rule['date'] and source.get('filed_date') != rule['date']:
            raise ValueError('Publication date absent from source')
        if source['source_type'] not in ('sec_filing','sec_exhibit'):
            source['published_date'] = rule['date']; source['date_precision'] = 'day'
        for claim in rule['claims']:
            block = blocks[claim['locator']]
            if digest(block) != claim['block_hash']:
                raise ValueError('Claim paragraph changed')
            context = []
            for item in claim.get('context', []):
                context.append(check_proof(item))
            party_text = '\n'.join([block] + context)
            for cid, spelling in claim['parties'].items():
                if cid not in known or known[cid]['entity_status'] != 'resolved' or spelling not in party_text:
                    raise ValueError('Claim party missing in its evidence paragraph')
            a, b = claim['source_company_id'], claim['target_company_id']
            if set(claim['parties']) != {a, b} or a == b:
                raise ValueError('Claim party scope mismatch')
            if claim['excerpt'] not in block:
                raise ValueError('Excerpt missing from claim paragraph')
            rid = claim.get('revises_relationship_id') or stable_id('rel', rule['rule_id'], claim['key'])
            if rid in overrides['decisions'] or rid in overrides.get('cleared_candidates',{}):
                continue
            old = next((r for r in master['relationships'] if r['relationship_id'] == rid), None)
            revision=claim.get('revises_relationship_id') is not None
            eid=stable_id('event',rid,rule['rule_id'],rule['assertions_hash']) if revision else stable_id('event',rid)
            if revision:
                if not old or any(old[k]!=claim[k] for k in ('source_company_id','target_company_id','relationship_type','direction')):
                    raise ValueError('Revision must preserve relationship identity')
                if old['verification']=='approved_rule' and old['latest_event_ids']==[eid]:continue
                # An already applied correction may itself have been superseded.
                # Replay its proof, but never replace the current event with history.
                history={e['event_id']:e for e in master['events'] if rid in e['relationship_ids']}
                cursor=old['latest_event_ids'][0];seen=set()
                while cursor in history and cursor not in seen:
                    seen.add(cursor);previous=history[cursor]
                    if cursor==eid:break
                    cursor=previous.get('supersedes_event_id')
                if cursor==eid and previous['verification_metadata']['rule_version']==rule['assertions_hash']:
                    continue
                base=next((e for e in master['events'] if e['event_id']==claim['base_event_id']),None)
                if not base or digest(base)!=claim['base_event_hash'] or old['latest_event_ids']!=[base['event_id']]:
                    raise ValueError('Revision baseline changed; review again')
            if old and old['verification'] == 'approved_rule':
                meta = old['verification_metadata']
                if meta['evidence_hashes'].get(sid) == source['content_hash'] and meta['rule_version'] == rule['assertions_hash']:
                    continue
                # Replaying an unchanged original rule must not roll back a
                # subsequent SEC enrichment. Its original event remains pinned.
                original=next((e for e in master['events'] if e['event_id']==eid),None)
                if not revision and original and original['verification_metadata']['rule_version']==rule['assertions_hash'] and original['verification_metadata']['evidence_hashes'].get(sid)==source['content_hash']:
                    continue
            stamp = now(); deal = old['deal_ids'][0] if revision else stable_id('deal', rid)
            evidence_id = stable_id('evidence', eid) if revision else stable_id('evidence', rid)
            ev = dict(evidence_id=evidence_id, source_id=sid, section=claim['section'], locator=claim['locator'], excerpt=claim['excerpt'], normalized_text_hash=digest(claim['excerpt']), supports_fields=['parties', 'relationship', 'status', 'amounts', 'term', 'conditions'])
            eids = [evidence_id]
            for i, item in enumerate(claim.get('context', [])):
                ceid=stable_id('evidence',eid,'context',i);eids.append(ceid)
                cev=dict(evidence_id=ceid,source_id=item['source_id'],section='Corroborating primary disclosure',locator=item['locator'],excerpt=item['anchor'],normalized_text_hash=digest(item['anchor']),supports_fields=item.get('supports_fields',['parties']))
                master['evidence']=[v for v in master['evidence'] if v['evidence_id']!=ceid]+[cev]
            hashes={sid:source['content_hash'],**{p['source_id']:sources[p['source_id']]['content_hash'] for p in claim.get('context',[])}}
            meta = dict(reviewer=None, rule_id=rule['rule_id'], rule_version=rule['assertions_hash'], verified_at=stamp, reason=rule['evaluation_note'], evidence_hashes=hashes)
            amounts = []
            for i, assertion in enumerate(claim['amounts']):
                amount = deepcopy(assertion['amount'])
                amount_block=block
                if assertion.get('proof'):
                    if assertion['proof'] not in claim.get('context',[]):raise ValueError('Amount proof must be recorded in event evidence')
                    if assertion.get('xbrl'):raise ValueError('Cross-document XBRL amounts require separate evaluation')
                    amount_block=check_proof(assertion['proof'])
                if assertion['anchor'] not in amount_block:
                    raise ValueError('Amount anchor absent from claim paragraph')
                # The evaluated assertion includes the whole meaning, not just a number.
                xbrl=assertion.get('xbrl')
                if xbrl:
                    if source['source_type'] not in ('sec_filing','sec_exhibit'):raise ValueError('XBRL proof requires SEC filing')
                    raw=(root/'.cache/relationships/documents'/f'{sid}.html').read_bytes()
                    soup=BeautifulSoup(raw,'html.parser');fact=soup.find('ix:nonfraction',id=xbrl['fact_id'])
                    unit=soup.find('xbrli:unit',id=fact.get('unitref')) if fact else None
                    measure=unit.find('xbrli:measure') if unit else None
                    parents=[p for p in fact.parents if p.name in ('p','div')] if fact else []
                    if not fact or not measure or measure.get_text(strip=True)!='iso4217:'+amount['currency'] or not any(' '.join(p.stripped_strings)==block for p in parents):raise ValueError('XBRL currency/paragraph proof mismatch')
                    if fact.get('sign')=='-' or fact.get('format','').split(':')[-1] not in ('','num-dot-decimal'):raise ValueError('Unsupported XBRL numeric format')
                    value=Decimal(fact.get_text(strip=True).replace(',',''))*(Decimal(10)**int(fact.get('scale','0')))
                    if value!=Decimal(xbrl['value']) or str(xbrl['value']) not in [amount[k] for k in ('value','min_value','max_value')]:raise ValueError('XBRL value differs from evaluated amount')
                    amount['currency_basis']='SEC inline XBRL '+xbrl['fact_id']+' / '+measure.get_text(strip=True)
                elif amount['currency']:
                    currency_text=amount_block
                    if assertion.get('currency_proof'):
                        cp=assertion['currency_proof']
                        if cp not in claim.get('context',[]):raise ValueError('Currency proof must be recorded in event evidence')
                        currency_text=check_proof(cp)
                    if not explicit_currency(amount['currency'],amount['currency_basis']) or amount['currency_basis'] not in currency_text:
                        raise ValueError('Explicit currency evidence required')
                if amount['qualifier'] in ('up_to', 'at_least', 'more_than', 'range') and amount['value'] is not None:
                    raise ValueError('Bounded amount cannot be an exact total')
                if amount['currency'] is None and amount['currency_basis'] is not None:
                    raise ValueError('Unknown currency must remain unknown')
                if amount.get('original_text') and amount['original_text'] not in assertion['anchor']:
                    raise ValueError('Original amount text differs from evidence')
                amount.update(amount_id=stable_id('amount', eid, i), evidence_ids=eids, verification='approved_rule')
                amounts.append(amount)
            term = deepcopy(claim.get('term', EMPTY_TERM))
            if term != EMPTY_TERM: term['evidence_ids'] = eids
            rel = dict(relationship_id=rid, source_company_id=a, target_company_id=b, relationship_type=claim['relationship_type'], direction=claim['direction'], description=claim['description'], deal_ids=[deal], lifecycle_status=claim['status'], status_as_of=claim.get('status_as_of',rule['date']), first_observed_at=old['first_observed_at'] if old else stamp, last_observed_at=stamp, latest_event_ids=[eid], evidence_ids=eids, verification='approved_rule', verification_metadata=meta)
            if claim.get('business'):
                rel['business'] = dict(deepcopy(claim['business']), evidence_ids=eids)
            event = dict(event_id=eid, deal_id=deal, relationship_ids=[rid], event_type=claim['event_type'], effective_date=None, agreement_date=None, announced_at=None, announced_date=rule['date'], filed_date=None, detected_at=stamp, evidence_ids=eids, amounts=amounts, amount_disclosure='disclosed' if amounts else claim.get('amount_disclosure','not_stated_in_source'), term=term, conditions=claim.get('conditions', ''), verification='approved_rule', verification_metadata=meta, field_verification={k:dict(verification='approved_rule',evidence_ids=eids) for k in ('parties','relationship','status','amounts','term','conditions')}, supersedes_event_id=None)
            if source['source_type'] in ('sec_filing','sec_exhibit'):event.update(announced_date=None,filed_date=source['filed_date'])
            if revision:event['supersedes_event_id']=claim['base_event_id']
            for field in ('effective_date','agreement_date'):
                if claim.get(field):event[field]=claim[field]
            for table, key, row in [('relationships','relationship_id',rel),('events','event_id',event),('evidence','evidence_id',ev)]:
                master[table] = [v for v in master[table] if v[key] != row[key]] + [row]
        reports.append(dict(rule_id=rule['rule_id'], claims=len(rule['claims']), source_id=sid, assertions_hash=rule['assertions_hash'], human_reviewed=False))
    validate_master(master, root)
    # Validate publication policy before persisting any new assertion.
    from .exporter import public_subset
    validate_master(public_subset(master), root, public=True)
    save_master(master, root)
    write(root/'relationships_data/state/deal_evaluation.json', reports)
    return {'evaluated_disclosures':len(reports),'evaluated_claims':sum(r['claims'] for r in reports)}
