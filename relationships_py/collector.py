import json
from datetime import date,timedelta,datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
from .state import ROOT,read,write,digest,stable_id,now,load_master,save_master
from .config import settings,universe,user_agent,FORMS
from .http import Client,Forbidden,Unsupported
from .documents import parse_document,VERSION
from .sec_client import discover as sec_discover,attachments,archive_url,months_before,HOSTS
from .ir_client import discover as ir_discover,check_robots
from .validation import safe_url,validate_master


def invalidate(master,sid):
    eids={e['evidence_id'] for e in master['evidence'] if e['source_id']==sid}
    for row in master['relationships']+master['events']:
        if eids.intersection(row['evidence_ids']) and row['verification'].startswith('approved'):
            row['verification']='needs_review'
            if 'amounts' in row:
                for a in row['amounts']:a['verification']='needs_review'
                for field in row['field_verification'].values():field['verification']='needs_review'

def ingest(client,url,meta,root=ROOT):
    root=Path(root);state=read(root/'relationships_data/state/processed_documents.json');master=load_master(root)
    sid=stable_id('source',url);old=next((s for s in master['sources'] if s['source_id']==sid),None)
    item=state['documents'].setdefault(sid,{'url':url,'status':'discovered','meta':meta})
    try:
        raw,canonical,typ=client.get(url);h=digest(raw)
        parsed=parse_document(raw,typ)
        if old and old['content_hash']==h and item.get('extraction_version')==VERSION and item.get('status') in ('candidate_created','parsed','reviewed','published'):
            item['last_checked_at']=now();item.pop('recheck',None);write(root/'relationships_data/state/processed_documents.json',state);return sid
        if old and old['content_hash']!=h:invalidate(master,sid)
        source={'source_id':sid,'source_type':meta.get('source_type','official_newsroom'),'canonical_url':canonical,'publisher':meta.get('publisher',urlsplit(url).hostname),'title':parsed['title'],'form':meta.get('form'),'accession_number':meta.get('accession_number'),'filing_cik':meta.get('filing_cik'),'filed_date':meta.get('filed_date'),'published_at':None,'published_date':parsed['published_date'] or meta.get('published_date'),'date_precision':'day' if parsed['published_date'] or meta.get('published_date') or meta.get('filed_date') else 'unknown','retrieved_at':now(),'content_hash':h,'extraction_version':VERSION}
        master['sources']=[s for s in master['sources'] if s['source_id']!=sid]+[source]
        cache=root/'.cache/relationships/documents';cache.mkdir(parents=True,exist_ok=True);(cache/(sid+'.html')).write_bytes(raw);write(cache/(sid+'.json'),parsed)
        item.pop('recheck',None)
        item.update(status='downloaded',content_hash=h,extraction_version=VERSION,last_checked_at=now(),error=None)
        validate_master(master,root);save_master(master,root)
    except Exception as error:
        item.update(status='unsupported' if isinstance(error,Unsupported) else 'retryable_error',error=str(error),last_checked_at=now())
        write(root/'relationships_data/state/processed_documents.json',state);raise
    write(root/'relationships_data/state/processed_documents.json',state)
    return sid

def ingest_url(url,root=ROOT):
    configs=read(Path(root)/'relationships_config/official_sources.json',[])
    config=next((s for s in configs if urlsplit(url).hostname in s['allowed_hosts']),None)
    if not config:raise ValueError('URL host is not an allowlisted official source')
    if not config.get('usage_reviewed_at'):raise ValueError('Source use not reviewed')
    client=Client(config['allowed_hosts'],settings(root),root=root)
    safe_url(url,config['allowed_hosts']);check_robots(client,url)
    return ingest(client,url,{'source_type':'official_newsroom','publisher':config['company_id']},root)

def collect(root=ROOT,mode='incremental',months=None,universe_mode='pilot',sec_only=False):
    if months is not None and not 1<=months<=120:raise ValueError('Backfill months must be 1..120')
    root=Path(root);cfg=settings(root);state_path=root/'relationships_data/state/processed_documents.json'
    state=read(state_path);errors=[];today=date.today();count=0
    try:sec=Client(HOSTS,cfg,user_agent(),root)
    except ValueError as e:sec=None;errors.append(str(e))
    for row in universe(root,universe_mode)['securities']:
        cid=row['company_id']
        if not sec or not row.get('cik'):
            state['companies'][cid]={'status':'configuration_required','checked_at':now()};continue
        prior=state['companies'].get(cid,{}).get('last_success_date')
        since=months_before(today,months or cfg['backfill_months']) if mode=='backfill' else date.fromisoformat(prior)-timedelta(days=cfg['overlap_days']) if prior else today-timedelta(days=cfg['overlap_days'])
        try:
            filings=sec_discover(sec,row['cik'],since.isoformat())
            for f in filings:
                # Ownership forms can have XSL-prefixed primary paths. They are
                # outside this pipeline and must not abort discovery of 8-K/10-Q.
                if f['form'] not in FORMS:continue
                url=archive_url(row['cik'],f['accessionNumber'],f['primaryDocument']);sid=stable_id('source',url)
                meta={'source_type':'sec_filing','publisher':cid,'form':f['form'],'accession_number':f['accessionNumber'],'filing_cik':row['cik'],'filed_date':f['filingDate']}
                state['documents'].setdefault(sid,{'url':url,'status':'discovered','meta':meta})
                if f['form'] not in FORMS:state['documents'][sid]['status']='unsupported';continue
                if state['documents'][sid].get('status') in ('candidate_created','parsed','published','reviewed'):
                    state['documents'][sid]['recheck']=True
            state['companies'][cid]={'status':'discovered','last_success_date':today.isoformat(),'checked_at':now(),'since':since.isoformat(),'supported_filings':sum(f['form'] in FORMS for f in filings),'unsupported_filings':sum(f['form'] not in FORMS for f in filings)}
        except Forbidden as e:
            state['companies'][cid]={'status':'retryable_error','checked_at':now(),'error':str(e),'last_success_date':prior};errors.append(str(e));break
        except Exception as e:state['companies'][cid]={'status':'retryable_error','checked_at':now(),'error':str(e),'last_success_date':prior};errors.append(str(e))
    write(state_path,state)
    # Resume exhibit discovery from durable state, including old backfill filings outside overlap.
    if sec:
        indexes_checked=0
        for sid,item in list(state['documents'].items()):
            meta=item.get('meta',{})
            if indexes_checked>=cfg['max_documents_per_run']:break
            if meta.get('source_type')!='sec_filing' or meta.get('form') not in FORMS or item.get('attachments_discovered'):continue
            indexes_checked+=1
            try:
                filing={'accessionNumber':meta['accession_number']}
                for attachment in attachments(sec,meta['filing_cik'],filing):
                    aid=stable_id('source',attachment['url'])
                    state['documents'].setdefault(aid,{'url':attachment['url'],'status':'discovered','meta':dict(meta,source_type='sec_exhibit',form=attachment['type'])})
                item['attachments_discovered']=True;item.pop('attachments_error',None)
            except Exception as error:
                item['attachments_error']=str(error);errors.append(str(error))
                if isinstance(error,Forbidden):break
        write(state_path,state)
    # A global run cap leaves pending documents in git-backed state.
    attachment_counts={}
    for sid,item in list(state['documents'].items()):
        if count>=cfg['max_documents_per_run']:break
        if item['status'] not in ('discovered','retryable_error') and not item.get('recheck'):continue
        if urlsplit(item['url']).hostname not in HOSTS or not sec:continue
        acc=item['meta'].get('accession_number')
        if item['meta'].get('source_type')=='sec_exhibit':
            if attachment_counts.get(acc,0)>=cfg['max_attachments']:continue
            attachment_counts[acc]=attachment_counts.get(acc,0)+1
        try:ingest(sec,item['url'],item['meta'],root)
        except Forbidden as e:errors.append(str(e));break
        except Exception as e:errors.append(str(e))
        count+=1
    state=read(state_path)
    for config in ([] if sec_only else read(root/'relationships_config/official_sources.json',[])):
        fid=config['company_id'];prev=state['feeds'].get(fid,{})
        if prev.get('checked_at') and (datetime.now(timezone.utc)-datetime.fromisoformat(prev['checked_at'])).total_seconds()<config['crawl_interval']:continue
        try:
            client=Client(config['allowed_hosts'],cfg,root=root)
            links=ir_discover(client,config)
            for url in links:
                sid=stable_id('source',url)
                state['documents'].setdefault(sid,{'url':url,'status':'discovered','meta':{'source_type':'official_newsroom','publisher':fid}})
            state['feeds'][fid]={'checked_at':now(),'status':'discovered','found':len(links)};write(state_path,state)
            for sid,item in list(state['documents'].items()):
                if count>=cfg['max_documents_per_run']:break
                if item['meta'].get('publisher')!=fid or item['status'] not in ('discovered','retryable_error'):continue
                check_robots(client,item['url']);ingest(client,item['url'],item['meta'],root);count+=1
            state=read(state_path)
        except Exception as e:
            state=read(state_path);state['feeds'][fid]={'checked_at':now(),'status':'retryable_error','error':str(e)};errors.append(str(e))
    state['last_run']={'checked_at':now(),'mode':mode,'universe':universe_mode,'sec_only':sec_only,'downloaded_attempts':count,'errors':errors}
    write(state_path,state)
    return state['last_run']


def discover_ir(root=ROOT):
    """Read configured listings only; no bulk document download or approval."""
    root=Path(root);path=root/'relationships_data/state/processed_documents.json';state=read(path);results=[]
    for config in read(root/'relationships_config/official_sources.json',[]):
        try:
            links=ir_discover(Client(config['allowed_hosts'],settings(root),root=root),config)
            result={'company_id':config['company_id'],'status':'discovered','found':len(links),'checked_at':now()}
            for url in links:
                state['documents'].setdefault(stable_id('source',url),{'url':url,'status':'discovered','meta':{'source_type':'official_newsroom','publisher':config['company_id']}})
        except Exception as error:result={'company_id':config['company_id'],'status':'retryable_error','error':str(error),'checked_at':now()}
        state['feeds'][config['company_id']]=result;results.append(result)
    write(path,state);return results
