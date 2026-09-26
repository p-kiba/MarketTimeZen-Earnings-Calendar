"""Conservative paragraph candidates. Publication is a separate decision."""
import re
from decimal import Decimal
from ..state import stable_id, digest, now
from ..entities import resolve
from ..exporter import EMPTY_TERM

MONEY=re.compile(r'(?P<qual>approximately|up to|at least|about)?\s*(?P<cur>USD|US\$|EUR|JPY|\$)\s*(?P<n>\d+(?:\.\d+)?)\s*(?P<unit>billion|million|bn|m)?(?:\s*(?:to|–|-)\s*(?P<n2>\d+(?:\.\d+)?)\s*(?P<unit2>billion|million|bn|m)?)?',re.I)

def extract_amounts(text,eid,scope):
    result=[]
    for i,m in enumerate(MONEY.finditer(text)):
        unit=(m['unit'] or m['unit2'] or '').lower()
        num=Decimal(m['n'])*({'billion':Decimal(10)**9,'bn':Decimal(10)**9,'million':Decimal(10)**6,'m':Decimal(10)**6}.get(unit,1))
        qual={'approximately':'approximately','about':'approximately','up to':'up_to','at least':'at_least'}.get((m['qual'] or '').lower(),'exact')
        if m['n2']:qual='range'
        upper=Decimal(m['n2'])*({'billion':Decimal(10)**9,'bn':Decimal(10)**9,'million':Decimal(10)**6,'m':Decimal(10)**6}.get((m['unit2'] or m['unit'] or '').lower(),1)) if m['n2'] else None
        cur=m['cur'].upper();cur='USD' if cur in ('USD','US$') else None if cur=='$' else cur
        clause=re.split(r';|\.(?=\s|$)',text[:m.start()])[-1]+re.split(r';|\.(?=\s|$)',text[m.start():])[0]
        option=bool(re.search(r'option|optional|potential',clause,re.I))
        annual=bool(re.search(r'annual|per year',clause,re.I))
        increment=bool(re.search(r'additional|incremental',clause,re.I))
        revised=bool(re.search(r'revised|bringing.*total|total.*now',clause,re.I))
        unrelated=bool(re.search(r'revenue|capital expenditure|capex|loan|market cap|valuation|per share',clause,re.I))
        kind='other' if unrelated else 'potential_expansion' if option else 'annual_fee' if annual else 'incremental_commitment' if increment else 'committed_total' if 'commit' in clause.lower() else 'contract_value'
        semantics='unknown' if unrelated else 'contingent' if option else 'periodic' if annual else 'revised_total' if revised else 'increment' if increment else 'original_total'
        result.append({'amount_id':stable_id('amount',scope,i,m.group()),'value':str(num) if qual not in ('up_to','at_least','range') else None,'min_value':str(num) if qual in ('at_least','range') else None,'max_value':str(upper) if upper is not None else str(num) if qual=='up_to' else None,'currency':cur,'currency_basis':m['cur'] if cur else None,'qualifier':qual,'amount_kind':kind,'value_semantics':semantics,'scope':scope,'payer_company_ids':[],'payee_company_ids':[],'contingent':True if option or re.search(r'subject to|conditional',text,re.I) else None,'conditions':'Requires review of the original paragraph','evidence_ids':[eid],'verification':'candidate'})
    return result

def extract(source,parsed,companies,aliases=None):
    from urllib.parse import urlsplit
    if urlsplit(source['canonical_url']).path.lower().endswith(('.rdf','.rss','.xml')):return []
    output=[]
    for block in parsed['blocks']:
        text=block['text'];parties=resolve(text,companies,aliases)
        if len(parties)!=2 or re.search(r'Customer [A-Z]|unnamed|anonymous|did not|does not|not entered|no agreement|competitor|competes with',text,re.I):continue
        kind=None
        for pattern,value in [(r'\b(warrant|equity right)\b','equity_right'),(r'\b(acquire|acquisition|acquired)\b','acquisition'),(r'\b(invest|investment|investing)\b','investment'),(r'\b(partner|partnership|collaboration)\b','partnership'),(r'\b(provide|provides|provider|services)\b','service_provider'),(r'\b(supply|supplier|supplies)\b','supplier')]:
            if re.search(pattern,text,re.I):kind=value;break
        if not kind:continue
        # Ordering is only a candidate suggestion, never approval of direction.
        parties.sort(key=lambda c:text.lower().find(c['display_name'].lower()))
        rid=stable_id('rel',source['source_id'],block['locator'],kind,*[c['company_id'] for c in parties])
        eid=stable_id('evidence',source['source_id'],block['locator'],digest(text))
        excerpt=' '.join(text.split()[:25])
        evidence={'evidence_id':eid,'source_id':source['source_id'],'section':'paragraph','locator':block['locator'],'excerpt':excerpt,'normalized_text_hash':digest(excerpt),'supports_fields':['relationship']}
        stamp=now();deal=stable_id('deal',source['source_id'],block['locator']);event_id=stable_id('event',rid)
        rel={'relationship_id':rid,'source_company_id':parties[0]['company_id'],'target_company_id':parties[1]['company_id'],'relationship_type':kind,'direction':'undirected' if kind=='partnership' else 'directed','description':'Candidate: '+excerpt,'deal_ids':[deal],'lifecycle_status':'unknown','status_as_of':source['published_date'] or source['filed_date'],'first_observed_at':stamp,'last_observed_at':stamp,'latest_event_ids':[event_id],'evidence_ids':[eid],'verification':'needs_review','verification_metadata':None}
        amounts=extract_amounts(text,eid,deal)
        term=dict(EMPTY_TERM)
        duration=re.search(r'(\d+|seven)[ -]year',text,re.I)
        if duration:term.update(duration_value=7 if duration[1].lower()=='seven' else int(duration[1]),duration_unit='year',start_basis='each_service_schedule_commencement' if re.search(r'each.*commencement',text,re.I) else 'unknown',evidence_ids=[eid])
        event={'event_id':event_id,'deal_id':deal,'relationship_ids':[rid],'event_type':'newly_indexed','effective_date':None,'agreement_date':None,'announced_at':None,'announced_date':source['published_date'],'filed_date':source['filed_date'],'detected_at':stamp,'evidence_ids':[eid],'amounts':amounts,'amount_disclosure':'ambiguous' if amounts else 'explicitly_undisclosed' if re.search(r'not disclosed|undisclosed',text,re.I) else 'not_stated_in_source','term':term,'conditions':'','verification':'needs_review','verification_metadata':None,'field_verification':{k:{'verification':'needs_review','evidence_ids':[eid]} for k in ('parties','relationship','status','amounts','term','conditions')},'supersedes_event_id':None}
        output.append((rel,event,evidence))
    return output
