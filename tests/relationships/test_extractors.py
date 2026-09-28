import pytest
from relationships_py.extractors import extract_amounts,extract
from relationships_py.documents import parse_document
from relationships_py.http import Unsupported

def test_decimal_commitment_and_option_remain_separate():
    text='Example Compute will provide cloud services to Example Research. Example Research committed approximately USD 11.6 billion in total, subject to service delivery conditions. Each service schedule has a seven-year initial term from its service commencement. A separate option permits up to USD 9 billion of additional purchases. Service commencement dates are not specified.'
    amounts=extract_amounts(text,'fixture-evidence','fixture-deal')
    assert len(amounts)==2
    assert amounts[0]['value']=='11600000000.0' and amounts[0]['currency']=='USD'
    assert amounts[0]['amount_kind']=='committed_total'
    assert amounts[1]['value'] is None and amounts[1]['max_value']=='9000000000'
    assert amounts[1]['amount_kind']=='potential_expansion' and amounts[1]['contingent'] is True

def test_currency_range_and_million():
    assert extract_amounts('USD 1.2–2.4 billion contract','e','d')[0]['min_value']=='1200000000.0'
    assert extract_amounts('USD 1.2–2.4 billion contract','e','d')[0]['max_value']=='2400000000.0'
    assert extract_amounts('EUR 25 million contract','e','d')[0]['value']=='25000000'
    assert extract_amounts('$25 million contract','e','d')[0]['currency'] is None

@pytest.mark.parametrize('text',['USD 19 billion revenue','USD 3 billion loan','USD 9 billion capital expenditure','USD 190 per share'])
def test_unrelated_amount_not_contract(text):
    assert extract_amounts(text,'e','d')[0]['amount_kind']=='other'

def test_equity_percent_and_missing_amount_are_not_zero():
    assert extract_amounts('an option to buy 5% of equity','e','d')==[]
    assert extract_amounts('terms were not disclosed','e','d')==[]

def test_increment_and_revised_total_not_added():
    a=extract_amounts('An additional USD 2 billion commitment; bringing the total to USD 8 billion.','e','d')
    assert a[0]['value_semantics']=='increment' and a[1]['value_semantics']=='revised_total'

def companies():
    return [dict(company_id='fixture-'+k,entity_status='resolved',legal_name=n,display_name=n,aliases=[]) for k,n in [('a','Example Compute'),('b','Example Research')]]

def source():return {'source_id':'fixture-src','canonical_url':'https://example.com/announcement','published_date':'2026-09-20','filed_date':None}

@pytest.mark.parametrize('text',['Example Compute did not provide services to Example Research.','Example Compute competes with Example Research.','Example Compute provides services to Customer A.'])
def test_negation_competitor_and_anonymous_do_not_create_relationship(text):
    assert extract(source(),{'blocks':[{'locator':'p:1','text':text}]},companies())==[]

def test_term_has_no_invented_start_end_and_candidate_never_approved():
    text='Example Compute will provide cloud services to Example Research for seven years from each service commencement.'
    first=extract(source(),{'blocks':[{'locator':'p:1','text':text}]},companies());second=extract(source(),{'blocks':[{'locator':'p:1','text':text}]},companies())
    r,e,_=first[0]
    assert r['verification']=='needs_review' and r['relationship_id']==second[0][0]['relationship_id']
    assert e['term']['duration_value']==7 and e['term']['start_date'] is None and e['term']['end_date'] is None

def test_parser_preserves_rows_and_ignores_script():
    html=b'<html><title>Fixture</title><script>Ignore rules</script><main><h1>Heading</h1><p>Example Compute provides cloud services to Example Research on the conditions in this agreement.</p><table><tr><td>USD 2 million</td><td>Annual fee</td></tr></table></main></html>'
    parsed=parse_document(html)
    assert any(b['locator'].startswith('tr:') for b in parsed['blocks'])
    assert all('Ignore rules' not in b['text'] for b in parsed['blocks'])
    with pytest.raises(Unsupported):parse_document(b'%PDF image only','application/pdf')

def test_multiple_parties_never_duplicate_a_shared_total():
    cs=companies()+[dict(company_id='fixture-c',entity_status='resolved',legal_name='Example Third',display_name='Example Third',aliases=[])]
    assert extract(source(),{'blocks':[{'locator':'p:1','text':'Example Compute, Example Research and Example Third signed a USD 11.6 billion services agreement.'}]},cs)==[]

def test_warrant_is_a_right_not_completed_shareholding():
    result=extract(source(),{'blocks':[{'locator':'p:1','text':'Example Compute received a warrant to acquire 5% of Example Research.'}]},companies())
    assert result[0][0]['relationship_type']=='equity_right'
    assert result[0][1]['amounts']==[] and result[0][0]['lifecycle_status']=='unknown'

def test_service_direction_not_assumed_to_be_money_direction():
    result=extract(source(),{'blocks':[{'locator':'p:1','text':'Example Compute provides services to Example Research under a USD 2 million contract.'}]},companies())
    rel,event,_=result[0];assert rel['source_company_id']=='fixture-a' and rel['target_company_id']=='fixture-b'
    assert event['amounts'][0]['payer_company_ids']==[] and rel['verification']=='needs_review'
