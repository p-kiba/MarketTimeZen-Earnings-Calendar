import re

def resolve(text,companies,aliases=None):
    """Only complete verified names; ticker substrings never resolve a party."""
    matches=[]
    for c in companies:
        if c['entity_status']!='resolved':continue
        names=[c['legal_name'],c['display_name']]+[a['name'] for a in c['aliases']]
        names+=(aliases or {}).get(c['company_id'],[])
        for name in names:
            if not name or len(name)<4:continue
            for hit in re.finditer(r'(?<!\w)'+re.escape(name)+r'(?!\w)',text,re.I):matches.append((hit.start(),hit.end(),c))
    # Amazon inside Amazon Web Services (or Nebius inside Nebius, Inc.) is
    # not a second party. Separate, non-overlapping mentions remain eligible.
    found={}
    for start,end,c in matches:
        if any(a<=start and end<=b and (a,b)!=(start,end) and other['company_id']!=c['company_id'] for a,b,other in matches):continue
        found[c['company_id']]=c
    return list(found.values())

def from_sec_submissions(payload,company_id,as_of,source_url):
    """SEC gives identity/listings, not index membership or relationship evidence."""
    cik=str(payload['cik']).zfill(10)
    if not re.fullmatch(r'\d{10}',cik):raise ValueError('Invalid SEC CIK')
    tickers=payload.get('tickers',[]);exchanges=payload.get('exchanges',[])
    if len(tickers)!=len(exchanges):raise ValueError('SEC listing arrays differ')
    return {'company_id':company_id,'legal_name':payload['name'],'display_name':payload['name'],'aliases':[],'cik':cik,'listings':[{'symbol':s,'exchange':e,'valid_from':None,'valid_to':None,'source_url':source_url} for s,e in zip(tickers,exchanges)],'listing_status':'listed' if tickers else 'unknown','listing_status_as_of':as_of,'listing_status_source':source_url,'country':None,'universe_memberships':[],'entity_status':'resolved','merged_into':None}


def resolve_universe(root,mode):
    from datetime import date
    from .config import settings,universe,user_agent
    from .http import Client
    from .sec_client import HOSTS
    from .state import load_master,save_master,read,write,digest,now
    from pathlib import Path
    from .validation import validate_master
    client=Client(HOSTS,settings(root),user_agent(),root)
    master=load_master(root);results=[];seen=set()
    for row in universe(root,mode)['securities']:
        if not row.get('cik') or row['company_id'] in seen:continue
        master=load_master(root)
        seen.add(row['company_id']);url='https://data.sec.gov/submissions/CIK'+row['cik']+'.json'
        try:
            import json
            raw,_,_=client.get(url);payload=json.loads(raw)
            if str(payload['cik']).zfill(10)!=row['cik'] or row['symbol'] not in payload.get('tickers',[]):raise ValueError('Configured CIK and SEC ticker identity mismatch')
            old=next((c for c in master['companies'] if c['company_id']==row['company_id']),None)
            identity=from_sec_submissions(payload,row['company_id'],date.today().isoformat(),url)
            if old:
                identity.update(display_name=old['display_name'],aliases=old['aliases'],country=old['country'],universe_memberships=old['universe_memberships'])
            identity['universe_memberships']=[m for m in identity['universe_memberships'] if m['universe']!=mode]+[{'universe':mode,'as_of':universe(root,mode).get('as_of'),'source_url':universe(root,mode)['source_url']}]
            master['companies']=[c for c in master['companies'] if c['company_id']!=identity['company_id']]+[identity]
            validate_master(master,root);save_master(master,root)
            path=Path(root)/'relationships_data/state/sec_identities.json'
            receipts=read(path,{})
            receipts[identity['company_id']]={'company':identity,'url':url,'source_hash':digest(raw),'verified_at':now()}
            write(path,receipts)
            results.append({'company_id':row['company_id'],'status':'resolved'})
        except Exception as error:results.append({'company_id':row['company_id'],'status':'error','error':str(error)})
    return results
