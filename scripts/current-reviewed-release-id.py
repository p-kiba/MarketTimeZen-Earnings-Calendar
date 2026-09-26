"""Find the immutable review receipt matching the checked-out public records."""
from pathlib import Path

from relationships_py.exporter import public_subset
from relationships_py.state import ROOT, digest, load_master, read
from relationships_py.validation import validate_master


def current_review_id(root=ROOT):
    root = Path(root)
    data = public_subset(load_master(root))
    validate_master(data, root, public=True)
    fingerprint = digest(data)
    review_id = 'release-' + fingerprint[:24]
    receipt = read(root / 'relationships_data/review/releases' / f'{review_id}.json')
    if not receipt or receipt.get('review_id') != review_id or receipt.get('approved_data_hash') != fingerprint:
        raise ValueError('No reviewed release receipt matches the current public records')
    return review_id


if __name__ == '__main__':
    print(current_review_id())
