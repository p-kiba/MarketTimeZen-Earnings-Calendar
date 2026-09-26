from copy import deepcopy
import importlib.util
from pathlib import Path
import pytest
from relationships_py.ir_client import discover
from relationships_py.state import read,write,load_master,save_master,ROOT,digest
from relationships_py.exporter import export,validate_public
from relationships_py.review import extract_pending,decide,link_duplicate
from relationships_py.collector import collect,ingest
from relationships_py.http import Unsupported

class Feed:
    def __init__(self,body):self.body=body
    def get(self,url):return (b'User-agent: *\nAllow: /' if url.endswith('robots.txt') else self.body,url,'text/html')

@pytest.mark.parametrize('typ,body',[('rss',b'<rss><channel><item><link>https://ir.test.org/article</link></item></channel></rss>'),('atom',b'<feed xmlns="http://www.w3.org/2005/Atom"><entry><link href="https://ir.test.org/article"/></entry></feed>'),('html',b'<a href="/article">Article</a><a href="https://evil.test/a">External</a>')])
def test_ir_feed_adapters(typ,body):
    cfg=dict(parser_type=typ,listing_url='https://ir.test.org/news',allowed_hosts=['ir.test.org'],link_selector='a',usage_reviewed_at='2026-09-25',usage_note='Test fixture')
    assert discover(Feed(body),cfg)==['https://ir.test.org/article']

def test_missing_sec_and_ir_partial_failure_preserve_master(project,monkeypatch):
    monkeypatch.delenv('SEC_USER_AGENT',raising=False)
    monkeypatch.setattr('relationships_py.collector.ir_discover',lambda *args:(_ for _ in ()).throw(Unsupported('fixture unsupported')))
    old=load_master(project);result=collect(project)
    assert len(result['errors'])==1+len(read(project/'relationships_config/official_sources.json')) and load_master(project)==old
    assert all(c['status']=='configuration_required' for c in read(project/'relationships_data/state/processed_documents.json')['companies'].values())

def test_ingest_retry_and_idempotent_recheck(project):
    class Broken:
        def get(self,url):raise TimeoutError('fixture timeout')
    url='https://ir.test.org/fixture';meta={'publisher':'fixture','source_type':'test_fixture'}
    with pytest.raises(TimeoutError):ingest(Broken(),url,meta,project)
    state=read(project/'relationships_data/state/processed_documents.json');sid=next(iter(state['documents']));assert state['documents'][sid]['status']=='retryable_error'
    body=b'<html><title>Test fixture</title><p>Fixture document content that contains no resolvable relationship at all. Additional text ensures a complete readable document for the parser.</p></html>'
    ingest(Feed(body),url,meta,project);extract_pending(project)
    before=load_master(project);state=read(project/'relationships_data/state/processed_documents.json');state['documents'][sid]['recheck']=True;write(project/'relationships_data/state/processed_documents.json',state)
    ingest(Feed(body),url,meta,project)
    assert load_master(project)==before and not read(project/'relationships_data/state/processed_documents.json')['documents'][sid].get('recheck')

def test_queue_anomaly_holds_previous_publication(project):
    export(project);path=project/'output_json/relationships/latest.json';old=path.read_bytes()
    cfg=read(project/'relationships_config/settings.json');cfg['max_candidates_per_run']=1;write(project/'relationships_config/settings.json',cfg)
    with pytest.raises(ValueError,match='queue'):export(project)
    assert path.read_bytes()==old

def test_duplicate_link_preserves_amount_and_all_evidence(project):
    m=load_master(project);r=next(r for r in m['relationships'] if r['verification']=='approved_rule');dup=deepcopy(r);dup['relationship_id']='duplicate';dup['latest_event_ids']=[];m['relationships'].append(dup);save_master(m,project)
    amounts=deepcopy([e['amounts'] for e in m['events']]);link_duplicate('duplicate',r['relationship_id'],'fixture-reviewer','Same original deal',project)
    m=load_master(project);assert next(r for r in m['relationships'] if r['relationship_id']=='duplicate')['verification']=='rejected'
    assert [e['amounts'] for e in m['events']]==amounts

def test_public_adjacency_mismatch_detected_even_with_valid_hash(project):
    pointer=export(project);base=project/'output_json/relationships';manifest_path=base/pointer['manifest'];manifest=read(manifest_path)
    name='companies/'+manifest['company_ids'][0]+'.json';path=manifest_path.parent/name;doc=read(path);doc['relationships']=[];write(path,doc);manifest['files'][name]=digest(path.read_bytes());write(manifest_path,manifest);pointer['manifest_hash']=digest(manifest_path.read_bytes())
    with pytest.raises(ValueError,match='adjacency'):validate_public(project,pointer)

def test_generated_calendars_keep_independent_map_entry():
    for name in ('index.html','japan.html'):
        text=(ROOT/name).read_text();assert 'mtz-feature-nav' in text and 'goToConnections' in text and 'notifyFavorite(e.symbol)' in text
        assert 'cytoscape' not in text and 'output_json/relationships' not in text
    assert 'initializeSymbolSearch' in (ROOT/'html_template.py').read_text()

def test_staged_site_excludes_candidates_and_contains_both_calendars():
    spec=importlib.util.spec_from_file_location('stage_site',ROOT/'scripts/stage-site.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    out=module.stage();assert all((out/f).is_file() for f in ('index.html','japan.html','map.html','earnings_data.json'))
    assert not (out/'relationships_data').exists() and not (out/'tests').exists() and not (out/'.cache').exists()

def test_new_total_preserves_old_event_without_summing(project):
    m=load_master(project);old=next(e for e in m['events'] if e['verification']=='approved_rule' and e['amounts']);new=deepcopy(old);new['event_id']='revision-event';new['supersedes_event_id']=old['event_id'];new['event_type']='amendment';new['announced_date']='2026-09-25';new['amounts'][0]['value']='40000000000';new['amounts'][0]['value_semantics']='revised_total';new['amounts'][0]['amount_id']='revision-amount';m['events'].append(new)
    rel=next(r for r in m['relationships'] if r['relationship_id'] in new['relationship_ids']);rel['latest_event_ids']=[new['event_id']];save_master(m,project)
    pointer=export(project);directory=project/'output_json/relationships/versions'/pointer['build_id'];detail=read(directory/'relationships'/f"{rel['relationship_id']}.json")
    assert len(detail['events'])==2 and {e['amounts'][0]['value'] for e in detail['events']}=={'34000000000','40000000000'}

def test_manual_rejection_survives_reextraction(project):
    from relationships_py.extractors import extract
    from relationships_py.documents import parse_document
    m=load_master(project);src=deepcopy(m['sources'][0]);companies=[c for c in m['companies'] if c['company_id'] in ('co-ibm','co-redhat')]
    raw=b'<main><p>International Business Machines Corporation acquired Red Hat under the agreement confirmed in this test-only paragraph.</p></main>'
    src.update(source_id='fixture-rejection-source',source_type='test_fixture',content_hash=digest(raw));m['sources'].append(src)
    parsed=parse_document(raw)
    rel,event,evidence=extract(src,parsed,companies)[0]
    m['relationships'].append(rel);m['events'].append(event);m['evidence'].append(evidence);save_master(m,project)
    decide(rel['relationship_id'],'fixture-reviewer','Do not publish fixture','rejected',[],project)
    path=project/'relationships_data/state/processed_documents.json';s=read(path);s['documents'][src['source_id']]={'status':'downloaded'};write(path,s)
    cache=project/'.cache/relationships/documents';cache.mkdir(parents=True)
    (cache/f"{src['source_id']}.html").write_bytes(raw)
    write(cache/f"{src['source_id']}.json",parsed);extract_pending(project)
    assert next(r for r in load_master(project)['relationships'] if r['relationship_id']==rel['relationship_id'])['verification']=='rejected'
    assert read(path)['documents'][src['source_id']]['status']=='candidate_created'

def test_sec_attachment_queue_resumes_outside_overlap(project,monkeypatch):
    cfg=read(project/'relationships_config/settings.json');cfg['max_documents_per_run']=1;write(project/'relationships_config/settings.json',cfg);write(project/'relationships_config/official_sources.json',[])
    state=read(project/'relationships_data/state/processed_documents.json');primary='https://www.sec.gov/Archives/edgar/data/123/000000012320000001/old.htm'
    state['documents']['old']={'url':primary,'status':'discovered','meta':dict(source_type='sec_filing',publisher='fixture',form='8-K',accession_number='0000000123-20-000001',filing_cik='0000000123',filed_date='2020-01-01')};write(project/'relationships_data/state/processed_documents.json',state)
    monkeypatch.setattr('relationships_py.collector.user_agent',lambda:'Fixture reviewer@example.test')
    monkeypatch.setattr('relationships_py.collector.Client',lambda *a,**kw:object())
    monkeypatch.setattr('relationships_py.collector.sec_discover',lambda *a:[])
    monkeypatch.setattr('relationships_py.collector.attachments',lambda *a:[{'url':primary.replace('old.htm','ex10.htm'),'type':'EX-10.1'}])
    downloaded=[]
    def fake_ingest(client,url,meta,root):
        s=read(root/'relationships_data/state/processed_documents.json')
        for item in s['documents'].values():
            if item['url']==url:item['status']='parsed'
        write(root/'relationships_data/state/processed_documents.json',s);downloaded.append(url)
    monkeypatch.setattr('relationships_py.collector.ingest',fake_ingest)
    collect(project);assert downloaded==[primary]
    collect(project);assert downloaded==[primary,primary.replace('old.htm','ex10.htm')]
    assert len(read(project/'relationships_data/state/processed_documents.json')['documents'])==2

def test_unsupported_sec_xsl_paths_do_not_abort_supported_filings(project,monkeypatch):
    cfg=read(project/'relationships_config/universe.json');cfg['pilot']['securities']=cfg['pilot']['securities'][:1];write(project/'relationships_config/universe.json',cfg)
    monkeypatch.setattr('relationships_py.collector.user_agent',lambda:'Fixture contact')
    monkeypatch.setattr('relationships_py.collector.Client',lambda *a,**kw:object())
    monkeypatch.setattr('relationships_py.collector.sec_discover',lambda *a:[
        dict(form='4',accessionNumber='0000320193-26-000001',primaryDocument='xslF345X05/wk.xml',filingDate='2026-09-25'),
        dict(form='8-K',accessionNumber='0000320193-26-000002',primaryDocument='report.htm',filingDate='2026-09-25')])
    monkeypatch.setattr('relationships_py.collector.attachments',lambda *a:[])
    monkeypatch.setattr('relationships_py.collector.ir_discover',lambda *a:pytest.fail('SEC-only must not discover IR'))
    downloaded=[]
    monkeypatch.setattr('relationships_py.collector.ingest',lambda client,url,meta,root:downloaded.append(meta['form']))
    result=collect(project,sec_only=True)
    assert result['errors']==[] and downloaded==['8-K']
    state=read(project/'relationships_data/state/processed_documents.json')
    assert state['companies']['co-aapl']['supported_filings']==1
    assert state['companies']['co-aapl']['unsupported_filings']==1

def test_asset_fingerprint_is_stable_and_covers_all_modules(tmp_path):
    import shutil
    spec=importlib.util.spec_from_file_location('version_assets',ROOT/'scripts/version-map-assets.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    shutil.copytree(ROOT/'assets/relationships',tmp_path/'assets/relationships');shutil.copy2(ROOT/'map.html',tmp_path/'map.html')
    first=module.version(tmp_path);assert module.version(tmp_path)==first
    dependency=tmp_path/'assets/relationships/formatters.js';dependency.write_text(dependency.read_text()+'\n// fixture change\n')
    second=module.version(tmp_path);assert second!=first
    assert first not in (tmp_path/'map.html').read_text()
    assert all('?v='+second in line for line in (tmp_path/'assets/relationships/map.js').read_text().splitlines() if line.startswith('import '))
