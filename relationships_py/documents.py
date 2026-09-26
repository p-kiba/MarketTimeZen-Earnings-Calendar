import json
from io import BytesIO
from datetime import datetime
import re
from bs4 import BeautifulSoup
from .state import digest
from .http import Unsupported

VERSION='rules-1.7'

def parse_pdf(raw):
    """Text PDFs only; retain one-based page locators for manual evidence review."""
    from pypdf import PdfReader
    from pypdf.errors import PdfReadError
    try:reader=PdfReader(BytesIO(raw),strict=True)
    except PdfReadError as error:raise Unsupported('Unreadable PDF; use an accessible text source') from error
    if reader.is_encrypted:raise Unsupported('Encrypted PDF is not supported')
    if len(reader.pages)>200:raise Unsupported('PDF exceeds 200-page extraction limit')
    blocks=[];characters=0
    for number,page in enumerate(reader.pages,1):
        text=' '.join((page.extract_text() or '').split())
        characters+=len(text)
        if characters>2000000:raise Unsupported('PDF exceeds text extraction limit')
        if text:blocks.append({'locator':f'pdf-page:{number}','text':text})
    if characters<80:raise Unsupported('PDF has insufficient text; OCR is not implemented')
    return {'title':str((reader.metadata or {}).get('/Title') or 'Official PDF disclosure'),
            'blocks':blocks,'published_date':None,'normalized_hash':digest(blocks)}

def parse_document(raw,content_type='text/html'):
    if raw[:4]==b'%PDF' or 'pdf' in content_type:return parse_pdf(raw)
    soup=BeautifulSoup(raw,'html.parser')
    for el in soup(['script','style','nav','footer','header','noscript']):el.decompose()
    root=soup.find('article') or soup.find('main') or soup
    # NVIDIA newsroom uses <article> for related-story teasers, while the
    # disclosure itself lives in .article-body. Never pin the teaser as evidence.
    if root.name == 'article' and 'index-item' in root.get('class', []) and soup.select_one('div.article-body'):
        root=soup.select_one('div.article-body')
    if root.name == 'article' and 'card-block' in root.get('class', []) and soup.select_one('.entry-content'):
        root=soup.select_one('.entry-content')
    blocks=[]
    # Amazon News exposes full article text inside role-labelled divs instead of
    # paragraph elements. Prefer those article-body blocks over related-story
    # cards so we can pin actual disclosure wording and avoid sidebar noise.
    article_body=soup.select('div.contentItem-role-text')
    if article_body:
        for el in article_body:
            text=' '.join(el.stripped_strings)
            if text and (not blocks or blocks[-1]['text']!=text):blocks.append({'locator':f'p:{len(blocks)}','text':text})
    else:
        for el in root.find_all(['h1','h2','h3','p','tr','li']):
            text=' '.join(el.stripped_strings)
            if text and (not blocks or blocks[-1]['text']!=text):blocks.append({'locator':f'{el.name}:{len(blocks)}','text':text})
    # Many SEC inline-XBRL filings put their actual notes in div/span elements.
    # Append these with a separate locator namespace: existing paragraph proofs
    # stay stable, and hidden XBRL metadata/table duplicates are not prose.
    # EDGAR exhibit/prospectus wrappers can contain the same div/font prose
    # without inline XBRL. Their payment clauses must be retained too.
    # Preserve the legacy body locator for exhibits with no paragraph/table
    # blocks; append new locators instead of invalidating existing evidence.
    if not blocks and re.search(br'<DOCUMENT>\s*<TYPE>',raw[:1024],re.I) and not soup.find(lambda t: t.name and t.name.startswith('ix:')):
        text=' '.join(root.stripped_strings)
        if len(text)>=80:blocks.append({'locator':'body','text':text})
    if soup.find(lambda t: t.name and t.name.startswith('ix:')) or re.search(br'<DOCUMENT>\s*<TYPE>',raw[:1024],re.I):
        seen={b['text'] for b in blocks}
        for index,el in enumerate(root.find_all('div')):
            if el.find(['div','p','tr','table','li']) or el.find_parent(['table','p','li']):continue
            if any(a.has_attr('hidden') or re.search(r'display\s*:\s*none|visibility\s*:\s*hidden',a.get('style',''),re.I) or a.name in ('ix:hidden','ix:header') for a in [el,*el.parents]):continue
            text=' '.join(el.stripped_strings)
            if len(text)>=80 and text not in seen:
                blocks.append({'locator':f'sec-div:{index}','text':text});seen.add(text)
    # AWS customer-story cards render their public descriptions in labelled spans.
    # Append a separate namespace without changing existing paragraph locators.
    for index,el in enumerate(soup.select('span[data-rg-n="BodyText"]')):
        text=' '.join(el.stripped_strings)
        if text:blocks.append({'locator':f'aws-card:{index}','text':text})
    if not blocks:
        text=' '.join(root.stripped_strings)
        if len(text)<80:raise Unsupported('No readable text; image or JavaScript-only document')
        blocks=[{'locator':'body','text':text}]
    if sum(len(x['text']) for x in blocks)<80:raise Unsupported('Insufficient readable text')
    published=None
    # Visible article date takes precedence over unrelated site-wide metadata.
    for block in blocks[:6]:
        for fmt in ('%B %d, %Y', '%b %d, %Y'):
            try: published = datetime.strptime(block['text'], fmt).date().isoformat()
            except ValueError: continue
            break
        if published: break
    for item in ([] if published else soup.find_all('meta')):
        if item.get('property') in ('article:published_time','og:published_time') or item.get('name') in ('date','pubdate','datePublished'):
            candidate=item.get('content','')
            if re.match(r'^\d{4}-\d{2}-\d{2}',candidate):published=candidate[:10]
    if not published:
        for el in soup.find_all('time'):
            candidate=el.get('datetime','')
            if re.match(r'^\d{4}-\d{2}-\d{2}',candidate):published=candidate[:10];break
    return {'title':soup.title.get_text(' ',strip=True) if soup.title else 'Untitled source','blocks':blocks,'published_date':published,'normalized_hash':digest(blocks)}
