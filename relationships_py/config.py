import os
import re
from pathlib import Path
from .state import ROOT, read

FORMS = ['8-K','8-K/A','10-K','10-K/A','10-Q','10-Q/A','6-K','6-K/A','20-F','20-F/A']

def settings(root=ROOT):
    return read(Path(root) / 'relationships_config/settings.json')

def universe(root=ROOT, mode='pilot'):
    config = read(Path(root) / 'relationships_config/universe.json')
    if mode not in ('pilot', 'custom', 'sp500', 'large_cap_focus'):
        raise ValueError('Unknown universe')
    group = config.get(mode)
    if not group:
        raise ValueError(f'{mode} universe is not configured')
    if mode == 'sp500' and not all(group.get(k) for k in ('as_of','source_url','license_note','securities')):
        raise ValueError('sp500 requires dated sourced licensed securities input')
    rows = group.get('securities', [])
    for row in rows:
        if not re.fullmatch(r'[A-Z0-9.^/-]{1,20}', row.get('symbol', '')):
            raise ValueError('Invalid symbol')
        if row.get('cik') and not re.fullmatch(r'\d{10}', row['cik']):
            raise ValueError('Invalid CIK')
        if not row.get('company_id'):
            raise ValueError('Security must map to a stable company ID')
    return group

def user_agent():
    value = os.environ.get('SEC_USER_AGENT', '')
    if not re.search(r'[^\s@]+@[^\s@]+\.[^\s@]+', value) or any(x in value.lower() for x in ('example.', 'your_email', '<', '>')):
        raise ValueError('Set SEC_USER_AGENT to application name and a real operational contact')
    return value

def validate_config(root=ROOT):
    cfg = settings(root)
    if not 0 < cfg['sec_requests_per_second'] <= 2:
        raise ValueError('SEC rate must be <= 2 requests/second')
    if cfg['auto_publish_strict']:
        raise ValueError('Broad automatic publishing is not supported; use evaluated source-bound rules')
    for mode in ('pilot','custom','sp500','large_cap_focus'):
        if read(Path(root)/'relationships_config/universe.json').get(mode):
            universe(root, mode)
    bounds = cfg['tiers']['USD']['minimums']
    if bounds != sorted(bounds, key=int) or len(set(bounds)) != 5 or len(bounds) != 5 or bounds[0] != '0':
        raise ValueError('Five ascending tier boundaries required')
    if not 1<=cfg['initial_nodes']<=30 or not cfg['initial_nodes']<=cfg['expanded_nodes']<=150:raise ValueError('Node bounds must be initial <= 30 and expanded <= 150')
    if any(not re.fullmatch(r'#[0-9a-fA-F]{6}',c) for c in cfg['tiers']['USD']['colors']) or len(cfg['tiers']['USD']['colors'])!=5:raise ValueError('Five hex colors required')
    if any(not isinstance(cfg[k],int) or cfg[k]<=0 for k in ('max_documents_per_run','max_attachments','max_candidates_per_run','backfill_months','overlap_days')):raise ValueError('Positive collection limits required')
    return {'valid': True, 'sec_contact_configured': bool(os.environ.get('SEC_USER_AGENT')), 'universe': cfg['universe']}
