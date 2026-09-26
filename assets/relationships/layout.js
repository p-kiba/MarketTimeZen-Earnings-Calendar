// Geometry expresses connectivity, never deal value or investment importance.
// Reserve room for the square logo and its wrapped company name underneath.
const CARD_WIDTH=120, CARD_HEIGHT=128, GOLDEN_ANGLE=Math.PI*(3-Math.sqrt(5));
const compareId=(a,b)=>a<b?-1:a>b?1:0;
function seed(id){let h=2166136261;for(const c of id)h=Math.imul(h^c.charCodeAt(0),16777619);return (h>>>0)/4294967296;}
const validPoint=p=>p&&Number.isFinite(p.x)&&Number.isFinite(p.y);
const overlaps=(a,b)=>Math.abs(a.x-b.x)<CARD_WIDTH&&Math.abs(a.y-b.y)<CARD_HEIGHT;

export function graphPositions(ids,relationships,width,height,centerId=ids[0],previous=new Map()) {
  if(!ids.length)return [];
  const ordered=[...new Set(ids)].sort(compareId),index=new Map(ordered.map((id,i)=>[id,i]));
  const center=index.get(centerId)??0,aspect=Math.max(.65,Math.min(2.2,(width||800)/Math.max(1,height||600)));
  const adjacency=ordered.map(()=>new Set()),pairKeys=new Set(),links=[];
  for(const r of relationships){
    const a=index.get(r.source_company_id),b=index.get(r.target_company_id);
    if(a===undefined||b===undefined||a===b)continue;
    const key=[Math.min(a,b),Math.max(a,b)].join(':');
    if(pairKeys.has(key))continue;
    pairKeys.add(key);links.push([Math.min(a,b),Math.max(a,b)]);adjacency[a].add(b);adjacency[b].add(a);
  }
  links.sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
  const oldCenter=previous.get(ordered[center]),origin=validPoint(oldCenter)?oldCenter:{x:0,y:0};
  const anchors=ordered.map(id=>{const p=previous.get(id);return validPoint(p)?{x:p.x-origin.x,y:p.y-origin.y}:null;});
  const points=ordered.map((id,i)=>{
    if(i===center)return {x:0,y:0};
    if(anchors[i])return {...anchors[i]};
    const angle=i*GOLDEN_ANGLE+seed(id)*.7,radius=90*Math.sqrt(i+1);
    const neighbors=[...adjacency[i]].filter(j=>anchors[j]).sort((a,b)=>a-b);
    if(neighbors.length){
      return {x:neighbors.reduce((v,j)=>v+anchors[j].x,0)/neighbors.length+Math.cos(angle)*140,
        y:neighbors.reduce((v,j)=>v+anchors[j].y,0)/neighbors.length+Math.sin(angle)*140};
    }
    return {x:Math.cos(angle)*radius*Math.sqrt(aspect),y:Math.sin(angle)*radius/Math.sqrt(aspect)};
  });
  const springs=links.map(([a,b])=>({a,b,length:140+seed(ordered[a]+'|'+ordered[b])*55+
    7*Math.sqrt(Math.max(adjacency[a].size,adjacency[b].size))}));
  // Bounded relaxation runs once per topology change, not continuously on screen.
  const iterations=anchors.some(Boolean)?180:260;
  for(let step=0;step<iterations;step++){
    const force=points.map(()=>({x:0,y:0})),temperature=1-step/iterations;
    for(let a=0;a<points.length;a++)for(let b=a+1;b<points.length;b++){
      const p=points[a],q=points[b];let dx=p.x-q.x,dy=p.y-q.y;
      if(Math.abs(dx)+Math.abs(dy)<.01){dx=.1;dy=.17;}
      const distance=Math.max(1,Math.hypot(dx,dy)),repulsion=1050/distance;
      let fx=dx/distance*repulsion,fy=dy/distance*repulsion;
      const overlapX=CARD_WIDTH-Math.abs(dx),overlapY=CARD_HEIGHT-Math.abs(dy);
      if(overlapX>0&&overlapY>0){
        if(overlapX<overlapY)fx+=Math.sign(dx||1)*overlapX*.55;
        else fy+=Math.sign(dy||1)*overlapY*.55;
      }
      force[a].x+=fx;force[a].y+=fy;force[b].x-=fx;force[b].y-=fy;
    }
    for(const {a,b,length} of springs){
      const dx=points[b].x-points[a].x,dy=points[b].y-points[a].y,distance=Math.max(1,Math.hypot(dx,dy));
      const attraction=(distance-length)*.09,fx=dx/distance*attraction,fy=dy/distance*attraction;
      force[a].x+=fx;force[a].y+=fy;force[b].x-=fx;force[b].y-=fy;
    }
    for(let i=0;i<points.length;i++){
      if(i===center||anchors[i])continue;
      const p=points[i],f=force[i];f.x-=p.x*.012/aspect;f.y-=p.y*.012*aspect;
      const length=Math.hypot(f.x,f.y),limit=2+temperature*16,scale=length?Math.min(limit,length)/length:0;
      p.x+=f.x*scale;p.y+=f.y*scale;
    }
  }
  // Resolve remaining card collisions without snapping to rows or columns.
  const placement=ordered.map((_,i)=>i).sort((a,b)=>Number(b===center)-Number(a===center)||
    Number(!!anchors[b])-Number(!!anchors[a])||adjacency[b].size-adjacency[a].size||a-b);
  const placed=[];
  for(const i of placement){
    const initial={...points[i]};let candidate=initial,attempt=0;
    while(!anchors[i]&&placed.some(p=>overlaps(candidate,p))&&attempt<ordered.length*24){
      attempt++;const angle=attempt*GOLDEN_ANGLE+seed(ordered[i])*Math.PI*2,radius=24*Math.sqrt(attempt);
      candidate={x:initial.x+Math.cos(angle)*radius,y:initial.y+Math.sin(angle)*radius};
    }
    if(!anchors[i]&&placed.some(p=>overlaps(candidate,p)))candidate={x:Math.max(...placed.map(p=>p.x))+CARD_WIDTH+1,y:initial.y};
    points[i]=candidate;placed.push(candidate);
  }
  return ids.map(id=>{const p=points[index.get(id)];return {x:p.x+origin.x,y:p.y+origin.y};});
}

// Retain count-only callers; the live map passes actual relationship topology.
export function nodePositions(count,width,height){const ids=Array.from({length:count},(_,i)=>String(i));return graphPositions(ids,[],width,height,ids[0]);}
export function fanPositions(count,width,height){
  const ids=Array.from({length:count},(_,i)=>String(i));
  return graphPositions(ids,ids.slice(1).map(id=>({source_company_id:ids[0],target_company_id:id})),width,height,ids[0]);
}

// At overview zoom, use the available horizontal space while keeping each
// neighborhood's relative positions and the current camera/pan unchanged.
export function overviewHorizontalPositions(base,width,zoom,panX){
  if(base.size<2||width<900||zoom>=.32)return base;
  const xs=[...base.values()].map(p=>p.x),left=Math.min(...xs),right=Math.max(...xs);
  if(right-left<1)return base;
  const middle=(left+right)/2,screenMiddle=middle*zoom+panX;
  const margin=Math.min(140,Math.max(48,width*.07));
  const leftSpace=(middle-left)*zoom,rightSpace=(right-middle)*zoom;
  const factor=Math.max(1,Math.min(4.5,
    leftSpace?(screenMiddle-margin)/leftSpace:4.5,
    rightSpace?(width-margin-screenMiddle)/rightSpace:4.5));
  const progress=Math.max(0,Math.min(1,(.32-zoom)/.17));
  const eased=progress*progress*(3-2*progress),stretch=1+(factor-1)*eased;
  return new Map([...base].map(([id,p])=>[id,{x:middle+(p.x-middle)*stretch,y:p.y}]));
}

// Prefer a short curve that misses unrelated company cards. A straight line
// through another company can falsely suggest a relationship to that company.
export function edgeBend(a,b,positions) {
  const dx=b.x-a.x,dy=b.y-a.y,len=Math.hypot(dx,dy)||1;
  const others=positions.filter(p=>p!==a&&p!==b);
  let best=0,bestScore=Infinity;
  for(const bend of [0,90,-90,180,-180,270,-270,360,-360,480,-480]){
    const cx=(a.x+b.x)/2-dy/len*bend,cy=(a.y+b.y)/2+dx/len*bend;
    let hits=0;
    for(const p of others){
      for(let i=1;i<40;i++){const t=i/40,u=1-t,x=u*u*a.x+2*u*t*cx+t*t*b.x,y=u*u*a.y+2*u*t*cy+t*t*b.y;
        if(Math.abs(x-p.x)<62&&y>p.y-40&&y<p.y+86){hits++;break;}
      }
    }
    const score=hits*10000+Math.abs(bend);
    if(score<bestScore){bestScore=score;best=bend;}
    if(!hits)break;
  }
  return best;
}

// Keep opaque, single-line labels off their strokes and away from endpoint logos.
// A label centered on a short horizontal edge can otherwise conceal it entirely.
export function edgeLabelPlacement(a,b) {
  const dx=Math.abs(b.x-a.x),dy=Math.abs(b.y-a.y),vertical=dy>dx;
  const labelWidth=vertical?220:Math.max(64,Math.min(300,dx-110));
  return {labelWidth,labelX:vertical?labelWidth/2+14:0,labelY:vertical?0:-22};
}
