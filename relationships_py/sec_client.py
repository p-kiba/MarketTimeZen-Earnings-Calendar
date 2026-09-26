import calendar
import json
import re
from datetime import date, timedelta
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from .config import FORMS
from .validation import safe_url

HOSTS={'data.sec.gov','www.sec.gov'}

def months_before(day,months):
    serial=day.year*12+day.month-1-months;y,m=divmod(serial,12);m+=1
    return date(y,m,min(day.day,calendar.monthrange(y,m)[1]))

def rows(columns):
    required=('accessionNumber','filingDate','form','primaryDocument')
    if any(k not in columns for k in required):raise ValueError('Missing SEC submission columns')
    if any(not isinstance(v,list) for v in columns.values()) or len({len(v) for v in columns.values()})!=1:raise ValueError('SEC column lengths differ')
    return [dict(zip(columns,[columns[k][i] for k in columns])) for i in range(len(columns['form']))]

def archive_url(cik,accession,filename):
    if not re.fullmatch(r'\d{10}',cik) or not re.fullmatch(r'\d{10}-\d{2}-\d{6}',accession) or not re.fullmatch(r'[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)+',filename):raise ValueError('Invalid SEC archive components')
    return f'https://www.sec.gov/Archives/edgar/data/{int(cik)}/{accession.replace("-","")}/{filename}'

def discover(client,cik,since):
    raw,_,_=client.get(f'https://data.sec.gov/submissions/CIK{cik}.json');payload=json.loads(raw)
    if str(payload.get('cik','')).zfill(10)!=cik:raise ValueError('SEC issuer CIK mismatch')
    all_rows=rows(payload['filings']['recent'])
    for item in payload['filings'].get('files',[]):
        if item['filingTo']<since:continue
        name=item['name']
        if not re.fullmatch(r'CIK\d{10}-submissions-\d+\.json',name):raise ValueError('Invalid history filename')
        raw,_,_=client.get('https://data.sec.gov/submissions/'+name);all_rows.extend(rows(json.loads(raw)))
    selected={r['accessionNumber']:r for r in all_rows if r['filingDate']>=since}
    return list(selected.values())

def attachments(client,cik,filing):
    acc=filing['accessionNumber'];index=archive_url(cik,acc,acc+'-index.html')
    raw,_,_=client.get(index);soup=BeautifulSoup(raw,'html.parser');result=[]
    for tr in soup.select('table.tableFile tr'):
        cells=tr.find_all('td')
        if len(cells)<4:continue
        typ=cells[3].get_text(strip=True)
        if not re.match(r'^EX-(?:99|10|21)(?:\.|$)',typ):continue
        link=cells[2].find('a',href=True)
        if not link:continue
        url=urljoin(index,link['href']);safe_url(url,HOSTS)
        expected=f'/Archives/edgar/data/{int(cik)}/{acc.replace("-","")}/'
        from urllib.parse import urlsplit
        if not urlsplit(url).path.startswith(expected):raise ValueError('Exhibit outside filing directory')
        result.append({'url':url,'type':typ})
    return result
