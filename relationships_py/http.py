"""Allowlisted public HTTPS, bounded downloads and a cross-process SEC rate gate."""
import email.utils
import fcntl
import ipaddress
import random
import socket
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import requests
from .state import ROOT, read, write, digest
from .validation import safe_url

class Forbidden(RuntimeError): pass
class Unsupported(RuntimeError): pass

def check_dns(url):
    host=urlsplit(url).hostname
    addresses=socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(a[4][0]).is_global for a in addresses):
        raise ValueError('Non-public destination rejected')

def retry_delay(value,attempt):
    try:return max(0,float(value))
    except (ValueError,TypeError):
        try:return max(0,(email.utils.parsedate_to_datetime(value)-datetime.now(timezone.utc)).total_seconds())
        except (ValueError,TypeError,AttributeError):return 2**attempt+random.random()

class Client:
    def __init__(self,hosts,config,user_agent='MarketTimeZen source verification',root=ROOT,session=None):
        self.hosts=set(hosts); self.config=config; self.root=Path(root)
        self.session=session or requests.Session(); self.session.trust_env=False
        self.headers={'User-Agent':user_agent,'Accept-Encoding':'gzip, deflate'}
    def throttle(self,url):
        host=urlsplit(url).hostname
        group='sec' if host in ('www.sec.gov','data.sec.gov') else host
        interval=1/self.config['sec_requests_per_second'] if group=='sec' else self.config['ir_interval_seconds']
        path=self.root/'.cache/relationships/rate'/group;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('a+') as f:
            fcntl.flock(f,fcntl.LOCK_EX); f.seek(0); raw=f.read()
            last=float(raw or 0);time.sleep(max(0,last+interval-time.time()))
            f.seek(0);f.truncate();f.write(str(time.time()));f.flush()
    def get(self,url):
        cache=self.root/'.cache/relationships/http'/digest(url)
        saved=read(cache.with_suffix('.json'),{})
        headers=dict(self.headers)
        if saved.get('etag'):headers['If-None-Match']=saved['etag']
        if saved.get('modified'):headers['If-Modified-Since']=saved['modified']
        original=url
        for redirect in range(6):
            safe_url(url,self.hosts);check_dns(url)
            for attempt in range(4):
                self.throttle(url)
                with self.session.get(url,headers=headers,timeout=self.config['timeout_seconds'],stream=True,allow_redirects=False) as r:
                    if r.status_code==403:raise Forbidden('HTTP 403; stopped without retry')
                    if r.status_code in (429,503):
                        wait=retry_delay(r.headers.get('Retry-After'),attempt)
                        if attempt==3 or wait>60:raise RuntimeError(f'HTTP {r.status_code}; deferred retry')
                        time.sleep(wait);continue
                    if r.status_code in (301,302,303,307,308):
                        url=urljoin(url,r.headers['Location']);headers=dict(self.headers);break
                    if r.status_code==304:
                        if cache.with_suffix('.body').exists():return cache.with_suffix('.body').read_bytes(),saved['url'],saved.get('content_type','')
                        raise RuntimeError('304 with missing body; clear conditional cache metadata')
                    r.raise_for_status();body=bytearray()
                    for chunk in r.iter_content(65536):
                        body.extend(chunk)
                        if len(body)>self.config['max_document_bytes']:raise Unsupported('Document exceeds configured byte limit')
                    content=bytes(body); low=content[:100000].lower()
                    if not content or any(x in low for x in (b'undeclared automated tool',b'your request originates from an undeclared',b'request rate threshold exceeded',b'just a moment...',b'captcha')):raise RuntimeError('Empty or blocked document')
                    cache.parent.mkdir(parents=True,exist_ok=True);cache.with_suffix('.body').write_bytes(content)
                    write(cache.with_suffix('.json'),{'etag':r.headers.get('ETag'),'modified':r.headers.get('Last-Modified'),'url':url,'content_type':r.headers.get('Content-Type','')})
                    return content,url,r.headers.get('Content-Type','')
            else:raise RuntimeError('Retry limit reached')
        raise RuntimeError('Redirect limit reached')
