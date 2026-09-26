export function decimalString(value,lang='en') {
  if(value===null || !/^\d+(\.\d+)?$/.test(value))return '—';
  const [whole,frac]=value.split('.');return BigInt(whole).toLocaleString(lang==='ja'?'ja-JP':'en-US')+(frac?'.'+frac:'');
}
export function amountText(a,lang='en') {
  const prefix={exact:'',approximately:lang==='ja'?'約 ':'Approx. ',more_than:lang==='ja'?'超 ': 'More than ',up_to:lang==='ja'?'最大 ':'Up to ',at_least:lang==='ja'?'最低 ':'At least ',range:'',unspecified:''}[a.qualifier]||'';
  const value=a.value ?? a.max_value ?? a.min_value;
  if(!a.currency&&a.original_text){
    if(lang==='ja'&&value&&/^\d+$/.test(value)&&BigInt(value)%100000000n===0n&&a.original_text.includes('$'))return (a.qualifier==='more_than'?'':prefix)+(BigInt(value)/100000000n).toLocaleString('ja-JP')+'億'+(a.qualifier==='more_than'?'超':'')+'（原文$・通貨未確認）';
    return a.original_text+(lang==='ja'?'（通貨未確認）':' (currency unconfirmed)');
  }
  const currency=a.currency || (lang==='ja'?'通貨未確認':'Currency unconfirmed');
  if(lang==='ja'&&a.currency==='USD'&&value&&/^\d+(?:\.0+)?$/.test(value)&&BigInt(value.split('.')[0])%100000000n===0n){
    const formatted=(BigInt(value.split('.')[0])/100000000n).toLocaleString('ja-JP')+'億米ドル';
    if(a.qualifier==='more_than'&&a.min_value&&!a.max_value)return formatted+'超';
    if(a.qualifier==='at_least'&&a.min_value&&!a.max_value)return formatted+'以上';
    if(!a.min_value&&!a.max_value)return prefix+formatted;
  }
  return prefix+currency+' '+(a.min_value&&a.max_value?decimalString(a.min_value,lang)+'–'+decimalString(a.max_value,lang):decimalString(value,lang));
}
export function dateKey(tz='America/New_York',date=new Date()) {
  const p=Object.fromEntries(new Intl.DateTimeFormat('en-US',{timeZone:tz,year:'numeric',month:'2-digit',day:'2-digit'}).formatToParts(date).map(p=>[p.type,p.value]));return `${p.year}-${p.month}-${p.day}`;
}
export function nextEarnings(company,records,universe,today) {
  const symbols=company.listings.filter(l=>!l.valid_to||l.valid_to>=today).map(l=>l.symbol);
  if(company.listing_status==='unlisted')return {state:'unlisted'};
  if(!symbols.length)return {state:'unknownSymbol'};
  if(!symbols.some(s=>universe.includes(s)))return {state:'outsideUniverse'};
  const next=records.filter(r=>symbols.includes(r.symbol)&&r.status!=='changed'&&/^\d{4}-\d{2}-\d{2}$/.test(r.date)&&r.date>=today).sort((a,b)=>a.date.localeCompare(b.date))[0];
  if(next)return {state:'found',record:next};
  const last=records.reduce((v,r)=>r.date>v?r.date:v,'');
  return {state:last<today?'outsidePeriod':'notRecorded'};
}
export function rankCompanies(companies,query) {
  const raw=query.trim();if(!raw)return [];
  // Accept common ticker-entry forms such as "$AAPL" and "NASDAQ:AAPL".
  const tickerQuery=raw.replace(/^\$/,'').replace(/^[A-Z][A-Z0-9.-]*:/i,'').trim().toUpperCase();
  const q=raw.toLocaleLowerCase();
  return companies.map(c=>{
    const symbols=c.listings.map(l=>l.symbol.toUpperCase());
    const names=[c.legal_name,c.display_name,...c.aliases.map(a=>a.name)].filter(Boolean).map(n=>n.toLowerCase());
    const rank=(tickerQuery&&symbols.includes(tickerQuery))?0:names.includes(q)?1:
      (tickerQuery&&symbols.some(s=>s.startsWith(tickerQuery)))?2:names.some(n=>n.startsWith(q))?3:
      (tickerQuery&&symbols.some(s=>s.includes(tickerQuery)))?4:names.some(n=>n.includes(q))?5:99;
    return {company:c,rank};
  }).filter(r=>r.rank<99).sort((a,b)=>a.rank-b.rank||a.company.display_name.localeCompare(b.company.display_name));
}

export function amountBands(thresholds,lang='en') {
  const compact=value=>{const n=BigInt(value);if(lang==='ja')return (Number(n)/1e8).toLocaleString('ja-JP')+'億';return '$'+(Number(n)/1e9>=1?(Number(n)/1e9)+'B':(Number(n)/1e6)+'M');};
  return thresholds.map((v,i)=>i===0?(lang==='ja'?compact(thresholds[1])+'ドル未満':'< '+compact(thresholds[1])):i===thresholds.length-1?compact(v)+(lang==='ja'?'ドル以上':'+'):compact(v)+'–'+compact(thresholds[i+1])+(lang==='ja'?'ドル未満':''));
}

export function termText(term,lang='en') {
  const ja=lang==='ja',parts=[];
  if(term.duration_value!==null){const units=ja?{year:'年',month:'か月',day:'日'}:{year:'years',month:'months',day:'days'};parts.push(term.duration_value+' '+(units[term.duration_unit]||term.duration_unit||''));}
  if(term.start_basis)parts.push(term.start_basis==='each_service_schedule_commencement'?(ja?'各サービスの提供開始日から':'From each service commencement'):term.start_basis==='unknown'?(ja?'開始条件未確認':'Start condition unconfirmed'):term.start_basis);
  if(parts.length||term.start_date||term.end_date)parts.push((term.start_date||(ja?'開始日未定':'Start not stated'))+' – '+(term.end_date||(ja?'終了日未定':'End not stated')));
  if(term.renewal)parts.push(term.renewal);
  return parts.join(' · ');
}
