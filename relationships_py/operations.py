"""Collection and reviewed release are separate operator actions."""
from pathlib import Path
from .state import ROOT, read, write, load_master, digest, now
from .validation import validate_master, ID
from .exporter import public_subset, export


def collect_round(root=ROOT, mode='incremental', months=24, sec_only=False):
    from .collector import collect
    from .review import extract_pending, review_report
    root=Path(root)
    before={r['relationship_id'] for r in load_master(root)['relationships']}
    # The configured large-cap focus runs under one document/network budget.
    # This deliberately does not call any verifier, exporter or deployment.
    result={'started_at':now(),'collection':collect(root,mode,months,'large_cap_focus',sec_only)}
    result['extraction']=extract_pending(root)
    result['report']=str(Path(review_report(root)).relative_to(root))
    master=load_master(root)
    result['new_candidate_ids']=[r['relationship_id'] for r in master['relationships'] if r['relationship_id'] not in before and r['verification'] in ('candidate','needs_review')]
    result['finished_at']=now();result['published']=False
    write(root/'relationships_data/state/collection_round.json',result)
    return result


def prepare_release(reviewer, reason, root=ROOT):
    if not reviewer.strip() or not reason.strip():raise ValueError('Review attribution and reason required')
    root=Path(root);data=public_subset(load_master(root));validate_master(data,root,public=True)
    fingerprint=digest(data);review_id='release-'+fingerprint[:24]
    receipt=dict(review_id=review_id,approved_data_hash=fingerprint,reviewed_at=now(),reviewer=reviewer,reason=reason,
                 counts={k:len(v) for k,v in data.items()},deployment_authorized=False)
    path=root/'relationships_data/review/releases'/f'{review_id}.json'
    # A content-addressed approval is immutable and never auto-renewed by collection.
    if path.exists():return read(path)
    write(path,receipt);return receipt


def release_reviewed(review_id, root=ROOT):
    root=Path(root)
    if not ID.fullmatch(review_id) or not review_id.startswith('release-'):raise ValueError('Invalid review ID')
    receipt=read(root/'relationships_data/review/releases'/f'{review_id}.json')
    data=public_subset(load_master(root));validate_master(data,root,public=True)
    if not receipt or receipt.get('review_id')!=review_id or receipt.get('approved_data_hash')!=digest(data):
        raise ValueError('Approved records or sources changed after review; prepare a new review')
    result=export(root)
    write(root/'relationships_data/state/last_reviewed_release.json',dict(review_id=review_id,released_at=now(),result=result,deployed=False))
    return result
