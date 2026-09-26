const BASE='output_json/relationships/';
const SCOPE=new URL(BASE,globalThis.location?.href||'http://localhost/').pathname;
const ID=/^[a-zA-Z0-9_-]{1,100}$/;
function safePath(path) { return typeof path==='string'&&/^[a-zA-Z0-9_/-]+\.json$/.test(path)&&!path.includes('..')&&!path.startsWith('/'); }
async function hash(text) {return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))].map(n=>n.toString(16).padStart(2,'0')).join('');}
function saved(key) {try{return localStorage.getItem('mtz-public:'+SCOPE+':'+key);}catch{return null;}}
function save(key,value) {try{localStorage.setItem('mtz-public:'+SCOPE+':'+key,value);}catch{/* Public cache is optional and contains no preferences. */}}
export class DataClient {
  constructor(){this.manifest=null;this.offline=false;this.cache=new Map();}
  async fetchText(path,signal){const res=await fetch(path,{signal,cache:'no-cache'});if(!res.ok)throw new Error(`HTTP ${res.status}`);return res.text();}
  async verified(path,expected,signal){
    let failure;
    for(let attempt=0;attempt<2;attempt++)try{const text=await this.fetchText(BASE+path,signal);if(await hash(text)!==expected)throw new Error('Hash mismatch');save(path,text);return JSON.parse(text);}catch(e){if(e.name==='AbortError')throw e;failure=e;}
    const cached=saved(path);if(cached&&await hash(cached)===expected){this.offline=true;return JSON.parse(cached);}
    throw failure;
  }
  async open(signal){
    let pointer;try{pointer=JSON.parse(await this.fetchText(BASE+'latest.json',signal));}catch(e){if(e.name==='AbortError')throw e;pointer=JSON.parse(saved('last-pointer')||'null');this.offline=true;}
    if(!pointer)throw new Error('No complete public release available');
    const candidates=[pointer,pointer.previous,JSON.parse(saved('last-pointer')||'null')].filter(Boolean);
    let failure;
    for(const [index,p] of candidates.entries())try{
      if(!ID.test(p.build_id)||p.manifest!==`versions/${p.build_id}/manifest.json`)throw new Error('Invalid release pointer');
      const m=await this.verified(p.manifest,p.manifest_hash,signal);
      if(m.schema_version!=='1.0'||m.build_id!==p.build_id||!Array.isArray(m.company_ids)||!Array.isArray(m.relationship_ids))throw new Error('Unsupported release');
      const old=this.manifest;this.manifest=m;this.cache=new Map();
      try{
        const [companies,events,coverage]=await Promise.all(['companies.json','recent_events.json','coverage.json'].map(name=>this.file(name,signal)));
        this.companies=companies.companies;this.events=events;this.coverage=coverage.coverage;
        if(index>0)this.offline=true;save('last-pointer',JSON.stringify(p));return this;
      }catch(e){this.manifest=old;throw e;}
    }catch(e){if(e.name==='AbortError')throw e;failure=e;}
    throw failure;
  }
  async file(name,signal){
    if(!safePath(name)||!Object.prototype.hasOwnProperty.call(this.manifest.files,name))throw new Error('File is not in this manifest');
    if(this.cache.has(name))return this.cache.get(name);
    const v=await this.verified(`versions/${this.manifest.build_id}/${name}`,this.manifest.files[name],signal);
    if(v.build_id!==this.manifest.build_id||v.schema_version!=='1.0')throw new Error('Mixed release');
    this.cache.set(name,v);return v;
  }
  company(id,signal){if(!ID.test(id)||!this.manifest.company_ids.includes(id))throw new Error('Unknown company');return this.file(`companies/${id}.json`,signal);}
  relationship(id,signal){if(!ID.test(id)||!this.manifest.relationship_ids.includes(id))throw new Error('Unknown relationship');return this.file(`relationships/${id}.json`,signal);}
}
