import {latestResults,resultRows} from './earnings-results.js?v=68012a419a70';
import {category,connectionGroups,mergeNeighborhoods,counterparties} from './network.js?v=68012a419a70';
import {dealRows} from './deals.js?v=68012a419a70';
import {graphPositions,edgeBend,edgeLabelPlacement} from './layout.js?v=68012a419a70';
import {DataClient} from './data-client.js?v=68012a419a70';
import {CompanyView} from './company-view.js?v=68012a419a70';
import {queryState,calendarURL,updateURL,safeSourceURL} from './navigation.js?v=68012a419a70';
import {rankCompanies,amountText,dateKey,nextEarnings,amountBands,termText} from './formatters.js?v=68012a419a70';
import {dictionary} from './i18n.js?v=68012a419a70';

let logoPaths={}, detailGeneration=0;
let state=queryState(), client, cy, generation=0, request, selected=null, lastFocus=null, pageSize=30;
let neighborhoods=new Map(), collapsedGroups=new Set();
let mapMode=false;
let expansionHistory=[], selectionVersion=0, selectionOpen=false, quickFilter="", selectionRows=10;
const ux=(ja,en)=>state.lang==='ja'?ja:en;
let layoutCenter=null,layoutKey='',layoutPositions=new Map();
let companies=new Map(), relationships=new Map(), expanded=new Set(), earningsPromise, dealPageSize=20;
const $=id=>document.getElementById(id), t=key=>dictionary[state.lang][key]||key;
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n;};
const button=(text,action,cls='')=>{const b=el('button',text,cls);b.type='button';b.addEventListener('click',action);return b;};
const link=(text,url)=>{const a=el('a',text);a.href=url;return a;};
const connectionColors={supply:'#29b6f6',partnership:'#2ecc91',capital:'#b678f0',group:'#9aa9bd',mixed:'#f5a742'};
const connectionKind=r=>({supplier:'supply',service_provider:'supply',partnership:'partnership',investment:'capital',acquisition:'capital',equity_right:'capital',subsidiary:'group',group_member:'group'}[r.relationship_type]||'group');
const connectionTypeLabel=key=>({supply:ux('供給・サービス','Supply / services'),partnership:ux('提携','Partnership'),capital:ux('出資・買収','Investment / acquisition'),group:ux('グループ関係','Group relationships'),mixed:ux('複数種類の関係','Mixed relationship types')}[key]);
const connectionColor=rows=>{const kinds=new Set(rows.map(connectionKind));return connectionColors[kinds.size===1?[...kinds][0]:'mixed'];};
const bands=()=>amountBands(client?.manifest.tiers.USD.minimums||['0','100000000','1000000000','10000000000','50000000000'],state.lang);
const logo=c=>logoPaths[c?.company_id]||c?.listings.map(l=>logoPaths[l.symbol]).find(Boolean)||'';
const name=id=>{const key=client?.canonicalId(id)||id;return companies.get(key)?.display_name || client?.companies.find(c=>c.company_id===key)?.display_name || id;};
function message(text,error=false){$('mtz-message').textContent=text;$('mtz-message').className=error?'notice error':'notice';}
function shell(){
  $('mtz-map-app').innerHTML=`
    ${$('mtz-shared-header').innerHTML}<div class="mtz-header"><span id="mtz-market" class="muted"></span><nav class="mtz-feature"><a id="mtz-calendar"></a><a id="mtz-connections" href="map.html" aria-current="page"></a><button id="mtz-deals" type="button"></button></nav><button id="mtz-lang" type="button"></button></div>
    <section class="mtz-controls" aria-label="Search and filters"><div class="mtz-search"><label id="mtz-search-label" for="mtz-search"></label><input id="mtz-search" type="search" autocomplete="off" maxlength="120" aria-controls="mtz-results"><div id="mtz-results"></div></div><label><span id="mtz-type-label"></span><select id="mtz-type"></select></label><label><span id="mtz-status-label"></span><select id="mtz-status"></select></label><label><span id="mtz-date-label"></span><select id="mtz-days"></select></label><label class="check"><input id="mtz-amount" type="checkbox"><span id="mtz-amount-label"></span></label></section>
    <p id="mtz-message" class="notice" role="status" aria-live="polite"></p>
    <section id="mtz-intro" class="mtz-intro"><p id="mtz-pilot" class="eyebrow"></p><h1 id="mtz-heading"></h1><p id="mtz-start"></p><p id="mtz-discovery" class="muted"></p><div id="mtz-quick-start" class="mtz-quick-start"></div><div id="mtz-favorites"></div><div id="mtz-updates"></div></section>
    <section id="mtz-workspace" class="mtz-workspace" hidden><div class="mtz-toolbar"><div class="mtz-company-heading"><h1 id="mtz-company-name"></h1><span id="mtz-source-period" class="muted"></span></div><div class="mtz-view"><button id="mtz-map-view" type="button"></button><button id="mtz-list-view" type="button"></button></div><button id="mtz-map-mode" type="button" aria-pressed="false" aria-controls="mtz-workspace"></button><button id="mtz-expand" type="button"></button><button id="mtz-cancel" type="button" hidden></button></div><label id="mtz-peer-control" class="check mtz-peer-control"><input id="mtz-peer-labels" type="checkbox"><span id="mtz-peer-labels-text"></span></label><nav id="mtz-groups" class="mtz-groups" aria-label="Connection groups"></nav><div class="mtz-graph-wrap"><nav id="mtz-map-tools" class="mtz-map-tools" aria-label="Map filters"></nav><aside id="mtz-selection" class="mtz-selection" aria-label="Selected company" hidden></aside><div id="mtz-graph" role="img" aria-label="Company connections graph; equivalent information is available in List"></div><button id="mtz-exit-map-mode" class="mtz-exit-map-mode" type="button" hidden></button><div class="mtz-map-bottom"><div id="mtz-legend" aria-label="Relationship colors" tabindex="0"></div><div id="mtz-zoom" class="mtz-zoom"><button id="mtz-minus" type="button">−</button><button id="mtz-plus" type="button">+</button><button id="mtz-reset" type="button"></button></div></div></div><div id="mtz-list" hidden></div></section>
    <footer class="mtz-footer"><button id="mtz-coverage" type="button"></button><span id="mtz-version" class="muted"></span></footer>
    <aside id="mtz-detail" class="mtz-detail" role="dialog" aria-labelledby="mtz-detail-title" tabindex="-1" hidden><button id="mtz-close" type="button"></button><div id="mtz-detail-content"></div></aside>`;
  $('mtz-lang').onclick=()=>{state.lang=state.lang==='en'?'ja':'en';updateURL(state);translate();if(client){renderIntro();render();}closeDetail();};
  $('mtz-deals').onclick=()=>{generation++;request?.abort();state.company=null;state.symbol='';state.relation=null;state.q='';$('mtz-search').value='';$('mtz-results').replaceChildren();companies.clear();relationships.clear();closeDetail();updateURL(state,true);message('');renderIntro();render();};
  $('mtz-search').addEventListener('input',search);
  $('mtz-search').addEventListener('keydown',e=>{if(e.key==='ArrowDown')$('mtz-results').querySelector('button')?.focus();});
  for(const [id,key] of [['mtz-type','type'],['mtz-status','status'],['mtz-days','days'],['mtz-amount','amount']])$(id).addEventListener('change',()=>{state[key]=key==='amount'?$(id).checked:$(id).value;pageSize=30;dealPageSize=20;updateURL(state,true);renderIntro();render();});
  $('mtz-map-view').onclick=()=>setView('map');$('mtz-list-view').onclick=()=>setView('list');
  $('mtz-plus').onclick=()=>cy?.zoom({level:Math.min(3,cy.zoom()*1.3),renderedPosition:{x:cy.width()/2,y:cy.height()/2}});
  $('mtz-minus').onclick=()=>cy?.zoom({level:Math.max(.15,cy.zoom()/1.3),renderedPosition:{x:cy.width()/2,y:cy.height()/2}});
  $('mtz-reset').onclick=fitView;
  $('mtz-map-mode').onclick=()=>setMapMode(true);
  $('mtz-exit-map-mode').onclick=()=>setMapMode(false);
  $('mtz-peer-labels').addEventListener('change',updatePeerLabels);
  $('mtz-expand').onclick=()=>expandCompany(selected||state.company);$('mtz-cancel').onclick=()=>{generation++;request?.abort();$('mtz-cancel').hidden=true;message('');};
  $('mtz-close').onclick=closeDetail;$('mtz-coverage').onclick=showCoverage;
  document.addEventListener('keydown',e=>{if(e.key==='Escape'){if(!$('mtz-detail').hidden)closeDetail();else if(selectionOpen){selectionOpen=false;selectionVersion++;$('mtz-selection').hidden=true;}else if(mapMode)setMapMode(false);$('mtz-results').replaceChildren();}if(e.key==='Tab'&&!$('mtz-detail').hidden&&matchMedia('(max-width: 760px)').matches){const nodes=[...$('mtz-detail').querySelectorAll('a[href],button:not([disabled]),input,select')];const first=nodes[0],last=nodes.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus();}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus();}}});
  addEventListener('popstate',()=>{state=queryState();translate();if(state.company&&client?.manifest.company_ids.includes(state.company))choose(state.company,false);else{companies.clear();relationships.clear();renderIntro();render();}});
  matchMedia('(max-width: 760px)').addEventListener('change',()=>{if(!$('mtz-detail').hidden)syncDetailLayout();cy?.resize();});
  let resizeFrame;addEventListener('resize',()=>{cancelAnimationFrame(resizeFrame);resizeFrame=requestAnimationFrame(()=>{if(client&&state.view==='map')render();});});
  translate();
}
function translate(){
  document.documentElement.lang=state.lang;
  document.querySelector('.header-title').textContent=t('title');document.title=t('title')+' — Market Time Zen';
  const texts={'mtz-deals':'deals','mtz-market':'us','mtz-calendar':'calendar','mtz-connections':'connections','mtz-heading':'noCompany','mtz-start':'start','mtz-discovery':'discovery','mtz-search-label':'search','mtz-type-label':'all','mtz-status-label':'allStatus','mtz-date-label':'recent','mtz-amount-label':'amountOnly','mtz-map-view':'map','mtz-list-view':'list','mtz-expand':'expand','mtz-cancel':'cancel','mtz-reset':'reset','mtz-map-mode':'mapMode','mtz-exit-map-mode':'exitMapMode','mtz-peer-labels-text':'peerLabels','mtz-close':'close','mtz-coverage':'coverage'};
  for(const [id,key] of Object.entries(texts))$(id).textContent=t(key);
  $('mtz-market').textContent=t('us')+' · '+t('universe_'+(client?.coverage.universe||'pilot'));
  $('mtz-calendar').href=calendarURL(state);$('mtz-lang').textContent=state.lang==='en'?'日本語':'English';$('mtz-lang').lang=state.lang==='en'?'ja':'en';
  $('mtz-search').placeholder=t('search');$('mtz-plus').setAttribute('aria-label',t('zoomIn'));$('mtz-minus').setAttribute('aria-label',t('zoomOut'));
  function options(id,rows,value){$(id).replaceChildren(...rows.map(([v,label])=>{const o=el('option',label);o.value=v;return o;}));$(id).value=value;}
  options('mtz-type',[['',t('all')],...['service_provider','supplier','partnership','investment','acquisition','subsidiary','group_member','equity_right'].map(k=>[k,t(k)])],state.type);
  options('mtz-status',[['',t('allStatus')],...['announced','signed','active','completed','terminated','historical','unknown'].map(k=>[k,t(k)])],state.status);
  options('mtz-days',[['',t('anyDate')],['30',state.lang==='ja'?'30日以内':'Past 30 days'],['90',state.lang==='ja'?'90日以内':'Past 90 days'],['365',state.lang==='ja'?'1年以内':'Past year']],state.days);
  $('mtz-amount').checked=state.amount;
  const legend=$('mtz-legend');legend.replaceChildren(el('strong',ux('関係の種類','Relationship types')));
  for(const [key,color] of Object.entries(connectionColors)){const span=el('span',connectionTypeLabel(key),'mtz-band');span.style.setProperty('--band-color',color);legend.append(span);}

}
function fitView(){if(!cy)return;cy.resize();cy.fit(undefined,45);if(cy.zoom()>1.25){cy.zoom(1.25);cy.center();}}
function rememberPositions(){
  if(cy&&layoutCenter===state.company)cy.nodes().forEach(n=>layoutPositions.set(n.id(),{...n.position()}));
}
function rerouteEdges(){
  if(!cy)return;
  rememberPositions();
  const positions=cy.nodes().map(n=>n.position()),byId=new Map(cy.nodes().map((n,i)=>[n.id(),positions[i]]));
  cy.batch(()=>cy.edges().forEach(edge=>{
    const a=byId.get(edge.source().id()),b=byId.get(edge.target().id());
    edge.data({bend:edgeBend(a,b,positions),...edgeLabelPlacement(a,b)});
  }));
}
// Selection belongs to the company, so rebuilding the graph keeps its emphasis.
function highlightCompany(){
  if(!cy)return;
  cy.batch(()=>{
    cy.elements().removeClass('company-focus connection-focus');
    const node=selected?cy.getElementById(selected):cy.collection();
    if(!node.length)return;
    const edges=node.connectedEdges();
    node.addClass('company-focus');
    edges.addClass('connection-focus');
  });
}
function updatePeerLabels(){
  if(!cy)return;
  const show=$('mtz-peer-labels').checked;
  cy.batch(()=>{const peers=cy.edges('[?peer]');peers.toggleClass('peer-info',show);peers.toggleClass('peer-info-hidden',!show);});
}
function setMapMode(enabled,restoreFocus=true){
  enabled=enabled&&state.view==='map'&&!!state.company;
  if(mapMode===enabled)return;
  const graph=cy,zoom=graph?.zoom(),pan=graph?.pan();
  const center=graph?{x:(graph.width()/2-pan.x)/zoom,y:(graph.height()/2-pan.y)/zoom}:null;
  mapMode=enabled;
  document.body.classList.toggle('map-mode',enabled);
  $('mtz-map-mode').setAttribute('aria-pressed',String(enabled));
  $('mtz-exit-map-mode').hidden=!enabled;
  requestAnimationFrame(()=>{
    if(graph&&cy===graph){graph.resize();graph.pan({x:graph.width()/2-center.x*zoom,y:graph.height()/2-center.y*zoom});}
    if(restoreFocus&&$('mtz-detail').hidden)(enabled?$('mtz-exit-map-mode'):$('mtz-map-mode')).focus({preventScroll:true});
  });
}
function setView(view){if(view!=='map')setMapMode(false,false);state.view=view;updateURL(state,true);render();}
function search(){
  const q=$('mtz-search').value;state.q=q;const matches=client?rankCompanies(client.companies,q):[];$('mtz-results').replaceChildren();
  if(!q)return;
  matches.slice(0,20).forEach(({company:c})=>{$('mtz-results').append(button(c.display_name+' · '+(c.listings.map(l=>l.symbol+(l.exchange?' ('+l.exchange+')':'')).join(', ')||t('unknownSymbol'))+' · '+(c.country||'—'),()=>choose(c.company_id),'search-result'));});
  if(!matches.length)$('mtz-results').append(el('p',t('searchEmpty')));
}
async function choose(cid,push=true){
  cid=client.canonicalId(cid);
  detailGeneration++;const seq=++generation;request?.abort();request=new AbortController();message(t('loading'));
  try{const data=await client.company(cid,request.signal);if(seq!==generation)return;
    state.company=cid;state.symbol='';state.q='';selected=cid;pageSize=30;expansionHistory=[];selectionOpen=false;selectionVersion++;
    ({companies,relationships}=mergeNeighborhoods([data]));expanded=new Set([cid]);neighborhoods=new Map([[cid,data]]);collapsedGroups.clear();
    $('mtz-search').value='';$('mtz-results').replaceChildren();closeDetail();updateURL(state,push);render();message(client.offline?t('offline'):'');
  }catch(e){if(e.name!=='AbortError'&&seq===generation){message(t('failed'),true);}}
}
async function expandCompany(cid){
  if(!cid)return;
  const seq=++generation;request?.abort();request=new AbortController();$('mtz-cancel').hidden=false;message(t('loading'));
  try{
    if(expanded.has(cid)){message(ux('この企業のつながりは展開済みです。別の企業を選択してください。','Already expanded. Select another company.'));return;}
    const ids=[cid];
    const pending=await Promise.all(ids.map(id=>client.company(id,request.signal)));if(seq!==generation)return;
    rememberPositions();expansionHistory.push({neighborhoods:new Map(neighborhoods),expanded:new Set(expanded),positions:new Map(layoutPositions)});
    for(const d of pending){neighborhoods.set(d.company.company_id,d);expanded.add(d.company.company_id);}
    ({companies,relationships}=mergeNeighborhoods(neighborhoods.values()));
    render();message(client.offline?t('offline'):'');
  }catch(e){if(e.name!=='AbortError'&&seq===generation)message(t('failed'),true);}finally{if(seq===generation)$('mtz-cancel').hidden=true;}
}
function collapseCompany(cid){
  if(cid===state.company)return;
  generation++;request?.abort();$('mtz-cancel').hidden=true;
  neighborhoods.delete(cid);expanded.delete(cid);
  ({companies,relationships}=mergeNeighborhoods(neighborhoods.values()));selected=state.company;render();
}
function ratingText(r){return r?.tier ? bands()[r.tier.level-1] : (r?.tier_reasons||['unrated']).map(k=>t('reason_'+k)===('reason_'+k)?t(k):t('reason_'+k)).join(' / ');}
// A connection line needs a business description, not just its taxonomy label.
const specificEdgeLabels={ja:{
  'rel-05c6587da4c523af5144b983':'Appleの米国製造プログラムに参加',
  'rel-0861e56024d9a66f3441f259':'Red Hatを買収',
  'rel-0b750bf7554cd2d1815b7904':'OpenAIへ出資',
  'rel-0e337fd63bd6d4f505d87843':'Appleの米国製造プログラムに参加',
  'rel-13a995805e1bac42cbeedcee':'AI技術・モデル最適化で協業',
  'rel-1f2e6eb551148eaeb1566cf1':'希土類磁石を供給・リサイクル',
  'rel-3184bf461ce38af0e098a4cb':'Apple向け半導体を製造',
  'rel-33284e76c221eecfec8e07a':'Apple製品用ICの製造で協業',
  'rel-3fc8d84d62525ec9ac1cff88':'Appleの米国製造プログラムに参加',
  'rel-52db33727c36dae4a1c9db96':'Appleの米国製造プログラムに参加',
  'rel-6c91d437575935bb6dd80400':'PinterestがAWSクラウドを利用',
  'rel-6d961c24ce89eaf990cbc1ce':'既存の提携を拡大',
  'rel-74cf17dc8e20aa93c0b1891d':'OpenAIへ追加出資',
  'rel-7893e3b8d0047339117cae8a':'カスタムASIC等を開発・供給',
  'rel-7a6a372adb37f5efe5570d73':'Appleの米国製造プログラムに参加',
  'rel-8f428b09a0e367a1851af394':'Appleの米国製造プログラムに参加',
  'rel-9be2cf84ad4c9c15185a1e63':'AIアクセラレーターを共同開発',
  'rel-ad97c4534214e19743408c3b':'半導体プロセス・混合信号技術で協業',
  'rel-d3082b9214c6b6945d6fadca':'OpenAI向けAI計算基盤を提供',
  'rel-e2898651f9dce1b13e467dc0':'Appleの米国製造プログラムに参加',
  'rel-f4780b88ad8c09b931cf235a':'Appleの米国製造プログラムに参加',
},en:{
  'rel-05c6587da4c523af5144b983':'Participates in Apple’s U.S. manufacturing program',
  'rel-0861e56024d9a66f3441f259':'IBM acquired Red Hat',
  'rel-0b750bf7554cd2d1815b7904':'Investment in OpenAI',
  'rel-0e337fd63bd6d4f505d87843':'Participates in Apple’s U.S. manufacturing program',
  'rel-13a995805e1bac42cbeedcee':'AI engineering and model optimization',
  'rel-1f2e6eb551148eaeb1566cf1':'Rare-earth magnet supply and recycling',
  'rel-3184bf461ce38af0e098a4cb':'Manufactures semiconductors for Apple',
  'rel-33284e76c221eecfec8e07a':'Develops ICs for Apple product sensors',
  'rel-3fc8d84d62525ec9ac1cff88':'Participates in Apple’s U.S. manufacturing program',
  'rel-52db33727c36dae4a1c9db96':'Participates in Apple’s U.S. manufacturing program',
  'rel-6c91d437575935bb6dd80400':'Pinterest uses AWS cloud services',
  'rel-6d961c24ce89eaf990cbc1ce':'Expands existing partnership',
  'rel-74cf17dc8e20aa93c0b1891d':'Additional investment in OpenAI',
  'rel-7893e3b8d0047339117cae8a':'Develops and supplies custom ASICs',
  'rel-7a6a372adb37f5efe5570d73':'Participates in Apple’s U.S. manufacturing program',
  'rel-8f428b09a0e367a1851af394':'Participates in Apple’s U.S. manufacturing program',
  'rel-9be2cf84ad4c9c15185a1e63':'Jointly develops AI accelerators',
  'rel-ad97c4534214e19743408c3b':'Semiconductor process and mixed-signal collaboration',
  'rel-d3082b9214c6b6945d6fadca':'Provides AI compute infrastructure to OpenAI',
  'rel-e2898651f9dce1b13e467dc0':'Participates in Apple’s U.S. manufacturing program',
  'rel-f4780b88ad9c09b931cf235a':'Participates in Apple’s U.S. manufacturing program',
}};
function connectionLabel(row){
  const headline=row.business?.headline?.trim();
  if(headline&&headline!==t(row.relationship_type))return headline;
  const curated=specificEdgeLabels[state.lang]?.[row.relationship_id];
  if(curated)return curated;
  const description=(row.description||'').replace(/\s+/g,' ').trim();
  if(description)return description.split(/(?<=[。.!?])\s*/u,1)[0];
  return t(row.relationship_type)+' · '+name(row.source_company_id)+' / '+name(row.target_company_id);
}
function relationCard(r){
  const row=button('',()=>showRelation(r.relationship_id),'mtz-relation-row');
  row.style.setProperty('--edge-color',connectionColor([r]));
  row.append(el('strong',name(r.source_company_id)+(r.direction==='directed'?' → ':' — ')+name(r.target_company_id)));
  if(r.business?.headline)row.append(el('span',r.business.headline,'mtz-relation-headline'));
  if(r.description)row.append(el('span',r.description,'mtz-relation-description'));
  row.append(el('span',t(r.relationship_type)+' · '+t(r.lifecycle_status)+' · '+(r.status_as_of||'—'),'muted'));
  row.append(el('span',r.amounts?.length?r.amounts.map(a=>amountText(a,state.lang)+' · '+t(a.value_semantics)).join(' / '):t('unknownAmount')));
  row.append(el('span',ux('金額の分類', 'Amount classification')+': '+ratingText(r),'mtz-rating-note'));
  return row;
}
function filtered(){
  const cutoff=state.days?new Date(Date.now()-Number(state.days)*86400000).toISOString().slice(0,10):null;
  return [...relationships.values()].filter(r=>(!state.type||r.relationship_type===state.type)&&(!state.status||r.lifecycle_status===state.status)&&(!state.amount||r.has_amount)&&(!cutoff||r.event_date&&r.event_date>=cutoff)).filter(r=>matchesQuickFilter(r)).sort((a,b)=>(b.event_date||'').localeCompare(a.event_date||'')||a.relationship_id.localeCompare(b.relationship_id));
}
function render(){
  const active=!!state.company&&companies.has(state.company);$('mtz-intro').hidden=active;$('mtz-workspace').hidden=!active;
  if(!active||state.view!=='map')setMapMode(false,false);
  $('mtz-map-mode').hidden=state.view!=='map';
  if(!active){selectionOpen=false;$('mtz-selection').hidden=true;cy?.destroy();cy=null;return;}
  renderMapTools();
  $('mtz-company-name').textContent=name(state.company);$('mtz-company-name').onclick=()=>selectCompany(state.company);
  $('mtz-company-name').tabIndex=0;$('mtz-company-name').onkeydown=e=>{if(e.key==='Enter')selectCompany(state.company);};
  const all=filtered(), categories=connectionGroups(all,state.company);
  $('mtz-groups').replaceChildren(...categories.map(g=>{
    const hidden=collapsedGroups.has(g.key), b=button((hidden?'+ ':'− ')+t('group_'+g.key)+' · '+g.counterparties+' '+t('companies'),()=>{
      hidden?collapsedGroups.delete(g.key):collapsedGroups.add(g.key);render();
    });b.setAttribute('aria-expanded',String(!hidden));return b;
  }));
  const rels=all.filter(r=>!collapsedGroups.has(category(r,state.company)));if(rels.length&&[t('empty'),t('collapsedEmpty')].includes($('mtz-message').textContent))message('');const relevant=new Set([state.company,...rels.flatMap(r=>[r.source_company_id,r.target_company_id])]);
  const direct=counterparties(neighborhoods.get(state.company)?.relationships||[],state.company);
  const updated=id=>rels.filter(r=>[r.source_company_id,r.target_company_id].includes(id)).reduce((v,r)=>r.last_observed_at>v?r.last_observed_at:v,'');
  const fav=id=>companies.get(id)?.listings.some(l=>state.favorites.includes(l.symbol));
  const ordered=[state.company,...[...relevant].filter(id=>id!==state.company).sort((a,b)=>Number(direct.has(b))-Number(direct.has(a))||Number(fav(b))-Number(fav(a))||updated(b).localeCompare(updated(a))||name(a).localeCompare(name(b)))];
  const cap=expanded.size>1?client.manifest.expanded_nodes:client.manifest.initial_nodes;const shown=ordered.slice(0,cap), visible=new Set(shown);
  const visibleRows=rels.filter(r=>visible.has(r.source_company_id)&&visible.has(r.target_company_id));
  const dates=visibleRows.map(r=>r.status_as_of).filter(Boolean).sort();
  const peerCount=visibleRows.filter(r=>category(r,state.company)==='extended').length;
  $('mtz-source-period').textContent=dates.length?t('sourcePeriod')+': '+dates[0]+' — '+dates.at(-1):'';
  $('mtz-peer-control').hidden=state.view!=='map';
  $('mtz-map-view').setAttribute('aria-pressed',state.view==='map');$('mtz-list-view').setAttribute('aria-pressed',state.view==='list');
  document.querySelector('.mtz-graph-wrap').hidden=state.view==='list';$('mtz-list').hidden=state.view!=='list';
  $('mtz-list').replaceChildren();
  if(!rels.length){const empty=t(all.length?'collapsedEmpty':'empty');$('mtz-list').append(el('p',empty));message(empty);}
  rels.slice(0,pageSize).forEach(r=>$('mtz-list').append(relationCard(r)));
  if(rels.length>pageSize)$('mtz-list').append(button(t('more'),()=>{pageSize+=30;render();}));
  if(state.view==='list')return;
  if(!window.cytoscape){message(t('failed'),true);state.view='list';render();return;}
  const begin=performance.now();
  // Rebuilding an existing neighborhood must not reset the user's viewport.
  const viewport=cy&&layoutCenter===state.company?{zoom:cy.zoom(),pan:{...cy.pan()}}:null;
  rememberPositions();
  if(layoutCenter!==state.company){layoutPositions=new Map();layoutKey='';layoutCenter=state.company;}
  const topology=[...new Set(visibleRows.map(r=>[r.source_company_id,r.target_company_id].sort().join('|')))].sort();
  const nextLayoutKey=JSON.stringify([[...shown].sort(),topology]);
  const positions=layoutKey===nextLayoutKey&&shown.every(id=>layoutPositions.has(id))
    ?shown.map(id=>({...layoutPositions.get(id)}))
    :graphPositions(shown,visibleRows,$('mtz-graph').clientWidth,$('mtz-graph').clientHeight,state.company,layoutPositions);
  layoutKey=nextLayoutKey;shown.forEach((id,i)=>layoutPositions.set(id,{...positions[i]}));
  const nodes=shown.map((id,i)=>({data:{id,label:name(id),favorite:!!fav(id),logo:logo(companies.get(id)),center:id===state.company},position:positions[i]}));
  const positionById=new Map(shown.map((id,i)=>[id,positions[i]]));
  const groups=new Map();for(const r of rels){if(!visible.has(r.source_company_id)||!visible.has(r.target_company_id))continue;const pair=[r.source_company_id,r.target_company_id].sort().join('|');if(!groups.has(pair))groups.set(pair,[]);groups.get(pair).push(r);}
  const edges=[...groups.values()].map((rows,i)=>{const r=rows[0],multi=rows.length>1;const directed=rows.filter(row=>row.direction==='directed');const forward=directed.some(row=>row.source_company_id===r.source_company_id),reverse=directed.some(row=>row.source_company_id===r.target_company_id);const a=positionById.get(r.source_company_id),b=positionById.get(r.target_company_id);return {data:{id:'edge-'+i,source:r.source_company_id,target:r.target_company_id,relations:rows.map(r=>r.relationship_id),color:connectionColor(rows),bend:edgeBend(a,b,positions),line:multi?'dashed':({partnership:'dashed',equity_right:'dotted',investment:'dashed',group_member:'dotted'}[r.relationship_type]||'solid'),arrow:forward?'triangle':'none',sourceArrow:reverse?'triangle':'none',label:(multi?`${rows.length} ${t('relations')} · ${[...new Set(rows.map(connectionLabel))].join(' / ')}`:connectionLabel(r)).replace(/\s+/g,' ').trim(),rated:!multi&&!!r.tier,multiple:multi,peer:category(r,state.company)==='extended',...edgeLabelPlacement(a,b)}};});
  cy?.destroy();
  cy=window.cytoscape({container:$('mtz-graph'),elements:[...nodes,...edges],...(viewport||{}),layout:{name:'preset',fit:!viewport,padding:50},minZoom:.15,maxZoom:3,motionBlur:false,style:[{selector:'node',style:{'shape':'round-rectangle','width':58,'height':58,'background-color':'#eaf0f7','border-width':1,'border-color':'#cad5e4','label':'data(label)','font-family':'-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif','font-size':14,'text-wrap':'wrap','text-max-width':105,'text-valign':'bottom','text-margin-y':9,'color':'#243147'}},{selector:'node[logo != ""]',style:{'background-image':'data(logo)','background-fit':'contain','background-width':'100%','background-height':'100%'}},{selector:'node[logo = ""]',style:{'width':92,'height':48,'text-valign':'center','text-margin-y':0,'text-max-width':86,'background-color':'#f8fafc'}},{selector:'node[?center]',style:{'background-color':'#eff3f9'}},{selector:'node[?favorite]',style:{'border-width':3,'border-color':'#c49a24'}},{selector:'edge',style:{'width':1.8,'curve-style':'unbundled-bezier','control-point-distances':'data(bend)','control-point-weights':.5,'line-color':'data(color)','target-arrow-color':'data(color)','target-arrow-shape':'data(arrow)','source-arrow-color':'data(color)','source-arrow-shape':'data(sourceArrow)','line-style':'data(line)','arrow-scale':1.4,'source-distance-from-node':16,'target-distance-from-node':16,'text-margin-x':'data(labelX)','text-margin-y':'data(labelY)','opacity':1}},{selector:'edge[?peer]',style:{'width':1.4}},{selector:'edge[?multiple]',style:{'label':'','text-margin-x':'data(labelX)','text-margin-y':'data(labelY)','font-size':10,'text-background-color':'white','text-background-opacity':1,'text-background-padding':'3px'}},{selector:'edge:selected, edge.inspect, edge.connection-focus, edge.peer-info',style:{'label':'data(label)','text-wrap':'ellipsis','text-max-width':'data(labelWidth)','font-size':12,'text-background-color':'white','text-background-opacity':1,'text-background-padding':'4px','color':'#243147','opacity':1}},{selector:'edge.peer-info-hidden',style:{'label':''}},{selector:'edge.peer-info-hidden.inspect, edge.peer-info-hidden.connection-focus',style:{'label':'data(label)'}},{selector:'node.company-focus',style:{'border-width':0,'underlay-color':'#68cfff','underlay-opacity':.24,'underlay-padding':10,'underlay-shape':'round-rectangle','underlay-corner-radius':16,'font-weight':700}},{selector:'edge.connection-focus',style:{'opacity':1,'z-index':10}},{selector:'edge.connection-focus[?multiple]',style:{'line-color':'#edacc4','target-arrow-color':'#edacc4','source-arrow-color':'#edacc4'}}]});
  if(!viewport&&cy.zoom()>1.25){cy.zoom(1.25);cy.center();}
  cy.on('mouseover','edge',e=>{e.target.addClass('inspect');markSelectionRows(e.target.data('relations'),true);});cy.on('mouseout','edge',e=>{e.target.removeClass('inspect');markSelectionRows(e.target.data('relations'),false);});
  cy.on('tap','node',e=>selectCompany(e.target.id()));
  cy.on('dragfree','node',rerouteEdges);
  cy.on('tap','edge',e=>{const ids=e.target.data('relations');if(ids.length===1)showRelation(ids[0]);else{detailGeneration++;openDetail(t('details'));$('mtz-detail-content').append(el('p',t('aggregateReason'),'notice'));for(const id of ids){const r=relationships.get(id);$('mtz-detail-content').append(relationCard(r));}}});
  cy.on('tap',e=>{if(e.target===cy){selected=null;selectionOpen=false;selectionVersion++;$('mtz-selection').hidden=true;highlightCompany();if(['suppliers','customers'].includes(quickFilter))render();}});
  highlightCompany();
  updatePeerLabels();
  cy.style().selector('edge').style({'min-zoomed-font-size':10}).selector('node').style({'min-zoomed-font-size':9}).update();
  if(selectionOpen)renderSelection();
  $('mtz-graph').dataset.renderMs=(performance.now()-begin).toFixed(2);$('mtz-graph').dataset.nodes=String(nodes.length);$('mtz-graph').dataset.peerRelationships=String(peerCount);$('mtz-graph').dataset.edges=String(edges.length);
  const rendered=cy;requestAnimationFrame(()=>requestAnimationFrame(()=>{if(cy===rendered)$('mtz-graph').dataset.frameMs=(performance.now()-begin).toFixed(2);}));
}
function matchesQuickFilter(r){
  if(!quickFilter)return true;
  if(quickFilter==='recent')return r.event_date>=new Date(Date.now()-90*86400000).toISOString().slice(0,10);
  if(quickFilter==='amount')return r.has_amount;
  if(quickFilter==='capital')return ['investment','acquisition','equity_right'].includes(r.relationship_type);
  if(quickFilter==='partnership')return r.relationship_type==='partnership';
  return category(r,selected||state.company)===quickFilter;
}
function renderMapTools(){
  const tools=$('mtz-map-tools');tools.replaceChildren();
  const filter=el('select');filter.setAttribute('aria-label',ux('取引を絞り込む','Filter connections'));
  for(const [value,ja,en] of [['','すべての取引','All connections'],['recent','公表90日以内','Announced in 90 days'],['amount','金額あり','Amount disclosed'],['suppliers','選択企業の供給元','Selected company suppliers'],['customers','選択企業の顧客','Selected company customers'],['partnership','提携','Partnerships'],['capital','出資・買収','Investments / acquisitions']]){const o=el('option',ux(ja,en));o.value=value;filter.append(o);}
  filter.value=quickFilter;filter.onchange=()=>{quickFilter=filter.value;render();};tools.append(filter);
  const undo=button(ux('つながりの展開を戻す','Undo expansion'),()=>{
    const previous=expansionHistory.pop();if(!previous)return;
    generation++;request?.abort();$('mtz-cancel').hidden=true;message('');
    neighborhoods=previous.neighborhoods;expanded=previous.expanded;
    ({companies,relationships}=mergeNeighborhoods(neighborhoods.values()));
    if(!companies.has(selected))selected=state.company;
    render();
    cy?.nodes().forEach(n=>{const p=previous.positions.get(n.id());if(p)n.position(p);});rerouteEdges();
  });undo.disabled=!expansionHistory.length;tools.append(undo);
}
function selectCompany(cid){
  if(state.view!=='map'){showCompany(cid);return;}
  closeDetail();selected=client.canonicalId(cid);selectionOpen=true;selectionRows=10;
  highlightCompany();
  if(['suppliers','customers'].includes(quickFilter))render();else renderSelection();
}
function markSelectionRows(ids,active){
  $('mtz-selection').querySelectorAll('[data-relation-id]').forEach(row=>{if(ids.includes(row.dataset.relationId))row.classList.toggle('is-inspected',active);});
}
function inspectRelation(id,active){
  cy?.edges().filter(edge=>edge.data('relations').includes(id)).toggleClass('inspect',active);
}
async function renderSelection(){
  const version=++selectionVersion,cid=selected,panel=$('mtz-selection');
  panel.hidden=!selectionOpen||!cid;if(panel.hidden)return;
  const c=companies.get(cid);if(!c){panel.hidden=true;return;}
  const wasOpen=panel.querySelector('details')?.open;
  panel.replaceChildren();
  const heading=el('div',undefined,'mtz-selection-heading');
  if(logo(c)){const img=el('img');img.src=logo(c);img.alt='';heading.append(img);}
  const title=el('div');title.append(el('strong',name(cid)),el('small',c.listings.map(l=>l.symbol).join(' · ')));heading.append(title);
  heading.append(button('×',()=>{selectionOpen=false;selectionVersion++;panel.hidden=true;}));heading.lastChild.setAttribute('aria-label',t('close'));panel.append(heading);
  const actions=el('div',undefined,'mtz-selection-actions');
  const expand=button(t('loading'),()=>expandCompany(cid));expand.disabled=true;expand.classList.add('primary');
  actions.append(expand,button(ux('詳細・決算','Details / earnings'),()=>showCompany(cid)),button(t('center'),()=>choose(cid)));panel.append(actions);
  const rows=filtered().filter(r=>[r.source_company_id,r.target_company_id].includes(cid));
  const details=el('details'),summary=el('summary',ux(`取引一覧（${rows.length}件）`,`Connections (${rows.length})`));
  details.open=wasOpen??!matchMedia('(max-width: 760px)').matches;details.append(summary);
  const list=el('div',undefined,'mtz-selection-list');
  for(const r of rows.slice(0,selectionRows)){
    const row=button('',()=>showRelation(r.relationship_id),'mtz-selection-row');row.dataset.relationId=r.relationship_id;row.style.setProperty('--edge-color',connectionColor([r]));
    row.append(el('strong',name(r.source_company_id===cid?r.target_company_id:r.source_company_id)),el('span',connectionLabel(r)),el('small',r.amounts?.length?r.amounts.map(a=>amountText(a,state.lang)+' · '+t(a.value_semantics)).join(' / '):t('unknownAmount')),el('small',r.event_date||'—'));
    row.onmouseenter=()=>inspectRelation(r.relationship_id,true);row.onmouseleave=()=>inspectRelation(r.relationship_id,false);
    row.onfocus=()=>inspectRelation(r.relationship_id,true);row.onblur=()=>inspectRelation(r.relationship_id,false);list.append(row);
  }
  if(!rows.length)list.append(el('p',t('empty')));
  if(rows.length>selectionRows)list.append(button(t('more'),()=>{selectionRows+=10;renderSelection();}));
  details.append(list);panel.append(details);
  if(expanded.has(cid)){expand.textContent=ux('展開済み','Expanded');return;}
  try{
    const data=await client.company(cid);if(version!==selectionVersion)return;
    const newCompanies=data.companies.filter(c=>!companies.has(c.company_id)).length;
    const added=[...data.relationships,...(data.peer_relationships||[])].filter(r=>!relationships.has(r.relationship_id)).length;
    expand.textContent=ux(`つながりを展開 ＋${newCompanies}社 / ${added}件`,`Expand +${newCompanies} companies / ${added} connections`);
    expand.disabled=added===0;
    expand.title=ux('絞り込みと表示上限により、一部が表示されない場合があります','Filters and the display limit may hide some additions');
  }catch{if(version===selectionVersion){expand.textContent=ux('つながりの展開を再試行','Retry expansion');expand.disabled=false;}}
}
function openDetail(title){
  const panel=$('mtz-detail');if(panel.hidden)lastFocus=document.activeElement;
  panel.hidden=false;$('mtz-map-app').classList.add('has-detail');$('mtz-detail-content').replaceChildren(el('h2',title));$('mtz-detail-content').firstChild.id='mtz-detail-title';
  syncDetailLayout();
  $('mtz-close').focus({preventScroll:true});
  // Detail panels change the canvas size, not the user's zoom or pan.
  cy?.resize();
}
function syncDetailLayout(){const panel=$('mtz-detail'),mobile=matchMedia('(max-width: 760px)').matches;panel.setAttribute('aria-modal',String(mobile));for(const n of $('mtz-map-app').children)if(n!==panel){n.inert=mobile;n.toggleAttribute('inert',mobile);if(mobile)n.setAttribute('aria-hidden','true');else n.removeAttribute('aria-hidden');}if(mobile&&!panel.contains(document.activeElement))$('mtz-close').focus();}
function closeDetail(){
  detailGeneration++;
  if($('mtz-detail').hidden)return;$('mtz-detail').hidden=true;$('mtz-map-app').classList.remove('has-detail');for(const n of $('mtz-map-app').children){n.inert=false;n.removeAttribute('inert');n.removeAttribute('aria-hidden');}
  if(lastFocus?.isConnected)lastFocus.focus({preventScroll:true});
  cy?.resize();
}
function paragraph(parent,title,value){if(value===null||value===undefined||value==='')return;const d=el('div',undefined,'mtz-field');if(title)d.append(el('h3',title));d.append(el('p',String(value)));parent.append(d);}
async function showCompany(cid){
  cid=client.canonicalId(cid);
  const seq=++detailGeneration;const c=companies.get(cid)||client.companies.find(c=>c.company_id===cid);if(!c)return;
  selected=cid;highlightCompany();
  openDetail(c.display_name);const content=$('mtz-detail-content');
  if(logo(c)){const img=el('img',undefined,'company-logo');img.src=logo(c);img.alt=c.display_name;content.prepend(img);}
  const results=el('section',undefined,'mtz-earnings-results');results.hidden=true;results.id='mtz-company-results';
  let loaded=false;
  const resultsButton=button(t('viewResults'),async()=>{
    results.hidden=!results.hidden;resultsButton.setAttribute('aria-expanded',String(!results.hidden));
    if(results.hidden||loaded)return;
    resultsButton.disabled=true;results.setAttribute('aria-busy','true');results.replaceChildren(el('p',t('loading')));
    try{
      const report=await latestResults(c);if(!results.isConnected)return;
      results.replaceChildren();loaded=true;
      if(!report){results.append(el('p',t('resultsMissing')));return;}
      const r=report.latest;
      results.append(el('h3',t('latestResults')),el('p',report.companyName+' · '+report.symbol,'muted'));
      results.append(el('p',state.lang==='ja'?`${r.fiscalYear}年度 第${r.fiscalQuarter}四半期`:`FY${r.fiscalYear} Q${r.fiscalQuarter}`));
      const table=el('table'),head=el('thead'),header=el('tr');
      for(const label of [t('resultMetric'),t('resultValue'),t('resultYoY')]){const th=el('th',label);th.scope='col';header.append(th);}head.append(header);table.append(head);
      const body=el('tbody');for(const row of resultRows(report,state.lang)){const tr=el('tr'),th=el('th',row.label);th.scope='row';tr.append(th,el('td',row.value),el('td',row.change));body.append(tr);}table.append(body);results.append(table);
      results.append(el('p',t('resultPeriod')+': '+(r.startDate||'—')+' — '+r.endDate,'muted'),el('p',t('resultFiled')+': '+(r.filedDate||'—')+' · '+(r.form||'—'),'muted'));
      if(c.display_member_ids?.length>1)results.append(el('p',t('consolidatedResults'),'muted'));
    }catch{if(results.isConnected)results.replaceChildren(el('p',t('resultsFailed')));}
    finally{resultsButton.disabled=false;results.removeAttribute('aria-busy');}
  },'mtz-results-button');
  resultsButton.setAttribute('aria-expanded','false');resultsButton.setAttribute('aria-controls',results.id);content.append(resultsButton,results);
  paragraph(content,state.lang==='ja'?'国':'Country',c.country);
  paragraph(content,state.lang==='ja'?'収録範囲':'Coverage',client.coverage.universe);
  if(c.display_member_ids?.length>1)paragraph(content,state.lang==='ja'?'まとめて表示':'Displayed together',c.display_member_ids.map(id=>client.rawName(id)).join(' / '));
  paragraph(content,state.lang==='ja'?'上場情報の確認日':'Listing checked',c.listing_status_as_of);
  const symbol=c.listings[0]?.symbol;if(symbol)content.append(link(t('calendar'),calendarURL(state,symbol)));
  paragraph(content,t('us'),c.listings.map(l=>l.symbol+(l.exchange?' · '+l.exchange:'')).join(', ')||t('unknownSymbol'));
  paragraph(content,state.lang==='ja'?'上場状態':'Listing',t(c.listing_status==='unknown'?'unknownListing':c.listing_status)+(c.listing_status_as_of?' · '+c.listing_status_as_of:''));
  content.append(button(t('center'),()=>choose(cid),'primary'),button(t('expand'),()=>{closeDetail();expandCompany(cid);}));
  if(cid!==state.company&&expanded.has(cid))content.append(button(t('collapseConnections'),()=>{closeDetail();collapseCompany(cid);}));
  const earnings=el('div',t('loading'));content.append(earnings);
  try{
    earningsPromise ||= Promise.all([fetch('earnings_data.json').then(r=>{if(!r.ok)throw Error('earnings');return r.json();}),fetch('assets/relationships/calendar-universe.json').then(r=>{if(!r.ok)throw Error('universe');return r.json();})]);
    const [records,universe]=await earningsPromise;if(seq!==detailGeneration)return;const result=nextEarnings(c,records,universe,dateKey(state.tz));earnings.replaceChildren(el('h3',t('nextEarnings')));
    if(result.state==='found'){const r=result.record;earnings.append(el('p',`${r.date===dateKey(state.tz)?t('today')+' · ':''}${r.date} · ${t(['bmo','amc'].includes(r.hour)?r.hour:'dateOnly')}${r.status==='unconfirmed'?' · '+t('unconfirmed'):''}`),link(t('calendar'),calendarURL(state,r.symbol,r.date.slice(0,7))));}else earnings.append(el('p',t(result.state)));
  }catch{earningsPromise=null;if(seq!==detailGeneration)return;earnings.textContent=t('earningsError');}
  const rels=[...relationships.values()].filter(r=>[r.source_company_id,r.target_company_id].includes(cid));paragraph(content,t('relations'),rels.length);
  for(const r of rels.slice(0,30))content.append(relationCard(r));
  if(rels.length>30)content.append(button(t('more'),()=>{closeDetail();choose(cid).then(()=>setView('list'));}));
}
async function showRelation(rid){
  const seq=++detailGeneration;message(t('loading'));
  try{const d=await client.relationship(rid);if(seq!==detailGeneration)return;const r=d.relationship;openDetail(name(r.source_company_id)+(r.direction==='directed'?' → ':' — ')+name(r.target_company_id));const content=$('mtz-detail-content');
    if([r.source_company_id,r.target_company_id].some(id=>client.groups.has(client.canonicalId(id))))paragraph(content,state.lang==='ja'?'資料上の当事者':'Parties in the source',client.rawName(r.source_company_id)+(r.direction==='directed'?' → ':' — ')+client.rawName(r.target_company_id));
    const latest=d.events.filter(e=>r.latest_event_ids.includes(e.event_id)).sort((a,b)=>(b.announced_date||'').localeCompare(a.announced_date||''))[0];
    if(latest?.amounts.length){const summary=el('section',undefined,'mtz-amount-detail');summary.append(el('h3',state.lang==='ja'?'公表された金額':'Disclosed amount'));for(const a of latest.amounts)summary.append(el('strong',amountText(a,state.lang)),el('p',t(a.amount_kind)+' · '+t(a.value_semantics)));content.append(summary);}
    paragraph(content,ux('金額の分類','Amount classification'),ratingText(d.summary||relationships.get(rid)));
    paragraph(content,t('details'),t(r.relationship_type));paragraph(content,t('statusAsOf'),t(r.lifecycle_status)+' · '+(r.status_as_of||'—'));paragraph(content,'',r.description);
    if(r.business){const b=r.business;paragraph(content,t('businessContent'),b.headline);paragraph(content,t('products'),b.products.join(' / '));paragraph(content,client.rawName(r.source_company_id),b.source_role);paragraph(content,client.rawName(r.target_company_id),b.target_role);paragraph(content,t('scale'),b.scale);paragraph(content,t('geography'),b.geography);}
    if(r.status_as_of&&r.status_as_of<new Date(Date.now()-365*86400000).toISOString().slice(0,10))content.append(el('p',t('stale'),'notice'));
    paragraph(content,t(r.verification),r.verification_metadata?.verified_at?new Intl.DateTimeFormat(state.lang,{timeZone:state.tz,dateStyle:'medium',timeStyle:'short'}).format(new Date(r.verification_metadata.verified_at))+' · '+state.tz:'');
    const ordered=[...d.events].sort((a,b)=>(b.announced_date||'').localeCompare(a.announced_date||''));
    for(const e of ordered){content.append(el('h3',t('history')+' · '+t(e.event_type)));
      paragraph(content,state.lang==='ja'?'公表日 / 締結日 / SEC提出日':'Announced / agreed / SEC filed',[e.announced_date||'—',e.agreement_date||'—',e.filed_date||'—'].join(' / '));
      for(const a of e.amounts){const block=el('section',undefined,'mtz-amount-detail');block.append(el('strong',amountText(a,state.lang)),el('p',t(a.amount_kind)+' · '+t(a.value_semantics)),el('p',a.scope));if(a.contingent!==false)block.append(el('p',a.contingent===true?t('contingent'):(state.lang==='ja'?'条件の有無は未確認':'Contingency unconfirmed')));if(a.conditions)block.append(el('p',a.conditions));content.append(block);}
      if(!e.amounts.length)paragraph(content,t('unknownAmount'),t(e.amount_disclosure));
      paragraph(content,t('term'),termText(e.term,state.lang));
      paragraph(content,state.lang==='ja'?'収録を検出':'Indexed',new Intl.DateTimeFormat(state.lang,{timeZone:state.tz,dateStyle:'medium',timeStyle:'short'}).format(new Date(e.detected_at))+' · '+state.tz);
      paragraph(content,t('conditions'),e.conditions);
    }
    content.append(el('h3',t('evidence')));
    for(const e of d.evidence){const s=d.sources.find(s=>s.source_id===e.source_id);content.append(el('blockquote',e.excerpt));paragraph(content,s.title,e.section+' · '+e.locator);const url=safeSourceURL(s.canonical_url);if(url)content.append(link(t('source'),url));}
    for(const id of [r.source_company_id,r.target_company_id])content.append(button(name(id),()=>showCompany(id)));
    message(client.offline?t('offline'):'');
  }catch{if(seq===detailGeneration)message(t('failed'),true);}
}
function renderIntro(){
  if(!client)return;
  $('mtz-pilot').textContent=t('us')+' · '+(client.coverage.universe||'pilot');
  $('mtz-discovery').textContent=`${client.coverage.indexed_companies} ${t('companies')} · ${client.coverage.published_relationships} ${t('relations')} · ${t('freshness')}: ${client.manifest.data_as_of||'—'}`;
  $('mtz-quick-start').replaceChildren();
  for(const id of ['co-aapl','co-openai','co-amzn','co-googl','co-nvda','co-msft','co-meta','co-mu','co-coreweave']){
    const c=client.companies.find(c=>c.company_id===id);if(c)$('mtz-quick-start').append(button(c.display_name+(c.listings[0]?' · '+c.listings[0].symbol:''),()=>choose(id),'mtz-company-chip'));
  }
  $('mtz-favorites').replaceChildren();
  const favorites=client.companies.filter(c=>c.listings.some(l=>state.favorites.includes(l.symbol)));
  if(favorites.length){$('mtz-favorites').append(el('h2',t('favorites')));for(const c of favorites)$('mtz-favorites').append(button(c.display_name,()=>choose(c.company_id),'favorite-company'));}
  const rows=dealRows(client.events,state),host=$('mtz-updates');host.replaceChildren(el('h2',t('dealTimeline')),el('p',t('dealScope'),'muted'));
  host.append(el('p',rows.length+' '+t('dealCount'),'muted'));
  if(!rows.length)host.append(el('p',t('empty')));
  const grid=el('div',undefined,'mtz-deal-grid');host.append(grid);
  for(const e of rows.slice(0,dealPageSize)){
    const card=el('article',undefined,'mtz-deal-card');
    card.append(el('p',(e.announced_date||e.filed_date||t('undated'))+' · '+(e.relationship_types||[]).map(t).join(' / '),'eyebrow'));
    card.append(el('h3',(e.company_ids||[]).map(name).join(' — ')));
    if(e.amounts?.length){for(const a of e.amounts){card.append(el('strong',amountText(a,state.lang),'mtz-deal-value'),el('p',t(a.amount_kind)+' · '+t(a.value_semantics),'muted'));if(a.contingent===true)card.append(el('span',t('contingent'),'mtz-deal-condition'));}}
    else card.append(el('p',t(e.amount_disclosure||'not_stated_in_source'),'muted'));
    if(e.description)card.append(el('p',e.description,'mtz-deal-description'));
    const term=e.term?termText(e.term,state.lang):'';if(term)card.append(el('p',term,'muted'));
    card.append(el('p',(e.statuses||[]).map(t).join(' / ')+(e.source_count?' · '+e.source_count+' '+t('sourcesCount'):''),'muted'));
    const actions=el('div',undefined,'mtz-deal-actions');actions.append(button(t('dealDetails'),()=>showRelation(e.relationship_ids[0]),'primary'),button(t('viewOnMap'),()=>choose(e.company_ids.find(id=>id==='co-openai')||e.company_ids[0])));card.append(actions);grid.append(card);
  }
  if(rows.length>dealPageSize)host.append(button(t('more'),()=>{dealPageSize+=20;renderIntro();}));
  $('mtz-version').textContent=`${client.coverage.indexed_companies} ${t('companies')} · ${client.coverage.published_relationships} ${t('relations')} · ${t('freshness')}: ${client.manifest.data_as_of||'—'}`;
}
function showCoverage(){if(!client)return;detailGeneration++;openDetail(t('coverage'));const c=client.coverage,p=$('mtz-detail-content');for(const [key,value] of [['universe',t('universe_'+c.universe)],['target_companies',c.target_companies],['indexed_companies',c.indexed_companies],['published_relationships',c.published_relationships],['pending_review',c.pending_review]])paragraph(p,({universe:state.lang==='ja'?'対象リスト':'Universe',target_companies:state.lang==='ja'?'収集対象企業':'Target companies',indexed_companies:state.lang==='ja'?'収録企業':'Indexed companies',published_relationships:state.lang==='ja'?'確認済み関係':'Verified connections',pending_review:state.lang==='ja'?'確認待ち':'Pending review'})[key],value);paragraph(p,state.lang==='ja'?'資料上の企業・関係数':'Source companies / relationships',`${c.source_company_count} / ${c.source_relationship_count}`);paragraph(p,state.lang==='ja'?'表示の統合':'Display grouping','Google / Alphabet · Amazon / AWS');paragraph(p,t('checked'),c.last_run?.checked_at||t('collectionUnavailable'));for(const line of c.limitations)p.append(el('p',line));}
async function start(){shell();message(t('loading'));try{const [data,logos]=await Promise.all([new DataClient().open(),fetch('assets/relationships/logos.json',{cache:'no-cache'}).then(r=>r.ok?r.json():{}).catch(()=>({}))]);client=new CompanyView(data);logoPaths=Object.fromEntries(Object.entries(logos).filter(([k,v])=>/^(?:[A-Z0-9.-]{1,20}|co-[a-z0-9-]{1,80})$/.test(k)&&/^assets\/logos\/us\/[A-Z0-9._-]+\.(?:png|ico)$/.test(v)));translate();renderIntro();message(client.offline?t('offline'):'');if(state.company&&client.manifest.company_ids.includes(state.company))await choose(state.company,false);else if(!state.company&&state.symbol){const matches=rankCompanies(client.companies,state.symbol);if(matches.length===1&&matches[0].rank===0)await choose(matches[0].company.company_id,false);else{$('mtz-search').value=state.symbol;search();}}else if(state.q){$('mtz-search').value=state.q;search();}if(state.company&&!client.manifest.company_ids.includes(state.company))message(t('searchEmpty'));if(state.relation&&client.manifest.relationship_ids.includes(state.relation))await showRelation(state.relation);}catch(e){message(t('failed'),true);$('mtz-message').append(button(t('retry'),()=>location.reload()));}}
start();
