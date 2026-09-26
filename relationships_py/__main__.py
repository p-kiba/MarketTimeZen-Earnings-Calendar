import argparse
import json
from pathlib import Path
from .state import ROOT,lock,read,write
from .config import validate_config
from .collector import collect,ingest_url
from .review import extract_pending,review_report,decide,link_duplicate
from .exporter import export,validate_public

def main():
    p=argparse.ArgumentParser(description='Evidence-based company connections; collection does not publish or deploy.')
    p.add_argument('--root',type=Path,default=ROOT)
    sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('validate-config');sub.add_parser('validate-public');sub.add_parser('extract');sub.add_parser('review-report')
    c=sub.add_parser('collect');c.add_argument('--mode',choices=['incremental','backfill'],default='incremental');c.add_argument('--months',type=int,default=24);c.add_argument('--universe',choices=['pilot','custom','sp500','large_cap_focus'],default='pilot')
    c.add_argument('--sec-only',action='store_true',help='Collect SEC submissions without running IR discovery')
    i=sub.add_parser('ingest-url');i.add_argument('--url',required=True)
    e=sub.add_parser('export');e.add_argument('--allow-removal',action='store_true')
    for command in ('approve','reject','withdraw'):
        d=sub.add_parser(command);d.add_argument('--candidate-id',required=True);d.add_argument('--reviewer',required=True);d.add_argument('--reason',required=True);d.add_argument('--fields',default='parties,relationship,status')
    d=sub.add_parser('link-duplicate');d.add_argument('--source-id',required=True);d.add_argument('--target-id',required=True);d.add_argument('--reviewer',required=True);d.add_argument('--reason',required=True)
    d=sub.add_parser('resolve-universe');d.add_argument('--universe',choices=['pilot','custom','sp500','large_cap_focus'],default='pilot')
    sub.add_parser('discover-ir')
    r=sub.add_parser('rollback');r.add_argument('--build-id',required=True)
    sub.add_parser('verify-pilot-rules')
    sub.add_parser('verify-deal-rules')
    b=sub.add_parser('apply-review-batch');b.add_argument('--batch',type=Path,required=True)
    b=sub.add_parser('collect-round');b.add_argument('--mode',choices=['incremental','backfill'],default='incremental');b.add_argument('--months',type=int,default=24);b.add_argument('--sec-only',action='store_true')
    b=sub.add_parser('prepare-release');b.add_argument('--reviewer',required=True);b.add_argument('--reason',required=True)
    b=sub.add_parser('release-reviewed');b.add_argument('--review-id',required=True)
    sub.add_parser('discover-statements')
    d=sub.add_parser('draft-disclosure');d.add_argument('--source-id',required=True)
    args=p.parse_args()
    with lock(args.root):
        if args.command=='validate-config':result=validate_config(args.root)
        elif args.command=='validate-public':result=validate_public(args.root)
        elif args.command=='collect':result=collect(args.root,args.mode,args.months,args.universe,args.sec_only)
        elif args.command=='ingest-url':result={'source_id':ingest_url(args.url,args.root)}
        elif args.command=='extract':result=extract_pending(args.root)
        elif args.command=='review-report':result={'report':review_report(args.root)}
        elif args.command=='export':result=export(args.root,args.allow_removal)
        elif args.command=='verify-deal-rules':
            from .deal_rules import verify
            result=verify(args.root)
        elif args.command=='apply-review-batch':
            from .review_batch import apply_batch
            result=apply_batch(args.batch,args.root)
        elif args.command=='collect-round':
            from .operations import collect_round
            result=collect_round(args.root,args.mode,args.months,args.sec_only)
        elif args.command=='prepare-release':
            from .operations import prepare_release
            result=prepare_release(args.reviewer,args.reason,args.root)
        elif args.command=='release-reviewed':
            from .operations import release_reviewed
            result=release_reviewed(args.review_id,args.root)
        elif args.command=='discover-statements':
            from .discovery import discover_statements
            result=discover_statements(args.root)
        elif args.command=='draft-disclosure':
            from .discovery import draft_disclosure
            result=draft_disclosure(args.source_id,args.root)
        elif args.command=='verify-pilot-rules':
            from .pilot_rules import verify
            result=verify(args.root)
        elif args.command=='link-duplicate':result=link_duplicate(args.source_id,args.target_id,args.reviewer,args.reason,args.root)
        elif args.command=='resolve-universe':
            from .entities import resolve_universe
            result=resolve_universe(args.root,args.universe)
        elif args.command=='discover-ir':
            from .collector import discover_ir
            result=discover_ir(args.root)
        elif args.command=='rollback':
            from .state import digest
            from .validation import ID
            if not ID.fullmatch(args.build_id):raise ValueError('Unsafe build ID')
            path=args.root/'output_json/relationships/versions'/args.build_id/'manifest.json'
            pointer={'schema_version':'1.0','build_id':args.build_id,'manifest':f'versions/{args.build_id}/manifest.json','manifest_hash':digest(path.read_bytes()),'previous':None}
            validate_public(args.root,pointer);write(args.root/'output_json/relationships/latest.json',pointer);result=pointer
        else:result=decide(args.candidate_id,args.reviewer,args.reason,{'approve':'approved_manual','reject':'rejected','withdraw':'withdrawn'}[args.command],args.fields.split(','),args.root)
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
