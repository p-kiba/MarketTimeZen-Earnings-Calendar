// Stable center-out lattice: each node has a separate label/tap area even at high density.
export function nodePositions(count,width,height) {
  const aspect=Math.max(.7,Math.min(3,width/Math.max(1,height)));
  const cols=Math.ceil(Math.sqrt(count*aspect)/2)*2+1;
  const rows=Math.ceil(count/cols/2)*2+3;
  const points=[];
  for(let y=-Math.floor(rows/2);y<=Math.floor(rows/2);y++)for(let x=-Math.floor(cols/2);x<=Math.floor(cols/2);x++)points.push({x:x*116,y:y*98});
  points.sort((a,b)=>(a.x/aspect)**2+a.y**2-((b.x/aspect)**2+b.y**2)||a.y-b.y||a.x-b.x);
  return points.slice(0,count);
}

// A single company's adjacency fans out to a rectangular perimeter. This
// uses the available viewport without shrinking 25 labels around a tall ellipse.
export function fanPositions(count,width,height) {
  if(count<=1)return [{x:0,y:0}].slice(0,count);
  const n=count-1,aspect=Math.max(1,Math.min(2.5,width/Math.max(1,height)));
  const cols=Math.max(2,Math.ceil(n*aspect/(2*(aspect+1))));
  const rows=Math.max(2,Math.ceil(n/2)-cols),rim=[];
  for(let x=0;x<cols;x++)rim.push({x,y:0});
  for(let y=0;y<rows;y++)rim.push({x:cols,y});
  for(let x=cols;x>0;x--)rim.push({x,y:rows});
  for(let y=rows;y>0;y--)rim.push({x:0,y});
  return [{x:0,y:0},...Array.from({length:n},(_,i)=>{
    const p=rim[Math.floor(i*rim.length/n)];return {x:(p.x-cols/2)*116,y:(p.y-rows/2)*98};
  })];
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
        if(Math.abs(x-p.x)<53&&Math.abs(y-p.y)<37){hits++;break;}
      }
    }
    const score=hits*10000+Math.abs(bend);
    if(score<bestScore){bestScore=score;best=bend;}
    if(!hits)break;
  }
  return best;
}
