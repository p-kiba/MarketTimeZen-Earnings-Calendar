"""Only temporary local repositories: never contacts or pushes the real origin."""
import os
import subprocess
import pytest
from relationships_py.state import ROOT

def git(directory,*args):
    return subprocess.check_output(['git','-C',str(directory),*args],text=True,stderr=subprocess.DEVNULL).strip()

@pytest.fixture
def repositories(tmp_path):
    remote=tmp_path/'remote.git';remote.mkdir();git(remote,'init','--bare')
    a=tmp_path/'a';a.mkdir();git(a,'init','-b','main');git(a,'config','user.name','fixture');git(a,'config','user.email','fixture@example.test')
    (a/'calendar.json').write_text('original');git(a,'add','calendar.json');git(a,'commit','-m','fixture initial');git(a,'remote','add','origin',str(remote));git(a,'push','origin','main')
    b=tmp_path/'b';git(tmp_path,'clone','-b','main',str(remote),str(b));git(b,'config','user.name','fixture');git(b,'config','user.email','fixture@example.test')
    return a,b,remote

def run_script(a):
    return subprocess.run(['bash',str(ROOT/'scripts/commit-generated.sh'),'relationships.json'],cwd=a,env={**os.environ,'GITHUB_REF_NAME':'main'},capture_output=True,text=True)

def test_concurrent_remote_update_is_never_overwritten(repositories):
    a,b,remote=repositories
    (b/'calendar.json').write_text('newer calendar');git(b,'add','calendar.json');git(b,'commit','-m','fixture concurrent');git(b,'push','origin','main');latest=git(remote,'rev-parse','main')
    (a/'relationships.json').write_text('fixture relationships')
    result=run_script(a)
    assert result.returncode!=0 and 'Remote advanced' in result.stdout
    assert git(remote,'rev-parse','main')==latest and git(remote,'show','main:calendar.json')=='newer calendar'

def test_allowlisted_git_save_does_not_include_raw_files(repositories):
    a,_,remote=repositories;(a/'relationships.json').write_text('fixture relationships');(a/'raw-secret.txt').write_text('fixture, not real secret')
    assert run_script(a).returncode==0
    assert git(remote,'ls-tree','--name-only','main').splitlines()==['calendar.json','relationships.json']
