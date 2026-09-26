from copy import deepcopy
from relationships_py.state import read, write, load_master, digest
from relationships_py.documents import parse_document
from relationships_py.discovery import statement_candidates, discover_statements, draft_disclosure
from relationships_py.exporter import export, public_subset, validate_public
from relationships_py.validation import validate_master
import pytest


def test_newsroom_cards_never_replace_the_disclosure_body():
    text='NVIDIA and Fixture Supplier announce a platform development agreement with detailed products and terms.'
    for cls,body in [('index-item','<div class="article-body"><p>'+text+'</p></div>'),('card-block','<div class="entry-content"><p>'+text+'</p></div>')]:
        parsed=parse_document(f'<article class="{cls}"><p>Unrelated teaser</p></article>{body}'.encode())
        assert [b['text'] for b in parsed['blocks']]==[text]


def test_unknown_and_multi_party_statements_are_kept_without_inventing_edges():
    companies=[dict(company_id='co-'+n.lower(),display_name=n,legal_name=None,aliases=[],entity_status='resolved') for n in ['Alpha Corp','Beta Corp','Gamma Corp']]
    source=dict(source_id='source-test',canonical_url='https://issuer.test/disclosure',content_hash='abc',publisher='co-alpha')
    parsed={'blocks':[dict(locator='p:0',text='Alpha Corp will partner with Beta Corp, Gamma Corp and Newcomer Industries to develop products for USD 3 billion.') ]}
    rows=statement_candidates(source,parsed,companies)
    assert len(rows)==1 and rows[0]['reason']=='multi_party'
    assert len(rows[0]['mentioned_company_ids'])==3
    assert 'Newcomer Industries' in rows[0]['unresolved_mentions']
    assert rows[0]['relationship_ids']==[] and rows[0]['verification']=='needs_review'
    assert 'text' not in rows[0] and 'amounts' not in rows[0]
    assert rows==statement_candidates(source,parsed,companies)


def test_statement_discovery_and_local_worksheet_do_not_change_public_data(project):
    m=load_master(project);source=m['sources'][0];raw=b'<main><p>Fixture Alpha partners with Fixture Beta to develop advanced systems and products with agreed milestones.</p></main>'
    source['content_hash']=digest(raw)
    # Isolate a source from production approvals in this fixture.
    for key in ['relationships','events','evidence']:m[key]=[]
    m['sources']=[source]
    from relationships_py.state import save_master
    save_master(m,project)
    path=project/'.cache/relationships/documents'/f"{source['source_id']}.html";path.parent.mkdir(parents=True);path.write_bytes(raw)
    before=load_master(project);result=discover_statements(project)
    assert result['statements']==1 and result['published']==0
    draft=draft_disclosure(source['source_id'],project)
    assert '.cache/relationships/review/' in draft['private_worksheet']
    assert load_master(project)==before
    path.write_bytes(b'changed')
    with pytest.raises(ValueError,match='Source changed'):draft_disclosure(source['source_id'],project)


def test_business_context_requires_the_same_relationship_evidence(project):
    m=public_subset(load_master(project));r=next(r for r in m['relationships'] if r.get('business'))
    other=next(e['evidence_id'] for e in m['evidence'] if e['evidence_id'] not in r['evidence_ids'])
    r['business']['evidence_ids']=[other]
    with pytest.raises(ValueError,match='Business context'):validate_master(m,project,public=True)


def test_public_adjacency_counts_real_counterparties_and_preserves_context(project):
    p=export(project);root=project/'output_json/relationships/versions'/p['build_id']
    nvda=read(root/'companies/co-nvda.json');meta=read(root/'companies/co-meta.json')
    assert nvda['total_counterparties']>=20 and meta['total_counterparties']>=7
    assert nvda['total_relationships']>nvda['total_counterparties']
    assert all(r['verification'].startswith('approved') for r in public_subset(load_master(project))['relationships'])
    assert any(r['business'] and 'Blackwell' in r['business']['headline'] for r in nvda['relationships'])
    corning=next(r for r in meta['relationships'] if r['source_company_id']=='co-glw')
    assert corning['amounts'][0]['max_value']=='6000000000' and corning['tier'] is None
    amd=next(r for r in meta['relationships'] if r['source_company_id']=='co-amd')
    assert not amd['amounts'] and '6GW' in amd['business']['scale']
    assert meta['source_dates']==sorted(meta['source_dates'])

def test_every_neighborhood_contains_all_verified_peer_edges_without_new_parties(project):
    p=export(project);root=project/'output_json/relationships/versions'/p['build_id']
    data=public_subset(load_master(project));found=0
    for c in data['companies']:
        cid=c['company_id'];shard=read(root/f'companies/{cid}.json')
        peers={c['company_id'] for c in shard['companies']}-{cid}
        expected={r['relationship_id'] for r in data['relationships'] if {r['source_company_id'],r['target_company_id']}<=peers}
        assert {r['relationship_id'] for r in shard['peer_relationships']}==expected
        assert shard['total_peer_relationships']==len(expected)
        assert not expected.intersection(r['relationship_id'] for r in shard['relationships'])
        found+=len(expected)
        for edge in shard['relationships']+shard['peer_relationships']:
            detail=read(root/f"relationships/{edge['relationship_id']}.json")
            assert detail['summary']==edge
            assert edge['tier'] is not None or edge['tier_reasons']
    assert found>0 and validate_public(project)['valid']


def test_large_cap_membership_is_valid_schema(project):
    m=load_master(project);m['companies'][0]['universe_memberships'].append(dict(universe='large_cap_focus',as_of='2026-09-26',source_url='https://www.sec.gov/'))
    validate_master(m,project)


def test_extraction_rejects_changed_raw_cache(project):
    from relationships_py.review import extract_pending
    m=load_master(project);source=m['sources'][0]
    state=read(project/'relationships_data/state/processed_documents.json')
    state['documents'][source['source_id']]={'status':'downloaded'}
    write(project/'relationships_data/state/processed_documents.json',state)
    path=project/'.cache/relationships/documents'/f"{source['source_id']}.html";path.parent.mkdir(parents=True);path.write_bytes(b'changed')
    before=load_master(project);extract_pending(project)
    assert load_master(project)==before
    assert read(project/'relationships_data/state/processed_documents.json')['documents'][source['source_id']]['status']=='retryable_error'
