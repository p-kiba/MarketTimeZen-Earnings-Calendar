from copy import deepcopy
import json
from pathlib import Path
import pytest
from relationships_py.state import load_master,save_master,read,write,digest,ROOT
from relationships_py.validation import validate_master,safe_url
from relationships_py.exporter import export,validate_public,public_subset
from relationships_py.collector import invalidate
from relationships_py.review import decide,link_duplicate
from relationships_py.config import validate_config,user_agent,universe
from relationships_py.entities import resolve,from_sec_submissions


def test_real_pilot_public_refs_and_idempotence(project):
    first=export(project);before={p.relative_to(project):p.read_bytes() for p in (project/'output_json').rglob('*.json')}
    assert validate_public(project)['valid']
    assert export(project)==first
    assert before=={p.relative_to(project):p.read_bytes() for p in (project/'output_json').rglob('*.json')}

@pytest.mark.parametrize('status',['candidate','needs_review','rejected','withdrawn'])
def test_unapproved_relationship_never_exported(project,status):
    m=load_master(project);r=next(r for r in m['relationships'] if r['verification']=='approved_rule');rid=r['relationship_id'];r['verification']=status
    assert rid not in {r['relationship_id'] for r in public_subset(m)['relationships']}

@pytest.mark.parametrize('mutation',['fixture','fixture_id','example_host','stale_hash','missing_party','missing_evidence','unapproved_amount','float_amount'])
def test_public_gate_rejects_unsafe_records(project,mutation):
    m=public_subset(load_master(project))
    if mutation=='fixture':m['sources'][0]['source_type']='test_fixture'
    elif mutation=='fixture_id':m['companies'][0]['company_id']='fixture-example'
    elif mutation=='example_host':m['sources'][0]['canonical_url']='https://example.com/fixture'
    elif mutation=='stale_hash':m['sources'][0]['content_hash']='changed'
    elif mutation=='missing_party':m['relationships'][0]['target_company_id']='missing'
    elif mutation=='missing_evidence':m['relationships'][0]['evidence_ids']=[]
    else:
        amount=next(e for e in m['events'] if e['amounts'])['amounts'][0]
        if mutation=='unapproved_amount':amount['verification']='candidate'
        else:amount['value']=34e9
    with pytest.raises(Exception):validate_master(m,project,public=True)

def test_verified_relationship_survives_unverified_amount(project):
    m=load_master(project);e=next(e for e in m['events'] if e['verification']=='approved_rule' and e['amounts']);eid=e['event_id'];e['amounts'][0]['verification']='needs_review'
    result=public_subset(m);row=next(e for e in result['events'] if e['event_id']==eid)
    assert row['amounts']==[] and row['amount_disclosure']=='ambiguous'
    validate_master(result,project,public=True)

def test_public_corruption_is_detected(project):
    p=export(project);path=project/'output_json/relationships'/p['manifest'];m=read(path);data=path.parent/'companies.json';data.write_text('{}')
    with pytest.raises(ValueError):validate_public(project)

def test_export_failure_retains_last_pointer(project):
    export(project);path=project/'output_json/relationships/latest.json';before=path.read_bytes();m=load_master(project)
    for r in m['relationships']:r['verification']='withdrawn'
    save_master(m,project)
    with pytest.raises(ValueError,match='Abnormal'):export(project)
    assert path.read_bytes()==before

def test_source_change_invalidates_approval_but_not_lifecycle(project):
    m=load_master(project);r=next(r for r in m['relationships'] if r['verification']=='approved_rule');old=r['lifecycle_status'];eids=set(r['evidence_ids']);sid=next(e for e in m['evidence'] if e['evidence_id'] in eids)['source_id'];invalidate(m,sid)
    assert r['verification']=='needs_review' and r['lifecycle_status']==old

def test_review_requires_identity_and_retains_decision(project):
    m=load_master(project);r=next(r for r in m['relationships'] if r['verification']=='needs_review');rid=r['relationship_id']
    with pytest.raises(ValueError):decide(rid,'','reason','approved_manual',[],project)
    with pytest.raises(ValueError):decide(rid,'reviewer','reason','approved_manual',[],project)
    decide(rid,'fixture-reviewer','Reject ambiguous parties','rejected',[],project)
    assert read(project/'relationships_data/overrides.json')['decisions'][rid]['decision']=='rejected'

def test_sec_identity_preserves_multiple_classes_as_one_company():
    payload={'cik':123,'name':'Fixture Holdings','tickers':['FX.A','FX.B'],'exchanges':['NYSE','NYSE']}
    c=from_sec_submissions(payload,'fixture-co','2026-09-25','https://www.sec.gov/example')
    assert c['company_id']=='fixture-co' and c['cik']=='0000000123' and len(c['listings'])==2
    payload['exchanges']=[]
    with pytest.raises(ValueError):from_sec_submissions(payload,'a','2026-09-25','https://www.sec.gov/example')

def test_short_ticker_or_brand_does_not_resolve():
    company={'company_id':'co-on','entity_status':'resolved','legal_name':'ON Semiconductor Corporation','display_name':'ON Semiconductor','aliases':[]}
    assert not resolve('ON is a word. Apple products here.',[company])
    assert resolve('ON Semiconductor Corporation announced',[company])

@pytest.mark.parametrize('url',['javascript:alert(1)','file:///tmp/a','http://example.org/a','https://127.0.0.1/a','https://localhost/a','https://safe.com@evil.com/a','https://safe.com:444/a'])
def test_unsafe_url_rejected(url):
    with pytest.raises(ValueError):safe_url(url,{'safe.com'})

def test_sp500_requires_provenance_not_security_count(project):
    cfg=read(project/'relationships_config/universe.json');cfg['sp500']={'securities':cfg['pilot']['securities']};write(project/'relationships_config/universe.json',cfg)
    with pytest.raises(ValueError):universe(project,'sp500')
    cfg['sp500'].update(as_of='2026-09-25',source_url='https://example.org/test',license_note='Fixture only');write(project/'relationships_config/universe.json',cfg)
    assert len(universe(project,'sp500')['securities'])==20

def test_large_cap_focus_is_an_explicit_priority_watchlist(project):
    group=universe(project,'large_cap_focus')
    symbols={row['symbol'] for row in group['securities']}
    assert {'META','TSLA','AMD','MU','GOOGL','NVDA'} <= symbols
    assert all(row['cik'] and row['company_id'] for row in group['securities'])
    assert 'not an index' in group['license_note']

def test_sec_contact_missing_and_example_rejected(monkeypatch):
    monkeypatch.delenv('SEC_USER_AGENT',raising=False)
    with pytest.raises(ValueError):user_agent()
    monkeypatch.setenv('SEC_USER_AGENT','Application contact@example.com')
    with pytest.raises(ValueError):user_agent()
