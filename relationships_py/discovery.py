"""Private statement inbox: preserve n-ary/unknown parties without inventing edges.

This is discovery, not entity resolution or publication. Capitalized spans and
linked labels may be products or people; a curator must establish their identity.
Full paragraphs stay in the local cache, never in the public or committed inbox.
"""
import re
from pathlib import Path
from .state import ROOT, read, write, digest, stable_id, load_master
from .documents import parse_document
from .entities import resolve
from .changes import change_signals, write_change_review

RELATION = re.compile(r'\b(partner\w*|collaborat\w*|agreement\w*|suppl\w*|invest\w*|acqui\w*|adopt\w*|co-develop\w*|deliver\w*)\b', re.I)
NAME = re.compile(r'\b[A-Z][A-Za-z0-9&.-]*(?:\s+(?:[A-Z][A-Za-z0-9&.-]*)){0,4}\b')
STOP = {'The', 'This', 'These', 'Our', 'We', 'Today', 'As', 'For', 'In', 'It', 'With', 'AI', 'GPU', 'GPUs'}


def statement_candidates(source, parsed, companies, aliases=None):
    from urllib.parse import urlsplit
    if urlsplit(source['canonical_url']).path.lower().endswith(('.rdf','.rss','.xml')):return []
    result = []
    for block in parsed['blocks']:
        text = block['text']
        signals=change_signals(text)
        if not RELATION.search(text) and not signals:
            continue
        known = resolve(text, companies, aliases)
        # Suggestions are explicitly unresolved, including acronym-only names.
        names = sorted({m.group().strip(' .') for m in NAME.finditer(text)} - STOP)
        known_names = {c['display_name'].casefold() for c in known}
        unknown = [n for n in names if n.casefold() not in known_names][:40]
        result.append(dict(
            statement_id=stable_id('statement', source['source_id'], block['locator']),
            source_id=source['source_id'], source_url=source['canonical_url'],
            content_hash=source['content_hash'], locator=block['locator'],
            block_hash=digest(text), publisher_company_id=source['publisher'],
            mentioned_company_ids=[c['company_id'] for c in known],
            unresolved_mentions=unknown, verification='needs_review',
            reason='multi_party' if len(known) > 2 else 'unresolved_mentions' if unknown else 'bilateral_statement',
            relationship_ids=[],  # No all-pairs expansion, amount splitting or approval.
            change_signals=signals,
        ))
    return result


def discover_statements(root=ROOT):
    root = Path(root); master = load_master(root); rows = []; unavailable = []
    aliases = read(root/'relationships_config/aliases.json', {})
    for source in sorted(master['sources'],key=lambda s:(s['published_date'] or s['filed_date'] or '',s['source_id']),reverse=True):
        if source['source_type'] == 'test_fixture':
            continue
        path = root/'.cache/relationships/documents'/f"{source['source_id']}.html"
        if not path.exists():
            unavailable.append(source['source_id']); continue
        raw = path.read_bytes()
        if digest(raw) != source['content_hash']:
            unavailable.append(source['source_id']); continue
        rows.extend(statement_candidates(source, parse_document(raw), master['companies'], aliases))
    from .config import settings
    limit=settings(root)['max_candidates_per_run']
    changes=write_change_review(master,rows,limit,root)
    deferred=max(0,len(rows)-limit)
    write(root/'relationships_data/review/statements.json', {
        'version': '1.0', 'publication_eligible': False,
        'statements': rows[:limit], 'deferred_statements': deferred, 'unavailable_sources': unavailable,
    })
    return {'statements': min(limit,len(rows)), 'deferred_statements': deferred, 'unavailable_sources': len(unavailable), 'changes':changes, 'published': 0}


def draft_disclosure(source_id, root=ROOT):
    """Produce a local review worksheet; no executable approval/hash is generated."""
    root = Path(root)
    source = next(s for s in load_master(root)['sources'] if s['source_id'] == source_id)
    raw = (root/'.cache/relationships/documents'/f'{source_id}.html').read_bytes()
    if digest(raw) != source['content_hash']:
        raise ValueError('Source changed; re-ingest before review')
    parsed = parse_document(raw)
    path = root/'.cache/relationships/review'/f'{source_id}.json'
    write(path, {'source_id': source_id, 'url': source['canonical_url'],
        'content_hash': source['content_hash'], 'date_to_verify': source['published_date'],
        'verification': 'needs_review', 'claims': [],
        'check': ['Exact parties and roles; no implicit parent substitution',
                  'Product/service, direction, lifecycle and date',
                  'Amount scope/currency, options and shared totals',
                  'Source/block hashes and <=25 quoted words per source'],
        'blocks': [dict(b, block_hash=digest(b['text'])) for b in parsed['blocks']]})
    return {'private_worksheet': str(path), 'published': 0}
