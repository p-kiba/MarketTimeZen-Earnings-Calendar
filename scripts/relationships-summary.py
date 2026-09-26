import json,os
from pathlib import Path
state=json.loads(Path('relationships_data/state/processed_documents.json').read_text())
round_path=Path('relationships_data/state/collection_round.json')
round_state=json.loads(round_path.read_text()) if round_path.exists() else {}
summary='## Company connections\n\nPublication: '+os.getenv('EXPORT_OUTCOME','not run')+'\n\n'
publication_path=Path('relationships_data/state/automatic_publication.json')
publication=json.loads(publication_path.read_text()) if publication_path.exists() else {}
summary+='Automatically included from explicit official announcements (not manually reviewed): '+str(publication.get('published_count',0))+'\n\n'
summary+='New candidates: '+str(len(round_state.get('new_candidate_ids',[])))+'\n\n'
changes=round_state.get('extraction',{}).get('discovery',{}).get('changes',{})
summary+='Private review hints (not confirmed changes): '+json.dumps(changes.get('counts',{}),ensure_ascii=False)+'\n\n'
summary+='Collection-stage pointer unchanged before auto-publication: '+str(round_state.get('public_pointer_unchanged','unknown'))+'\n\n'
errors=state.get('last_run',{}).get('errors',[])
if errors and os.getenv('GITHUB_ACTIONS'):print('::warning::Relationship collection has '+str(len(errors))+' partial errors; inspect the review artifact and collection state.')
summary+='Last collection (partial failures are retained):\n```json\n'+json.dumps(state.get('last_run'),ensure_ascii=False,indent=2)+'\n```\n'
path=os.getenv('GITHUB_STEP_SUMMARY')
if path:
    with open(path,'a') as f:f.write(summary)
else:print(summary)
