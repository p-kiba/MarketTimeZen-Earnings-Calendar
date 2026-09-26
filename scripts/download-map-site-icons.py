"""Fetch PNG/ICO site icons from explicitly configured company websites.

Run manually; results remain candidates until reviewed and added to logo_assets.json.
Never replaces an existing image or publishes data.
"""
import hashlib
import json
import struct
import sys
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

import requests

ROOT = Path(__file__).resolve().parents[1]


class Icons(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []
        self.title = ''
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'title':
            self.in_title = True
        if tag == 'link' and 'icon' in attrs.get('rel', '').lower():
            if attrs.get('href'):
                self.urls.append(attrs['href'])

    def handle_endtag(self, tag):
        if tag == 'title':
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data


def fetch(url):
    if urlsplit(url).scheme != 'https':
        raise ValueError('HTTPS required')
    with requests.get(url, timeout=12, stream=True, headers={'User-Agent': 'MarketTimeZen-LogoCollector/1.0'}) as response:
        response.raise_for_status()
        data = bytearray()
        for chunk in response.iter_content(65536):
            data.extend(chunk)
            if len(data) > 5_000_000:
                raise ValueError('Asset too large')
        if urlsplit(response.url).scheme != 'https':
            raise ValueError('HTTPS required')
        return bytes(data), response.url


def collect(item):
    cid, url = item
    result = {'company_id': cid, 'website': url, 'status': 'unavailable'}
    try:
        body, page = fetch(url)
        parser = Icons()
        parser.feed(body.decode('utf-8', errors='replace'))
        result.update(website=page, page_title=parser.title.strip())
        urls = list(dict.fromkeys([urljoin(page, u) for u in parser.urls] + [urljoin(page, '/favicon.ico')]))
        for icon in urls:
            try:
                data, source = fetch(icon)
                if data[:8] == b'\x89PNG\r\n\x1a\n' and len(data) >= 24:
                    width, height = struct.unpack('>II', data[16:24])
                    if not 16 <= width <= 4096 or not 16 <= height <= 4096:
                        continue
                    suffix = '.png'
                elif data[:4] == b'\x00\x00\x01\x00' and len(data) >= 22:
                    width, height = data[6] or 256, data[7] or 256
                    suffix = '.ico'
                else:
                    continue
                path = ROOT / '.cache/relationships/site-icons' / (cid + suffix)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
                return dict(result, status='candidate', source_url=source, candidate_path=str(path.relative_to(ROOT)),
                            width=width, height=height, sha256=hashlib.sha256(data).hexdigest())
            except (requests.RequestException, ValueError):
                continue
    except (requests.RequestException, ValueError) as error:
        result['error_type'] = type(error).__name__
    return result


if __name__ == '__main__':
    sites = json.loads(Path(sys.argv[1]).read_text())
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(collect, sites.items()))
    destination = ROOT / '.cache/relationships/site-icons-report.json'
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    for r in results:
        print(r['company_id'], r['status'], r.get('page_title', ''), r.get('source_url', ''), flush=True)
