// User-selected display groups. Primary records and their legal parties stay intact.
const GROUPS = [
  {id:'co-googl', members:['co-googl','co-google'], name:'Google / Alphabet', aliases:['Google','Alphabet','Google Cloud','グーグル','アルファベット']},
  {id:'co-amzn', members:['co-amzn','co-aws'], name:'Amazon / AWS', aliases:['Amazon','AWS','Amazon Web Services','アマゾン']},
  {id:'co-nebius', members:['co-nebius','co-nebius-inc'], name:'Nebius Group', aliases:['Nebius','Nebius Group','Nebius, Inc.']},
  {id:'co-openai', members:['co-openai','co-openai-opco'], name:'OpenAI', aliases:['OpenAI','OpenAI Group','OpenAI Group PBC','OpenAI OpCo, LLC']},
];

// Presentation only: retain source identities and contract-party names for evidence.
const SHORT_NAMES = {
  'co-palantir':'Palantir', 'co-nflx':'Netflix', 'co-dell':'Dell',
  'co-brk-b':'Berkshire Hathaway', 'co-jpm':'JPMorgan Chase',
  'co-hpe':'HPE', 'co-cost':'Costco', 'co-catl':'CATL', 'co-uber':'Uber',
  'co-oxy':'Occidental', 'co-unh':'UnitedHealth', 'co-ge':'GE',
  'co-the-goldman-sachs-group-inc':'Goldman Sachs',
  'co-the-charles-schwab-corporation':'Charles Schwab',
  'co-capital-one-financial-corporation':'Capital One',
  'co-e-trade-financial-corporation':'E*TRADE',
  'co-marvell-technology-inc':'Marvell', 'co-sony-pictures':'Sony Pictures',
  'co-ase':'ASE', 'co-foxconn':'Foxconn', 'co-siliconware':'Siliconware',
  // Keep business/subsidiary distinctions; these are not parent-company merges.
  'co-woodward-gas-turbine-combustion-parts':'Woodward ガスタービン燃焼部品事業',
  'co-collins-aerospace-flight-control-actuation-business':'Collins 飛行制御・駆動事業',
};
function conciseCompany(company) {
  const original=company.display_name;
  const display_name=SHORT_NAMES[company.company_id] || original.replace(/(?:,?\s+(?:Inc\.?|Incorporated|Corporation|Corp\.?|LLC|Ltd\.?|Limited|plc))+$/i,'');
  if(display_name===original)return company;
  const aliases=[...(company.aliases||[])];
  for(const name of [original,company.legal_name].filter(Boolean)){
    if(!aliases.some(a=>a.name===name))aliases.push({name});
  }
  return {...company,display_name,aliases};
}

export class CompanyView {
  constructor(raw) {
    this.raw=raw;
    this.themes=raw.themes||[];
    this.rawCompanies=new Map(raw.companies.map(c=>[c.company_id,c]));
    this.memberToGroup=new Map();
    this.groups=new Map();
    for(const group of GROUPS){
      // A historical/offline release may not contain every group member.
      const members=group.members.filter(id=>this.rawCompanies.has(id));
      if(!members.length)continue;
      const id=members.includes(group.id)?group.id:members[0];
      this.groups.set(id,{...group,id,members});
      for(const member of members)this.memberToGroup.set(member,id);
    }
    const display=new Map();
    for(const company of raw.companies){
      const id=this.canonicalId(company.company_id);
      if(display.has(id))continue;
      const group=this.groups.get(id), primary=this.rawCompanies.get(id);
      if(!group){display.set(id,conciseCompany(company));continue;}
      const members=group.members.map(member=>this.rawCompanies.get(member));
      const names=new Set([...group.aliases,...members.flatMap(c=>[c.display_name,c.legal_name,...c.aliases.map(a=>a.name)]).filter(Boolean)]);
      display.set(id,{...primary,display_name:group.name,
        aliases:[...names].map(name=>({name})),display_member_ids:group.members,
        listings:[...new Map(members.flatMap(c=>c.listings).map(l=>[`${l.symbol}|${l.exchange}`,l])).values()],
        themes:[...new Set(members.flatMap(c=>c.themes||[]))]});
    }
    this.companies=[...display.values()];
    this.displayCompanies=display;
    this.events=Object.fromEntries(Object.entries(raw.events).map(([key,value])=>[
      key,Array.isArray(value)?value.map(event=>this.projectEvent(event)).filter(Boolean):value
    ]));
    const visibleIds=new Set((this.events.timeline||[]).flatMap(e=>e.relationship_ids));
    this.coverage={...raw.coverage,indexed_companies:this.companies.length,
      published_relationships:Array.isArray(this.events.timeline)?visibleIds.size:raw.coverage.published_relationships,
      source_company_count:raw.coverage.indexed_companies,
      source_relationship_count:raw.coverage.published_relationships};
  }
  get manifest(){return this.raw.manifest;}
  get offline(){return this.raw.offline;}
  canonicalId(id){return this.memberToGroup.get(id)||id;}
  rawName(id){return this.rawCompanies.get(id)?.display_name||id;}
  projectRelationship(row){
    const source=this.canonicalId(row.source_company_id),target=this.canonicalId(row.target_company_id);
    if(source===target)return null;
    return {...row,source_company_id:source,target_company_id:target};
  }
  projectEvent(event){
    const ids=[...new Set((event.company_ids||[]).map(id=>this.canonicalId(id)))];
    if(ids.length<2 && (event.company_ids||[]).length>1)return null;
    return {...event,company_ids:ids};
  }
  async company(id,signal){
    const center=this.canonicalId(id);
    const members=this.groups.get(center)?.members||[center];
    const payloads=await Promise.all(members.map(member=>this.raw.company(member,signal)));
    const direct=new Map(),peers=new Map();
    for(const payload of payloads){
      for(const row of [...payload.relationships,...(payload.peer_relationships||[])]){
        const r=this.projectRelationship(row);if(!r)continue;
        const target=[r.source_company_id,r.target_company_id].includes(center)?direct:peers;
        target.set(r.relationship_id,r);
      }
    }
    const neighbors=new Set([...direct.values()].flatMap(r=>[r.source_company_id,r.target_company_id]));
    neighbors.delete(center);
    // A grouped center joins two adjacency sets. Fetch their neighbors to also
    // recover links between those sets. For other centers only aliased neighbors
    // need supplementation (e.g. Amazon's investment beside an AWS contract).
    const supplementIds=new Set();
    for(const neighbor of neighbors){
      if(members.length<2 && !this.groups.has(neighbor))continue;
      for(const member of this.groups.get(neighbor)?.members||[neighbor]){
        if(!members.includes(member))supplementIds.add(member);
      }
    }
    const supplements=await Promise.all([...supplementIds].map(member=>this.raw.company(member,signal)));
    for(const payload of supplements){
      for(const row of payload.relationships){
        const r=this.projectRelationship(row);
        if(r && neighbors.has(r.source_company_id) && neighbors.has(r.target_company_id))peers.set(r.relationship_id,r);
      }
    }
    // Only retain peer links whose two endpoints are displayed neighbors.
    const cross=[...peers.values()].filter(r=>neighbors.has(r.source_company_id)&&neighbors.has(r.target_company_id));
    return {...payloads[0],company:this.displayCompanies.get(center),
      companies:[center,...neighbors].map(cid=>this.displayCompanies.get(cid)),
      relationships:[...direct.values()],peer_relationships:cross,
      total_relationships:direct.size,total_counterparties:neighbors.size,total_peer_relationships:cross.length};
  }
  // Detail documents retain original IDs, parties, evidence, dates and amounts.
  relationship(id,signal){return this.raw.relationship(id,signal);}
}
