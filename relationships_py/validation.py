import re
from decimal import Decimal, InvalidOperation
from urllib.parse import urlsplit
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from .state import ROOT, read, digest
from .tiers import APPROVED

ID = re.compile(r'^[a-zA-Z0-9_-]{1,100}$')

def safe_url(url, hosts=None):
    p = urlsplit(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or p.port not in (None,443):
        raise ValueError('Only ordinary HTTPS links allowed')
    host=p.hostname.lower()
    if host == 'localhost' or '.' not in host or host.endswith(('.local','.internal')) or re.fullmatch(r'[\d.:]+',host):
        raise ValueError('Non-public host')
    if hosts is not None and host not in hosts:
        raise ValueError('Host is not configured as an official source')
    return url

def validate_master(master, root=ROOT, public=False):
    schema=read(Path(ROOT)/'schemas/relationships/master.schema.json')
    Draft202012Validator(schema,format_checker=FormatChecker()).validate({'schema_version':'1.0',**master})
    keys={'companies':'company_id','sources':'source_id','evidence':'evidence_id','relationships':'relationship_id','events':'event_id'}
    indexes={}
    for table,key in keys.items():
        rows=master[table]
        indexes[table]={v[key]:v for v in rows}
        if public and any(v[key].startswith(('fixture-', 'test-')) for v in rows):raise ValueError('Fixture ID cannot be published')
        if len(indexes[table]) != len(rows) or any(not ID.fullmatch(v[key]) for v in rows):
            raise ValueError('Duplicate or unsafe ID')
    def refs(values,table):
        if any(v not in indexes[table] for v in values):raise ValueError(f'Unresolved {table} reference')
    for source in master['sources']:
        if public and source['source_type']=='test_fixture':raise ValueError('Fixture cannot be published')
        safe_url(source['canonical_url'])
        if public and urlsplit(source['canonical_url']).hostname in ('example.com','example.org','example.net'):raise ValueError('Example source cannot be published')
    for ev in master['evidence']:
        refs([ev['source_id']],'sources')
        if not ev['excerpt'].strip() or digest(ev['excerpt'])!=ev['normalized_text_hash']:raise ValueError('Evidence excerpt/hash mismatch')
        if len(ev['excerpt'].split())>25:raise ValueError('Public excerpts must remain short (25 words maximum)')
    if public:
        for sid in indexes['sources']:
            excerpts={e['excerpt'] for e in master['evidence'] if e['source_id']==sid}
            if sum(len(x.split()) for x in excerpts)>25:raise ValueError('Combined source excerpts exceed 25 words')
    for rel in master['relationships']:
        refs([rel['source_company_id'],rel['target_company_id']],'companies')
        refs(rel['latest_event_ids'],'events')
        if public and (not rel['latest_event_ids'] or any(rel['relationship_id'] not in indexes['events'][eid]['relationship_ids'] for eid in rel['latest_event_ids'])):raise ValueError('Approved relationship requires its verified latest event')
        if public and any(indexes['companies'][c]['entity_status']!='resolved' for c in (rel['source_company_id'],rel['target_company_id'])):raise ValueError('Unresolved party')
        if rel.get('business'):
            refs(rel['business']['evidence_ids'],'evidence')
            if not set(rel['business']['evidence_ids']) <= set(rel['evidence_ids']):raise ValueError('Business context requires relationship evidence')
    for row in master['relationships']+master['events']:
        refs(row['evidence_ids'],'evidence')
        if not row['evidence_ids']:raise ValueError('Missing evidence')
        if public:
            if row['verification'] not in APPROVED:raise ValueError('Unapproved record')
            meta=row['verification_metadata']
            if not meta or not meta['reason'] or not (meta['reviewer'] if row['verification']=='approved_manual' else meta['rule_id'] and meta['rule_version']):raise ValueError('Approval provenance required')
            for eid in row['evidence_ids']:
                src=indexes['sources'][indexes['evidence'][eid]['source_id']]
                if meta['evidence_hashes'].get(src['source_id'])!=src['content_hash']:raise ValueError('Source changed; approval is stale')
    for event in master['events']:
        refs(event['relationship_ids'],'relationships')
        refs(event['term']['evidence_ids'],'evidence')
        if event['supersedes_event_id']:refs([event['supersedes_event_id']],'events')
        for field,decision in event['field_verification'].items():
            refs(decision['evidence_ids'],'evidence')
        if public:
            for field in ('parties','relationship','status'):
                decision=event['field_verification'].get(field,{})
                if decision.get('verification') not in APPROVED or not decision.get('evidence_ids'):raise ValueError('Unverified event field: '+field)
            if any(event['term'].get(k) is not None for k in ('duration_value','start_date','end_date')) and event['field_verification'].get('term',{}).get('verification') not in APPROVED:raise ValueError('Unverified term')
            if event['conditions'] and event['field_verification'].get('conditions',{}).get('verification') not in APPROVED:raise ValueError('Unverified conditions')
        if public:
            ids=set(event['evidence_ids'])|set(event['term']['evidence_ids'])
            for a in event['amounts']:ids.update(a['evidence_ids'])
            for d in event['field_verification'].values():ids.update(d['evidence_ids'])
            for eid in ids:
                src=indexes['sources'][indexes['evidence'][eid]['source_id']]
                if event['verification_metadata']['evidence_hashes'].get(src['source_id'])!=src['content_hash']:raise ValueError('Unverified field evidence hash')
        for amount in event['amounts']:
            refs(amount['evidence_ids'],'evidence')
            refs(amount['payer_company_ids']+amount['payee_company_ids'],'companies')
            if public and (amount['verification'] not in APPROVED or not amount['evidence_ids'] or event['field_verification'].get('amounts',{}).get('verification') not in APPROVED):raise ValueError('Unverified amount')
            if amount['currency'] and not amount['currency_basis']:raise ValueError('Currency basis required')
            for field in ('value','min_value','max_value'):
                val=amount[field]
                if val is not None:
                    if not re.fullmatch(r'\d+(?:\.\d+)?',val) or not Decimal(val).is_finite():raise ValueError('Amounts must be nonnegative decimal strings')
            if amount['min_value'] is not None and amount['max_value'] is not None and Decimal(amount['min_value'])>Decimal(amount['max_value']):raise ValueError('Invalid amount range')
    return indexes
