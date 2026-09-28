import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {webcrypto} from 'node:crypto';
import vm from 'node:vm';
import {execFileSync} from 'node:child_process';
const root=new URL('../../../',import.meta.url);
const moduleFile=async name=>import('data:text/javascript;base64,'+Buffer.from(await readFile(new URL('assets/relationships/'+name,root),'utf8')).toString('base64'));
globalThis.location={href:'https://site.example/app/map.html',search:''};globalThis.history={pushState(){},replaceState(){}};
if(!globalThis.crypto)Object.defineProperty(globalThis,'crypto',{value:webcrypto,configurable:true});
const {nodePositions}=await moduleFile('layout.js');
const n=await moduleFile('navigation.js'),f=await moduleFile('formatters.js');
let count=0;async function test(name,fn){await fn();count++;console.log('PASS '+name);}
await test('favorites/month safe round trip and JP market',()=>{const s=n.queryState('?favorites=BRK.B,AAPL&month=2026-10&return_market=jp&return=https://evil.test');const u=new URL(n.calendarURL(s));assert.equal(u.pathname,'/app/japan.html');assert.equal(u.searchParams.get('favorites'),'BRK.B,AAPL');assert.equal(u.searchParams.get('month'),'2026-10');assert.equal(new URL(n.calendarURL(s,'AAPL')).pathname,'/app/index.html');});
await test('malformed IDs, month, timezone rejected',()=>{const s=n.queryState('?company=../../x&month=2026-99&tz=BAD&favorites=%3Cscript%3E,AAPL');assert.equal(s.company,null);assert.equal(s.month,null);assert.equal(s.tz,'America/New_York');assert.deepEqual(s.favorites,['AAPL']);});
await test('unsafe source schemes and local hosts rejected',()=>{for(const x of ['javascript:alert(1)','data:text/html,x','file:///etc/passwd','https://127.0.0.1/a','https://localhost/a','https://user:pass@foo.com'])assert.equal(n.safeSourceURL(x),null);assert.equal(n.safeSourceURL('https://www.sec.gov/a'),'https://www.sec.gov/a');});
const c=(id,name,symbols=[])=>({company_id:id,legal_name:name,display_name:name,aliases:[],listings:symbols.map(symbol=>({symbol})),listing_status:'listed'});
await test('exact ticker first, shared names retained, multi-class one company',()=>{const cs=[c('a','Acme',['AAA','AAA.B']),c('b','AAA',['BBB']),c('c','Acme',['CCC'])];assert.equal(f.rankCompanies(cs,'AAA')[0].company.company_id,'a');assert.equal(f.rankCompanies(cs,'Acme').length,2);assert.equal(f.rankCompanies(cs,'AAA.B')[0].company.company_id,'a');});
await test('USD 11.6 billion Japanese exact amount and options remain separate',()=>{assert.equal(f.amountText({value:'11600000000.0',currency:'USD',qualifier:'approximately'},'ja'),'約 116億米ドル');assert.match(f.amountText({value:null,max_value:'9000000000',qualifier:'up_to',currency:'USD'},'ja'),/^最大 USD 9,000,000,000$/);});
await test('null and unknown currency not zero',()=>{assert.match(f.amountText({value:null,currency:null},'ja'),/通貨未確認 —/);assert.equal(f.decimalString('9007199254740993'),'9,007,199,254,740,993');});
await test('USD lower bounds use Japanese unit formatting without implying an exact value',()=>{assert.equal(f.amountText({value:null,min_value:'100000000000',max_value:null,qualifier:'more_than',currency:'USD',original_text:'more than $100 billion'},'ja'),'1,000億米ドル超');assert.equal(f.amountText({value:null,min_value:'100000000000',max_value:null,qualifier:'at_least',currency:'USD'},'ja'),'1,000億米ドル以上');});
await test('amount bands configurable, no internal level label',()=>{assert.deepEqual(f.amountBands(['0','100000000','1000000000','10000000000','50000000000'],'en'),['< $100M','$100M–$1B','$1B–$10B','$10B–$50B','$50B+']);});
await test('earnings dates exclude changed, retain unconfirmed and same date',()=>{const co=c('a','Acme',['AAA']);const r=f.nextEarnings(co,[{symbol:'AAA',date:'2026-09-24'},{symbol:'AAA',date:'2026-09-25',status:'changed'},{symbol:'AAA',date:'2026-09-26',status:'unconfirmed',hour:'amc'}],['AAA'],'2026-09-25');assert.equal(r.record.date,'2026-09-26');assert.equal(r.record.status,'unconfirmed');assert.equal(f.dateKey('America/New_York',new Date('2026-09-26T01:00:00Z')),'2026-09-25');assert.equal(f.dateKey('Asia/Tokyo',new Date('2026-09-26T01:00:00Z')),'2026-09-26');});
await test('missing earnings distinct from unlisted and coverage period',()=>{assert.equal(f.nextEarnings({...c('a','Acme'),listing_status:'unlisted'},[],[],'2026-09-25').state,'unlisted');assert.equal(f.nextEarnings(c('a','Acme'),[],[],'2026-09-25').state,'unknownSymbol');assert.equal(f.nextEarnings(c('a','Acme',['AAA']),[],[],'2026-09-25').state,'outsideUniverse');assert.equal(f.nextEarnings(c('a','Acme',['AAA']),[],['AAA'],'2026-09-25').state,'outsidePeriod');});
const template=await readFile(new URL('html_template.py',root),'utf8');
await test('favorite bridge preserves payload and absent handler is safe',()=>{const body=template.match(/function notifyFavorite\(symbol\) \{([\s\S]*?)\n\}/)[1];let payload;for(const window of [{},{webkit:{messageHandlers:{favoriteHandler:{postMessage:x=>payload=x}}}}])vm.runInNewContext('function notifyFavorite(symbol){'+body+'};notifyFavorite("BRK.B")',{window});assert.equal(payload.symbol,'BRK.B');assert.deepEqual(Object.keys(payload),['symbol']);});
await test('calendar map tab preserves favorites and month with the Apple default',()=>{const fn=template.match(/function goToConnections\(destination = 'connections'\) \{([\s\S]*?)\n\}/)[1];const window={location:{href:'https://site.example/app/index.html',search:'?favorites=IBM,NVDA'}};vm.runInNewContext('function goToConnections(destination="connections"){'+fn+'};goToConnections("map")',{window,URL,URLSearchParams,selectedMonth:'2026-10',document:{querySelector:()=>({dataset:{market:'us'}})}});const u=new URL(window.location.href);assert.equal(u.searchParams.get('tab'),'map');assert.equal(u.searchParams.get('company'),'co-aapl');assert.equal(u.searchParams.get('favorites'),'IBM,NVDA');assert.equal(u.searchParams.get('month'),'2026-10');});
const store=new Map();globalThis.localStorage={getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)};
const {DataClient}=await moduleFile('data-client.js');
const hash=async text=>Buffer.from(await crypto.subtle.digest('SHA-256',Buffer.from(text))).toString('hex');
const files=new Map();async function release(id){const manifest={schema_version:'1.0',build_id:id,company_ids:['co-a'],relationship_ids:[],files:{}};for(const [name,extra] of Object.entries({'companies.json':{companies:[c('co-a','Acme')]},'recent_events.json':{events:[],newly_indexed:[],undated:[]},'coverage.json':{coverage:{}},'companies/co-a.json':{company:c('co-a','Acme'),companies:[],relationships:[]}})){let text=JSON.stringify({schema_version:'1.0',build_id:id,...extra});files.set('output_json/relationships/versions/'+id+'/'+name,text);manifest.files[name]=await hash(text);}const text=JSON.stringify(manifest);files.set('output_json/relationships/versions/'+id+'/manifest.json',text);return {build_id:id,manifest:'versions/'+id+'/manifest.json',manifest_hash:await hash(text)};}
let older=await release('old'),newer=await release('new');files.set('output_json/relationships/latest.json',JSON.stringify({...newer,previous:older}));
globalThis.fetch=async path=>({ok:files.has(path),status:files.has(path)?200:404,text:async()=>files.get(path)});
await test('CDN partial new release falls back to complete previous release',async()=>{files.delete('output_json/relationships/versions/new/companies.json');const d=await new DataClient().open();assert.equal(d.manifest.build_id,'old');assert.equal(d.offline,true);assert.equal((await d.company('co-a')).build_id,'old');});
await test('offline cache stays one verified version',async()=>{files.clear();const d=await new DataClient().open();assert.equal(d.offline,true);assert.equal(d.manifest.build_id,'old');assert.equal((await d.company('co-a')).build_id,'old');assert.throws(()=>d.company('../../secret'));});
await test('corrupt cache fails instead of returning empty relationships',async()=>{store.clear();await assert.rejects(()=>new DataClient().open(),/No complete/);});
await test('dense deterministic layout keeps separate node-label areas',()=>{for(const count of [1,30,80,150]){const points=nodePositions(count,1384,594);assert.equal(points.length,count);assert.deepEqual(points[0],{x:0,y:0});assert.deepEqual(points,nodePositions(count,1384,594));for(let a=0;a<count;a++)for(let b=a+1;b<count;b++)assert.ok(Math.abs(points[a].x-points[b].x)>=116||Math.abs(points[a].y-points[b].y)>=98);}});
await test('fractional amounts stay exact and unknown term dates are not invented',()=>{assert.equal(f.amountText({value:'34000000000.5',currency:'USD'},'ja'),'USD 34,000,000,000.5');const text=f.termText({duration_value:7,duration_unit:'year',start_basis:'each_service_schedule_commencement',start_date:null,end_date:null,renewal:null},'ja');assert.equal(text,'7 年 · 各サービスの提供開始日から · 開始日未定 – 終了日未定');});

const {dealRows}=await moduleFile('deals.js');
await test('deal timeline uses publication dates, deduplicates and filters verified summaries',()=>{
 const old={event_id:'old',announced_date:'2025-01-01',detected_at:'2026-09-26',relationship_types:['investment'],statuses:['announced'],amounts:[{value:'1'}]};
 const recent={...old,event_id:'recent',announced_date:'2026-09-20',amounts:[]};
 assert.deepEqual(dealRows({events:[old,recent],newly_indexed:[old]},{}).map(e=>e.event_id),['recent','old']);
 assert.deepEqual(dealRows({timeline:[old,recent]},{amount:true}).map(e=>e.event_id),['old']);
 assert.deepEqual(dealRows({timeline:[old,recent]},{days:'30'},new Date('2026-09-26')).map(e=>e.event_id),['recent']);
 assert.equal(dealRows({timeline:[old]},{type:'supplier'}).length,0);
 assert.equal(dealRows({timeline:[old]},{status:'completed'}).length,0);
});
await test('unknown currency and expected lower bound are visible without becoming USD',()=>{
 const text=f.amountText({value:null,min_value:'30000000000',max_value:null,qualifier:'more_than',currency:null,original_text:'expected to exceed $30 billion'},'ja');
 assert.ok(text.includes('300')&&text.includes('超')&&text.includes('通貨未確認'));assert.ok(!text.includes('米ドル'));
 assert.equal(f.rankCompanies([{...c('apple','Apple',['AAPL']),legal_name:null}],'AAPL')[0].rank,0);
});
await test('edge route bends around an unrelated company on a straight path',async()=>{const {edgeBend}=await moduleFile('layout.js');const a={x:0,y:0},b={x:232,y:0},middle={x:116,y:0};assert.equal(edgeBend(a,b,[a,b]),0);const bend=edgeBend(a,b,[a,b,middle]);assert.ok(Math.abs(bend)/2>37);assert.equal(edgeBend(a,b,[a,b,middle]),bend);});
const network=await moduleFile('network.js');
await test('groups reflect center-relative direction and count unique counterparties',()=>{
 const rows=[{relationship_id:'a',source_company_id:'vendor',target_company_id:'center',relationship_type:'supplier',direction:'directed'},
 {relationship_id:'b',source_company_id:'center',target_company_id:'vendor',relationship_type:'investment',direction:'directed'},
 {relationship_id:'c',source_company_id:'center',target_company_id:'customer',relationship_type:'service_provider',direction:'directed'},
 {relationship_id:'d',source_company_id:'vendor',target_company_id:'other',relationship_type:'partnership',direction:'undirected'}];
 assert.deepEqual(rows.map(r=>network.category(r,'center')),['suppliers','capital','customers','extended']);
 assert.equal(network.counterparties(rows,'center').size,2);
 const groups=network.connectionGroups(rows,'center');assert.equal(groups.find(g=>g.key==='suppliers').counterparties,1);
 assert.equal(rows.filter(r=>!['suppliers','capital'].includes(network.category(r,'center'))).length,2);
});
await test('collapse keeps shared edges from remaining expanded neighborhoods',()=>{
 const shared={relationship_id:'shared'},extra={relationship_id:'extra'};
 const center={companies:[c('center','Center'),c('shared','Shared')],relationships:[shared]};
 const child={companies:[c('child','Child'),c('shared','Shared')],relationships:[shared,extra]};
 assert.equal(network.mergeNeighborhoods([center,child]).relationships.size,2);
 const collapsed=network.mergeNeighborhoods([center]);assert.equal(collapsed.relationships.size,1);assert.ok(collapsed.relationships.has('shared'));assert.ok(!collapsed.companies.has('child'));
});
await test('map entry module parses before browser startup',async()=>{
 execFileSync(process.execPath,['--input-type=module','--check'],{input:await readFile(new URL('assets/relationships/map.js',root),'utf8')});
});
await test('direct fan layout keeps 30 counterparties separated',async()=>{
 const {fanPositions}=await moduleFile('layout.js');
 for(const count of [1,3,25,30]){const points=fanPositions(count,1280,650);assert.equal(points.length,count);assert.deepEqual(points[0],{x:0,y:0});for(let a=0;a<count;a++)for(let b=a+1;b<count;b++)assert.ok(Math.abs(points[a].x-points[b].x)>=116||Math.abs(points[a].y-points[b].y)>=80);}
});
await test('peer edges load immediately and survive collapsing a duplicate expansion',()=>{
 const direct={relationship_id:'c-a',source_company_id:'center',target_company_id:'a'};
 const peer={relationship_id:'a-b',source_company_id:'a',target_company_id:'b'};
 const center={companies:[c('center','Center'),c('a','A'),c('b','B')],relationships:[direct],peer_relationships:[peer]};
 const child={companies:[c('a','A'),c('b','B')],relationships:[peer],peer_relationships:[]};
 for(const payloads of [[center],[center,child]]){
  const merged=network.mergeNeighborhoods(payloads);assert.equal(merged.relationships.size,2);
  assert.equal(network.category(merged.relationships.get('a-b'),'center'),'extended');
  assert.equal(merged.companies.size,3);
 }
});
console.log(`${count} browser-module tests passed`);
