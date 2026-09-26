"""Publish only explicit, complete claims from official company announcements."""
import re
from copy import deepcopy
from pathlib import Path

from .exporter import export, public_subset
from .state import ROOT, digest, load_master, now, save_master, write
from .config import settings
from .tiers import APPROVED
from .validation import validate_master

RULE_ID = 'explicit_official_announcement'
RULE_VERSION = '1'
VERBS = {
    'partnership': r'\b(partner(?:ship|ed|ing)?|collaborat\w*|joint venture)\b',
    'investment': r'\b(invest(?:ed|ment)?|equity stake|purchase shares)\b',
    'acquisition': r'\b(acquir\w*|acquisition|buyout)\b',
    'supplier': r'\b(supply|supplies|supplier)\b',
    'service_provider': r'\b(provid\w*|services contract)\b',
}
NEGATION = re.compile(r'\b(?:not|no|never|without|potential|could|may|example|illustrat\w*|expect\w*)\b', re.I)
GENERIC_TITLE_WORDS = {'announce', 'announces', 'announced', 'agreement', 'strategic', 'partnership',
                       'partners', 'partner', 'collaboration', 'collaborate', 'investment',
                       'invests', 'invest', 'major', 'new', 'expansion', 'expand', 'company',
                       'companies', 'press', 'release', 'news', 'today', 'their', 'with', 'and',
                       'from', 'into', 'will', 'more', 'group', 'corporation'}


def company_name(company):
    return re.sub(r'\b(?:Inc\.?|Corp\.?|Corporation|LLC|Ltd\.?|plc)\b.*$', '', company['display_name'], flags=re.I).strip(' ,.')


def eligible(rel, event, evidence, source, companies):
    if rel['verification'] not in ('candidate', 'needs_review') or event['verification'] not in ('candidate', 'needs_review'):
        return False
    if source['source_type'] not in ('official_newsroom', 'official_ir') or not source.get('published_date'):
        return False
    if rel['relationship_type'] not in VERBS or not rel['status_as_of'] or len(rel['latest_event_ids']) != 1:
        return False
    if rel['source_company_id'] == rel['target_company_id'] or not all(companies[c]['entity_status'] == 'resolved' for c in (rel['source_company_id'], rel['target_company_id'])):
        return False
    if event['event_id'] not in rel['latest_event_ids'] or event['relationship_ids'] != [rel['relationship_id']]:
        return False
    if event['announced_date'] != source['published_date'] or not rel['evidence_ids'] or not event['evidence_ids']:
        return False
    if any(event['field_verification'].get(field, {}).get('evidence_ids') != [evidence['evidence_id']]
           for field in ('parties', 'relationship', 'status')):
        return False
    title = source['title'] or ''
    excerpt = evidence['excerpt']
    if len(excerpt.split()) < 8:
        return False
    names = [company_name(companies[c]) for c in (rel['source_company_id'], rel['target_company_id'])]
    if any(len(name) < 4 or not re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', title, re.I) or not re.search(r'(?<!\w)' + re.escape(name) + r'(?!\w)', excerpt, re.I) for name in names):
        return False
    topic = title
    for name in names:
        topic = re.sub(re.escape(name), ' ', topic, flags=re.I)
    descriptive = {word.lower() for word in re.findall(r'[A-Za-z]{4,}', topic)} - GENERIC_TITLE_WORDS
    if len(descriptive) < 2:
        return False
    verb = VERBS[rel['relationship_type']]
    if not re.search(verb, title, re.I) or not re.search(verb, excerpt, re.I) or NEGATION.search(excerpt):
        return False
    if rel['relationship_type'] == 'investment':
        actor = re.search(r'(?<!\w)' + re.escape(names[0]) + r'(?!\w)', excerpt, re.I)
        action = re.search(verb, excerpt, re.I)
        target = re.search(r'(?<!\w)' + re.escape(names[1]) + r'(?!\w)', excerpt, re.I)
        if not actor or not action or not target or not (actor.start() < action.start() < target.start()):
            return False
    elif rel['relationship_type'] != 'partnership':
        # Generic paragraph extraction does not establish the direction of
        # supply, service or acquisition claims yet.
        return False
    return True


def auto_publish(root=ROOT):
    root = Path(root)
    if not settings(root)['auto_publish_strict']:
        raise ValueError('Strict automatic publication is disabled')
    master = load_master(root)
    original = deepcopy(master)
    idx = validate_master(master, root)
    current_public = public_subset(master)
    public_evidence = {item['evidence_id']: item for item in current_public['evidence']}
    excerpts_by_source = {}
    for item in public_evidence.values():
        excerpts_by_source.setdefault(item['source_id'], set()).add(item['excerpt'])
    grouped = set()
    for rel in master['relationships']:
        if rel['verification'] not in APPROVED:
            continue
        for eid in rel['evidence_ids']:
            sid = idx['evidence'][eid]['source_id']
            grouped.add((sid, frozenset((rel['source_company_id'], rel['target_company_id'])), rel['relationship_type']))
    published = []
    priority = {'investment': 0, 'partnership': 1}
    for rel in sorted(master['relationships'], key=lambda item: (priority.get(item['relationship_type'], 2), item['relationship_id'])):
        if len(rel['latest_event_ids']) != 1 or len(rel['evidence_ids']) != 1:
            continue
        event = idx['events'].get(rel['latest_event_ids'][0])
        evidence = idx['evidence'].get(rel['evidence_ids'][0])
        if not event or not evidence:
            continue
        source = idx['sources'][evidence['source_id']]
        key = (source['source_id'], frozenset((rel['source_company_id'], rel['target_company_id'])), rel['relationship_type'])
        if key in grouped or not eligible(rel, event, evidence, source, idx['companies']):
            continue
        source_excerpts = excerpts_by_source.setdefault(source['source_id'], set())
        available = 25 - sum(len(text.split()) for text in source_excerpts)
        if evidence['excerpt'] not in source_excerpts and len(evidence['excerpt'].split()) > available:
            original_excerpt = evidence['excerpt']
            if available < 8:
                continue
            words = original_excerpt.split()[:available]
            while words and words[-1].lower().strip(',;:') in {'such', 'the', 'a', 'an', 'and', 'or',
                                                                'of', 'to', 'in', 'for', 'with', 'by',
                                                                'that', 'which', 'as', 'from', 'at',
                                                                'into', 'on', 'its'}:
                words.pop()
            evidence['excerpt'] = ' '.join(words)
            if not eligible(rel, event, evidence, source, idx['companies']):
                evidence['excerpt'] = original_excerpt
                continue
            evidence['normalized_text_hash'] = digest(evidence['excerpt'])
        grouped.add(key)
        source_excerpts.add(evidence['excerpt'])
        stamp = now()
        meta = {'reviewer': None, 'rule_id': RULE_ID, 'rule_version': RULE_VERSION,
                'verified_at': stamp, 'reason': 'Automatically included from an explicit, complete official announcement; no manual source review.',
                'evidence_hashes': {source['source_id']: source['content_hash']}}
        rel.update(description=source['title'], lifecycle_status='announced', direction='undirected' if rel['relationship_type']=='partnership' else rel['direction'],
                   verification='approved_rule', verification_metadata=meta)
        event.update(verification='approved_rule', verification_metadata=dict(meta))
        for field in ('parties', 'relationship', 'status'):
            event['field_verification'][field]['verification'] = 'approved_rule'
        published.append(rel['relationship_id'])
    if published:
        validate_master(public_subset(master), root, public=True)
        save_master(master, root)
    result = {'published_ids': published, 'published_count': len(published), 'publication_rule': RULE_ID}
    try:
        result['release'] = export(root)
    except Exception:
        if published:
            save_master(original, root)
        raise
    write(root/'relationships_data/state/automatic_publication.json', result)
    return result
