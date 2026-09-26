from urllib.parse import urljoin,urlsplit
from urllib.robotparser import RobotFileParser
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from requests.exceptions import HTTPError
from .validation import safe_url
from .http import Unsupported


def check_robots(client,url):
    origin='https://'+urlsplit(url).netloc
    try:raw,_,_=client.get(origin+'/robots.txt')
    except HTTPError as error:
        # RFC 9309 §2.3.1.3: an absent robots file supplies no rules.
        # Keep authentication failures, throttling and server errors fail-closed.
        if error.response is not None and error.response.status_code in (404,410):return
        raise
    robot=RobotFileParser();robot.parse(raw.decode('utf-8',errors='replace').splitlines())
    if not robot.can_fetch('MarketTimeZen',url):raise Unsupported('robots.txt disallows this URL')

def discover(client,config):
    if not config.get('usage_reviewed_at') or not config.get('usage_note'):raise Unsupported('Review official source usage terms before collection')
    url=config.get('feed_url') or config.get('listing_url');safe_url(url,config['allowed_hosts'])
    check_robots(client,url);raw,_,_=client.get(url)
    links=[]
    if config['parser_type'] in ('rss','atom'):
        tree=ET.fromstring(raw)
        for item in list(tree.iter('item'))+list(tree.iter('{http://www.w3.org/2005/Atom}entry')):
            node=item.find('link')
            if node is None:node=item.find('{http://www.w3.org/2005/Atom}link')
            if node is not None:links.append(node.get('href') or node.text)
    elif config['parser_type']=='html':
        if not config.get('link_selector'):raise ValueError('HTML listing requires a specific selector')
        soup=BeautifulSoup(raw,'html.parser')
        links=[a.get('href') for a in soup.select(config['link_selector'])]
    else:raise Unsupported('Unsupported feed parser')
    result=[]
    for link in links:
        if not link:continue
        target=urljoin(url,link)
        if target.rstrip('/')==url.rstrip('/') or urlsplit(target).fragment:continue
        try:safe_url(target,config['allowed_hosts'])
        except ValueError:continue
        if target not in result:result.append(target)
    return result
