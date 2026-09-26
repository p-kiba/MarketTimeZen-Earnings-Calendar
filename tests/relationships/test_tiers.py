from relationships_py.tiers import tier, rating
from relationships_py.config import settings

def amount(value,**kw):
    return dict(amount_id='a',value=value,currency='USD',qualifier='exact',contingent=False,verification='approved_manual',value_semantics='original_total',amount_kind='contract_value',**kw)

def test_tier_boundaries():
    cfg=settings()['tiers']
    for value,level in [('99999999.99',1),('100000000',2),('1000000000',3),('10000000000',4),('50000000000',5)]:
        assert tier(amount(value),cfg)['level']==level

def test_unknown_option_annual_and_increment_are_not_rated():
    cfg=settings()['tiers']
    for key,value in [('value',None),('currency',None),('currency','EUR'),('qualifier','up_to'),('contingent',True),('contingent',None),('verification','candidate'),('value_semantics','increment'),('value_semantics','periodic')]:
        a=amount('11600000000');a[key]=value
        assert tier(a,cfg) is None

def test_grey_explanations_distinguish_missing_bounded_and_small_amounts():
    cfg=settings()['tiers']
    assert rating([],cfg)['tier_reasons']==['not_stated_in_source']
    assert rating([],cfg,'explicitly_undisclosed')['tier_reasons']==['explicitly_undisclosed']
    small=rating([amount('1000')],cfg)
    assert small['tier']['level']==1 and small['tier_reasons']==[]
    bounded=amount(None);bounded.update(max_value='6000000000',qualifier='up_to',currency=None,contingent=None)
    result=rating([bounded],cfg)
    assert result['tier'] is None
    assert set(result['tier_reasons'])=={'currency_unknown','bounded_or_unspecified','contingency_unknown'}

def test_multiple_amount_scopes_never_take_the_largest_color():
    a=amount('5000000000');a['value_semantics']='increment'
    b=amount('20000000000');b['contingent']=True
    result=rating([a,b],settings()['tiers'])
    assert result['tier'] is None
    assert set(result['tier_reasons'])=={'multiple_amounts','not_total','conditional'}
