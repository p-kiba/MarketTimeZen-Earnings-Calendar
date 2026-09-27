export const validId = value => /^[a-zA-Z0-9_-]{1,100}$/.test(value || '');
export function queryState(search = location.search) {
  const p = new URLSearchParams(search);
  const symbol = (p.get('symbol') || '').trim().toUpperCase();
  const favorites = (p.get('favorites') || '').slice(0,5000).split(',').map(s=>s.trim().toUpperCase()).filter(s=>/^[A-Z0-9.^/-]{1,20}$/.test(s)).slice(0,200);
  let tz=p.get('tz') || 'America/New_York';
  try { new Intl.DateTimeFormat('en',{timeZone:tz}); } catch { tz='America/New_York'; }
  const requestedTab=p.get('tab');
  const tab=['map','news'].includes(requestedTab)?requestedTab:'connections';
  return {company:validId(p.get('company'))?p.get('company'):null,symbol:/^[A-Z0-9.^/-]{1,20}$/.test(symbol)?symbol:'',q:(p.get('q')||'').slice(0,120),favorites,view:p.get('view')==='list'?'list':'map',tab,relation:validId(p.get('relation'))?p.get('relation'):null,details:p.get('details')==='company'?'company':'',lang:p.get('lang')==='ja'?'ja':'en',tz,month:/^\d{4}-(0[1-9]|1[0-2])$/.test(p.get('month')||'')?p.get('month'):null,return_market:p.get('return_market')==='jp'?'jp':'us',type:(p.get('type')||'').slice(0,30),status:(p.get('status')||'').slice(0,20),theme:/^[a-z0-9_-]{1,40}$/.test(p.get('theme')||'')?p.get('theme'):'',amount:p.get('amount')==='1',days:['30','90','365'].includes(p.get('days'))?p.get('days'):''};
}
export function calendarURL(state,symbol=null,month=null) {
  const url=new URL(symbol?'index.html':state.return_market==='jp'?'japan.html':'index.html',location.href);
  if(state.favorites.length)url.searchParams.set('favorites',state.favorites.join(','));
  if(month||state.month)url.searchParams.set('month',month||state.month);
  if(symbol)url.searchParams.set('symbol',symbol);
  return url.href;
}
export function updateURL(state,push=false) {
  const url=new URL('map.html',location.href);
  for(const key of ['company','q','view','tab','details','lang','tz','month','return_market','type','status','theme','days'])if(state[key])url.searchParams.set(key,state[key]);
  if(state.amount)url.searchParams.set('amount','1');
  if(state.favorites.length)url.searchParams.set('favorites',state.favorites.join(','));
  history[push?'pushState':'replaceState'](null,'',url);
}
export function connectionsURL(state,tab='connections') {
  const url=new URL('map.html',location.href);
  for(const key of ['lang','tz','month','return_market'])if(state[key])url.searchParams.set(key,state[key]);
  if(state.favorites.length)url.searchParams.set('favorites',state.favorites.join(','));
  if(tab==='map'){
    url.searchParams.set('tab','map');
    url.searchParams.set('company','co-aapl');
    url.searchParams.set('view','map');
  }
  if(tab==='news')url.searchParams.set('tab','news');
  return url.href;
}
export function safeSourceURL(value) {
  try { const u=new URL(value); if(u.protocol!=='https:'||u.username||u.password||u.port||!u.hostname.includes('.')||/^(?:\d|localhost)/.test(u.hostname)||u.hostname.endsWith('.local'))return null; return u.href; } catch {return null;}
}
