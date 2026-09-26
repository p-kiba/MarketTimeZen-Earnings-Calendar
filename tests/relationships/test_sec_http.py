import json
from datetime import date,datetime,timezone,timedelta
from unittest.mock import patch
import pytest
from relationships_py.sec_client import rows,archive_url,discover,attachments,months_before
from relationships_py.http import Client,Forbidden,Unsupported,retry_delay,check_dns
from relationships_py.config import settings
from relationships_py.ir_client import discover as ir_discover


def test_columns_reject_mismatches_and_archive_uses_issuer_cik():
    with pytest.raises(ValueError):rows({'form':['8-K'],'accessionNumber':[],'filingDate':[],'primaryDocument':[]})
    assert '/51143/000119312526123456/' in archive_url('0000051143','0001193125-26-123456','document.htm')
    with pytest.raises(ValueError):archive_url('0000051143','0001193125-26-123456','../secret.htm')

def test_calendar_backfill_months():
    assert months_before(date(2024,3,31),1)==date(2024,2,29)

def test_sec_history_and_amendments():
    columns={'form':['8-K/A'],'accessionNumber':['0000000001-26-000002'],'filingDate':['2026-09-10'],'primaryDocument':['doc.htm']}
    history={'form':['8-K'],'accessionNumber':['0000000001-25-000001'],'filingDate':['2025-01-01'],'primaryDocument':['old.htm']}
    class Fake:
        def get(self,url):return json.dumps(history if '-submissions-' in url else {'cik':1,'filings':{'recent':columns,'files':[{'name':'CIK0000000001-submissions-001.json','filingTo':'2025-01-01'}]}}).encode(),url,'application/json'
    result=discover(Fake(),'0000000001','2024-01-01')
    assert {r['form'] for r in result}=={'8-K','8-K/A'}

def test_exhibits_discovered_from_index_not_guessed():
    class Fake:
        def get(self,url):return b'<table class="tableFile"><tr><td>1</td><td>Contract</td><td><a href="contract.htm">doc</a></td><td>EX-10.1</td></tr><tr><td>2</td><td>Other</td><td><a href="other.htm">x</a></td><td>EX-101</td></tr></table>',url,'text/html'
    result=attachments(Fake(),'0000051143',{'accessionNumber':'0001193125-26-123456'})
    assert len(result)==1 and result[0]['url'].endswith('/contract.htm')

class Response:
    def __init__(self,status=200,body=b'hello world',headers=None):self.status_code=status;self.body=body;self.headers=headers or {}
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def raise_for_status(self):
        if self.status_code>=400:raise RuntimeError(str(self.status_code))
    def iter_content(self,n):yield self.body
class Session:
    def __init__(self,items):self.items=iter(items);self.calls=0
    def get(self,*args,**kwargs):self.calls+=1;return next(self.items)

@pytest.mark.parametrize('code',[429,503])
def test_retry_after_is_respected(tmp_path,code):
    session=Session([Response(code,headers={'Retry-After':'2'}),Response()]);c=Client({'official.test'},settings(),root=tmp_path,session=session)
    with patch('relationships_py.http.check_dns'),patch.object(c,'throttle'),patch('relationships_py.http.time.sleep') as sleep:
        assert c.get('https://official.test/file')[0]==b'hello world';sleep.assert_called_once_with(2)

def test_403_stops_without_retry(tmp_path):
    session=Session([Response(403)]);c=Client({'official.test'},settings(),root=tmp_path,session=session)
    with patch('relationships_py.http.check_dns'),patch.object(c,'throttle'):
        with pytest.raises(Forbidden):c.get('https://official.test/file')
    assert session.calls==1

def test_redirect_to_unapproved_host_is_blocked(tmp_path):
    c=Client({'official.test'},settings(),root=tmp_path,session=Session([Response(302,headers={'Location':'https://evil.test/a'})]))
    with patch('relationships_py.http.check_dns'),patch.object(c,'throttle'):
        with pytest.raises(ValueError):c.get('https://official.test/file')

def test_size_and_block_page_rejected(tmp_path):
    cfg=settings();cfg['max_document_bytes']=3;c=Client({'official.test'},cfg,root=tmp_path,session=Session([Response()]))
    with patch('relationships_py.http.check_dns'),patch.object(c,'throttle'):
        with pytest.raises(Unsupported):c.get('https://official.test/a')

def test_private_dns_rejected():
    with patch('socket.getaddrinfo',return_value=[(None,None,None,None,('127.0.0.1',443))]):
        with pytest.raises(ValueError):check_dns('https://official.test/a')

def test_retry_after_http_date():
    from email.utils import format_datetime
    future=datetime.now(timezone.utc)+timedelta(seconds=30)
    assert 28<retry_delay(format_datetime(future),0)<=30

def test_rate_lock_shared_across_sec_hosts(tmp_path):
    c=Client({'www.sec.gov','data.sec.gov'},settings(),root=tmp_path)
    with patch('relationships_py.http.time.time',return_value=100),patch('relationships_py.http.time.sleep') as sleep:
        c.throttle('https://www.sec.gov/a');c.throttle('https://data.sec.gov/b')
        assert sleep.call_args.args[0]==.5
