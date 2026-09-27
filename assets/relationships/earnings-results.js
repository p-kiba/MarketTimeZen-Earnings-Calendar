// Stored SEC-derived quarterly results. Fetch only when the user requests them.
const cache=new Map();
export async function latestResults(company){
  const symbols=[...new Set(company.listings.map(l=>l.symbol))].filter(s=>/^[A-Z0-9][A-Z0-9.-]{0,19}$/.test(s));
  for(const symbol of symbols){
    const path=`output_json/earnings/${symbol.toLowerCase()}.json`;
    if(!cache.has(path))cache.set(path,fetch(path).then(async r=>{if(r.status===404)return null;if(!r.ok)throw Error('earnings');return r.json();}).catch(e=>{cache.delete(path);throw e;}));
    const data=await cache.get(path);if(!data)continue;
    const quarters=Object.entries(data).filter(([key,r])=>/^FY\d{4}Q[1-4]$/.test(key)&&r&&typeof r==='object'&&/^\d{4}-\d{2}-\d{2}$/.test(r.endDate||''))
      .map(([,r])=>r).sort((a,b)=>b.endDate.localeCompare(a.endDate)||(b.filedDate||'').localeCompare(a.filedDate||''));
    const latest=quarters[0];if(!latest)continue;
    return {symbol,companyName:data.companyName||company.display_name,latest,previous:quarters.find(r=>r.fiscalYear===latest.fiscalYear-1&&r.fiscalQuarter===latest.fiscalQuarter)};
  }
  return null;
}
export function resultRows(result,lang){
  const ja=lang==='ja',n=(v,d=1)=>new Intl.NumberFormat(lang,{maximumFractionDigits:d}).format(v),valid=v=>typeof v==='number'&&Number.isFinite(v);
  return [['revenue',ja?'売上高':'Revenue'],['netIncome',ja?'純利益':'Net income'],['epsDiluted','EPS'],['grossMargin',ja?'粗利率':'Gross margin'],['operatingCashFlow',ja?'営業CF':'Operating cash flow']].map(([key,label])=>{
    const value=result.latest[key],prior=result.previous?.[key];let formatted='—',change='—';
    if(valid(value)){
      if(key==='grossMargin')formatted=n(value*100)+'%';
      else if(key==='epsDiluted')formatted=n(value,2);
      else{const size=Math.abs(value);formatted='$'+(size>=1e9?n(value/1e9)+'B':size>=1e6?n(value/1e6)+'M':n(value,0));}
      if(valid(prior)){
        if(key==='grossMargin'){const delta=(value-prior)*100;change=(delta>0?'+':'')+n(delta)+(ja?'ポイント':' pp');}
        else if(prior>0){const delta=(value/prior-1)*100;change=(delta>0?'+':'')+n(delta)+'%';}
      }
    }
    return {label,value:formatted,change};
  });
}
