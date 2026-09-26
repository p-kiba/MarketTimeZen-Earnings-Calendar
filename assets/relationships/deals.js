// Public, already-approved deal summaries. Dates are publication dates, never ingest dates.
export function dealRows(events,state,now=new Date()) {
  const rows=events.timeline||[...(events.events||[]),...(events.newly_indexed||[]),...(events.undated||[])];
  const unique=[...new Map(rows.map(e=>[e.event_id,e])).values()];
  const cutoff=state.days?new Date(now.getTime()-Number(state.days)*86400000).toISOString().slice(0,10):null;
  return unique.filter(e=>{
    const date=e.announced_date||e.filed_date;
    return (!state.amount||e.amounts?.length)&&(!state.type||e.relationship_types?.includes(state.type))&&(!state.status||e.statuses?.includes(state.status))&&(!cutoff||date&&date>=cutoff);
  }).sort((a,b)=>(b.announced_date||b.filed_date||'').localeCompare(a.announced_date||a.filed_date||'')||a.event_id.localeCompare(b.event_id));
}
