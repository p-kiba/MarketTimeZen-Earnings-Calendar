// Hysteresis keeps small wheel/pinch movements from flickering at a boundary.
export function disclosureDepth(ratio, previous=1){
  let depth=previous;
  if(depth===1&&ratio<=.72)depth=2;
  if(depth===2&&ratio<=.46)depth=3;
  if(depth===3&&ratio>=.56)depth=2;
  if(depth===2&&ratio>=.84)depth=1;
  return depth;
}
export function neighborhoodDepths(ids,pairs,center){
  const adjacent=new Map(ids.map(id=>[id,[]]));
  for(const [a,b] of pairs){if(adjacent.has(a)&&adjacent.has(b)){adjacent.get(a).push(b);adjacent.get(b).push(a);}}
  const depths=new Map([[center,0]]),queue=[center];
  for(let i=0;i<queue.length;i++)for(const id of adjacent.get(queue[i])||[]){
    if(!depths.has(id)){depths.set(id,depths.get(queue[i])+1);queue.push(id);}
  }
  return depths;
}
