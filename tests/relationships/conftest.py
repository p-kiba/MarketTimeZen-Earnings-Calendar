import shutil
from pathlib import Path
import pytest
from relationships_py.state import ROOT,load_master,write,read

@pytest.fixture
def project(tmp_path):
    for name in ('relationships_config','schemas/relationships'):
        shutil.copytree(ROOT/name,tmp_path/name)
    write(tmp_path/'relationships_data/state/processed_documents.json',{'documents':{},'companies':{},'feeds':{},'last_run':None})
    write(tmp_path/'relationships_data/overrides.json',{'decisions':{},'merges':{}})
    write(tmp_path/'relationships_data/state/sec_identities.json',read(ROOT/'relationships_data/state/sec_identities.json',{}))
    for key,rows in load_master().items():write(tmp_path/'relationships_data'/f'{key}.json',rows)
    return tmp_path
