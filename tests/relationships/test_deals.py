from copy import deepcopy
import shutil
import pytest
from relationships_py.state import ROOT, read, write, load_master, digest
from relationships_py.deal_rules import verify, explicit_currency
from relationships_py.exporter import export, validate_public
from relationships_py.documents import parse_document
from relationships_py.entities import resolve, resolve_universe


def test_visible_article_date_wins_over_related_story_metadata():
    raw=b'<html><meta property="article:published_time" content="2026-09-23"><main><p>February 27, 2026</p><h1>Real article</h1><p>This article has sufficient body content for extraction and must keep its own publication date, not that of a related story.</p><aside><time datetime="2026-09-23">New story</time></aside></main></html>'
    assert parse_document(raw)['published_date']=='2026-02-27'


def test_amazon_news_embedded_article_body_is_extracted_without_related_cards():
    raw=b'<html><head><meta property="article:published_time" content="2026-06-04T08:00:00Z"></head><body><main><h3>Summary card</h3><div class="contentItem-role-text">The main article names AWS and a customer, and states that this strategic infrastructure agreement will provide capacity for the customers business over several years.</div><div class="contentItem-role-text">The body provides additional concrete contract terms, the expected timeline, product details and the commitments made by both named companies.</div><li>Unrelated sidebar card</li></main></body></html>'
    parsed=parse_document(raw)
    assert parsed['published_date']=='2026-06-04'
    assert [b['locator'] for b in parsed['blocks']]==['p:0','p:1']
    assert 'Unrelated sidebar card' not in ' '.join(b['text'] for b in parsed['blocks'])


def test_missing_legal_name_does_not_block_reported_company_name():
    c=dict(company_id='co-sample',entity_status='resolved',legal_name=None,display_name='Sample Company',aliases=[])
    assert resolve('Sample Company supplies products.',[c])==[c]


def test_source_bound_deal_rules_are_idempotent_with_cached_sources(project):
    # Integration check only when source cache is available. CI tests below are offline.
    cache=ROOT/'.cache/relationships/documents'
    cfg=read(project/'relationships_config/deal_rules.json')
    ids={r['proof']['source_id'] for r in cfg['rules']}
    for rule in cfg['rules']:
        for claim in rule['claims']:
            ids.update(item['source_id'] for item in claim.get('context', []))
    for c in cfg['companies']:
        ids.add(c['identity_proof']['source_id'])
        if c.get('listing_proof'):ids.add(c['listing_proof']['source_id'])
    for receipt in read(project/'relationships_config/identity_enrichments.json', {}).values():
        ids.update(proof['source_id'] for proof in receipt['proofs'])
    if any(not (cache/f'{sid}.html').exists() for sid in ids):pytest.skip('Live source cache is intentionally not committed')
    target=project/'.cache/relationships/documents';target.mkdir(parents=True)
    for sid in ids:shutil.copy2(cache/f'{sid}.html',target/f'{sid}.html')
    before=load_master(project);verify(project);assert load_master(project)==before
    config=deepcopy(cfg);config['rules'][0]['claims'][0]['amounts'][0]['amount']['min_value']='99999999999'
    write(project/'relationships_config/deal_rules.json',config)
    with pytest.raises(ValueError,match='assertions changed'):verify(project)
    assert load_master(project)==before
    write(project/'relationships_config/deal_rules.json',cfg)
    first=next(iter(ids));(target/f'{first}.html').write_bytes(b'Changed source')
    with pytest.raises(ValueError,match='Source changed'):verify(project)
    assert load_master(project)==before


def test_timeline_only_contains_approved_amounts_and_preserves_meaning(project):
    pointer=export(project);folder=project/'output_json/relationships/versions'/pointer['build_id']
    events=read(folder/'recent_events.json')['timeline']
    assert len(events)==len({e['event_id'] for e in events})
    assert all(a['verification'].startswith('approved') for e in events for a in e['amounts'])
    aws=next(e for e in events if 'AWSとOpenAIの既存クラウド契約を8年間で' in e['description'] and e['announced_date']=='2026-02-27')
    assert aws['announced_date']=='2026-02-27' and aws['amounts'][0]['value']=='100000000000'
    assert aws['amounts'][0]['value_semantics']=='increment' and aws['term']['duration_value']==8
    assert not any(a.get('value')=='138000000000' for e in events for a in e['amounts'])
    broadcom=next(e for e in events if e['description'].startswith('Apple製品の複数世代に向けBroadcom'))
    assert broadcom['amounts'][0]['qualifier']=='more_than' and broadcom['amounts'][0]['value'] is None
    assert validate_public(project)['valid']
    companies=read(folder/'companies.json')['companies']
    assert next(c for c in companies if c['company_id']=='co-aapl')['listings'][0]['symbol']=='AAPL'


def test_unknown_and_conditional_amounts_remain_unrated():
    from relationships_py.tiers import tier
    config=read(ROOT/'relationships_config/settings.json')['tiers']
    amounts=[a for e in load_master()['events'] for a in e['amounts'] if a['verification']=='approved_rule']
    for a in amounts:
        if a['currency'] is None or a['contingent'] is not False or a['qualifier']=='more_than':assert tier(a,config) is None

def test_dollar_symbol_alone_does_not_prove_us_currency():
    for basis in ('$', '$4 billion', '20 billion dollars', 'ドル',None):assert not explicit_currency('USD',basis)
    for basis in ('USD 30.0 billion','US$ 4 billion','U.S. dollars','United States dollars','40億米ドル'):assert explicit_currency('USD',basis)


def test_sec_resolution_keeps_structured_universe_memberships(project,monkeypatch):
    import json
    cfg=read(project/'relationships_config/universe.json');cfg['pilot']['securities']=cfg['pilot']['securities'][:1];write(project/'relationships_config/universe.json',cfg)
    class Client:
        def get(self,url):return json.dumps(dict(cik=320193,name='Apple Inc.',tickers=['AAPL'],exchanges=['Nasdaq'])).encode(),url,'application/json'
    monkeypatch.setattr('relationships_py.config.user_agent',lambda:'test contact')
    monkeypatch.setattr('relationships_py.http.Client',lambda *a,**k:Client())
    previous=next(c for c in load_master(project)['companies'] if c['company_id']=='co-aapl')['universe_memberships']
    assert resolve_universe(project,'pilot')[0]['status']=='resolved'
    company=next(c for c in load_master(project)['companies'] if c['company_id']=='co-aapl')
    assert company['universe_memberships']==[m for m in previous if m['universe']!='pilot']+[dict(universe='pilot',as_of=cfg['pilot']['as_of'],source_url=cfg['pilot']['source_url'])]
    receipt=read(project/'relationships_data/state/sec_identities.json')['co-aapl']
    assert receipt['company']==company and receipt['url'].endswith('CIK0000320193.json')
