// Categorize the displayed endpoints relative to the chosen company.
// Explicit company display groups are projected before reaching this module.
export function category(r, center) {
  if (![r.source_company_id,r.target_company_id].includes(center)) return 'extended';
  if (['investment','acquisition','equity_right'].includes(r.relationship_type)) return 'capital';
  if (['subsidiary','group_member'].includes(r.relationship_type)) return 'group';
  if (['supplier','service_provider'].includes(r.relationship_type) && r.direction==='directed')
    return r.target_company_id===center?'suppliers':'customers';
  return 'collaboration';
}

export function connectionGroups(rows, center) {
  return ['suppliers','customers','collaboration','capital','group','extended'].map(key=>{
    const relationships=rows.filter(r=>category(r,center)===key);
    const counterparties=new Set(relationships.flatMap(r=>[r.source_company_id,r.target_company_id]).filter(id=>id!==center));
    return {key,relationships,counterparties:counterparties.size};
  }).filter(g=>g.relationships.length);
}

// Recompute from retained adjacency payloads so shared nodes/edges survive collapse.
export function mergeNeighborhoods(payloads) {
  const companies=new Map(),relationships=new Map();
  for(const p of payloads){
    p.companies.forEach(c=>companies.set(c.company_id,c));
    [...p.relationships,...(p.peer_relationships||[])].forEach(r=>relationships.set(r.relationship_id,r));
  }
  return {companies,relationships};
}

export function counterparties(rows,center) {
  return new Set(rows.filter(r=>[r.source_company_id,r.target_company_id].includes(center))
    .flatMap(r=>[r.source_company_id,r.target_company_id]).filter(id=>id!==center));
}
