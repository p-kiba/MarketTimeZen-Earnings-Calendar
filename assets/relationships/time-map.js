// Announcement time is depth; this is not a reconstruction of active contracts.
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!=null)n.textContent=text;if(cls)n.className=cls;return n;};
const cameras=new Map(),images=new Map(),cleanups=new WeakMap(),controllers=new WeakMap();
let showPast=true;
export function selectTimeCompany(root,id){controllers.get(root)?.select(id);}
export function inspectTimeRelation(root,id,active){controllers.get(root)?.inspect(id,active);}
export function disposeTimeMap(root){cleanups.get(root)?.();cleanups.delete(root);controllers.delete(root);}
export function renderTimeMap(root,{rows,events,positions,center,year,lang,name,logo,color,label,eventLabel,selected,onYear,onCompany,onEvent}){
 disposeTimeMap(root);root.replaceChildren();
 const t=(ja,en)=>lang==='ja'?ja:en,byId=new Map(rows.map(r=>[r.relationship_id,r]));
 const dated=events.filter(e=>e.event_type!=='correction'&&/^\d{4}-\d{2}-\d{2}$/.test(e.announced_date||'')&&e.relationship_ids.some(id=>byId.has(id)));
 const years=[...new Set(dated.map(e=>+e.announced_date.slice(0,4)))].sort((a,b)=>a-b);
 if(!years.length){root.append(el('p',t('この範囲には発表日付きの情報が未収録です。通常マップでつながりを展開してください。','No dated announcements in this neighborhood. Expand the normal map.'),'mtz-time-empty'));return;}
 const min=years[0],max=years.at(-1);let current=Math.max(min,Math.min(max,+year||max));
 let time=current,targetTime=current,lastPaint=0;
 const reducedMotion=window.matchMedia('(prefers-reduced-motion: reduce)').matches;
 const camera=cameras.get(center)||{yaw:.25,pitch:.12,zoom:1};cameras.set(center,camera);
 if(camera.time!=null&&Math.round(camera.time)===current){time=targetTime=camera.time;}
 let selectedId=selected,hovered=null,inspected=null;
 controllers.set(root,{select(id){selectedId=id;draw();},inspect(id,active){inspected=active?id:null;draw();}});
 const bar=el('div',null,'mtz-time-toolbar'),heading=el('div');heading.append(el('span',t('時間軸モード · 試験版','TIME AXIS · EXPERIMENTAL'),'mtz-time-eyebrow'));const title=el('strong');heading.append(title);
 const controls=el('div',null,'mtz-time-controls'),select=el('select');select.setAttribute('aria-label',t('発表年','Announcement year'));
 for(let y=min;y<=max;y++){const o=el('option',String(y));o.value=y;select.append(o);}controls.append(select);
 const past=el('label',null,'mtz-time-past'),check=el('input');check.type='checkbox';check.checked=showPast;past.append(check,document.createTextNode(t('過去2年を重ねる','Include previous two years')));bar.append(heading,controls,past);
 const scene=el('div',null,'mtz-time-volume'),canvas=el('canvas'),rail=el('div',null,'mtz-time-rail');canvas.tabIndex=0;canvas.setAttribute('aria-label',t('立体時間マップ。ドラッグまたは矢印キーで回転、ホイールで時間を移動、プラス・マイナスで拡大縮小。詳細は下の発表一覧からも開けます。','3D timeline. Drag or arrow keys to orbit; wheel to travel in time; plus/minus to zoom. Details are also available in the announcement list.'));
 const nav=el('div',null,'mtz-time-orbit');function button(label,action){const b=el('button',label);b.type='button';b.onclick=action;return b;}
 nav.append(button('−',()=>zoom(.85)),button('+',()=>zoom(1.18)),button(t('視点をリセット','Reset view'),()=>{Object.assign(camera,{yaw:.25,pitch:.12,zoom:1});draw();}));scene.append(canvas,rail,nav);
 const scrub=el('input',null,'mtz-time-range');scrub.type='range';scrub.min=min;scrub.max=max;scrub.step='.01';scrub.value=current;scrub.setAttribute('aria-label',t('時間を移動（左が過去、右が新しい発表）','Travel in time (past to present)'));scrub.oninput=()=>travel(+scrub.value);
 const hint=el('p',t('ドラッグで回転 · スクロールで時間を移動（下：過去／上：新しい年） · ロゴで企業を選択 · 線で関係の詳細','Drag to orbit · Scroll through time (down: past / up: newer) · Select logos for company actions · Lines for details'),'mtz-time-inspector');
 const list=el('details',null,'mtz-time-events'),summary=el('summary'),items=el('div');list.append(summary,items);
 root.append(bar,scene,scrub,hint,list,el('p',t('奥行きは発表年です。注目する年を手前に、過去を奥に表示します。点線は同じ企業を結びます。過去の表示は契約終了を意味しません。発表日がない情報は対象外です。詳細ページは現在の収録情報です。','Depth represents announcement year. The focused year is in front; past years recede. Dotted traces connect the same company. Fading does not mean a contract ended. Undated records are excluded. Detail pages show current records.'),'mtz-time-note'));
 const ctx=canvas.getContext('2d');let nodes=[],edges=[],traces=[],hits=[],frame=0,dead=false,width=1,height=1;
 const pts=[...positions.values()],xs=pts.map(p=>p.x),zs=pts.map(p=>p.y),cx=(Math.min(...xs)+Math.max(...xs))/2,cz=(Math.min(...zs)+Math.max(...zs))/2,span=Math.max(1,Math.max(...xs)-Math.min(...xs),Math.max(...zs)-Math.min(...zs));
 function entries(y){const groups=new Map();for(const e of dated.filter(e=>+e.announced_date.slice(0,4)===y))for(const id of e.relationship_ids){if(!byId.has(id))continue;if(!groups.has(id))groups.set(id,{row:byId.get(id),events:[]});groups.get(id).events.push(e);}return [...groups.values()];}
 function description(e){return `${name(e.row.source_company_id)} → ${name(e.row.target_company_id)} · ${e.events.map(x=>`${x.announced_date} ${eventLabel(x.event_type)}`).join(' / ')}`;}
 function rebuild(){hint.textContent=t('ドラッグで回転 · スクロールで時間を移動（下：過去／上：新しい年） · ロゴで企業を選択 · 線で関係の詳細','Drag to orbit · Scroll through time (down: past / up: newer) · Select logos for company actions · Lines for details');title.textContent=String(current);select.value=current;nodes=[];edges=[];traces=[];rail.replaceChildren();items.replaceChildren();const previous=new Map();
 for(let y=min;y<=max;y++){const depth=current-y;const active=entries(y),ids=new Set(active.flatMap(e=>[e.row.source_company_id,e.row.target_company_id])),local=new Map();
 const b=button(`${y}${active.length?'':t(' · 未収録',' · No records')}`,()=>change(y));b.classList.toggle('active',depth===0);if(Math.abs(depth)<=2)rail.prepend(b);
 for(const id of ids){const p=positions.get(id);if(!p)continue;const n={id,x:(p.x-cx)/span*680,y:-(p.y-cz)/span*560,z:0,year:y,depth};nodes.push(n);local.set(id,n);if(previous.has(id))traces.push([previous.get(id),n]);previous.set(id,n);const url=logo(id);if(url&&!images.has(url)){const img=new Image();images.set(url,img);img.onload=draw;img.onerror=draw;img.src=url;}}
 for(const entry of active){const a=local.get(entry.row.source_company_id),b=local.get(entry.row.target_company_id);if(a&&b)edges.push({a,b,entry,depth});}
 }
 const active=entries(current);summary.textContent=t(`${current}年の発表 · ${active.length}件の関係（一覧を開く）`,`${current} · ${active.length} relationships (open list)`);
 for(const e of active){items.append(button(description(e),()=>onEvent(e)));}
 const companyIds=[...new Set(active.flatMap(e=>[e.row.source_company_id,e.row.target_company_id]))];for(const id of companyIds)items.append(button(t('企業を選択: ','Select company: ')+name(id),()=>onCompany(id)));
 draw();}
 function travel(y){targetTime=Math.max(min,Math.min(max,y));scrub.value=targetTime;draw();}
 function change(y){travel(y);}select.onchange=()=>change(+select.value);check.onchange=()=>{showPast=check.checked;rebuild();};
 function opacity(n){const age=time-n.year;if(age<0)return Math.max(0,1+age*2);if(!showPast)return Math.max(0,1-age*2);return Math.max(0,1-age/2.8)*Math.exp(-age*.65);}
 function project(n){const age=time-n.year,depth=age*420,x=n.x*Math.cos(camera.yaw)+depth*Math.sin(camera.yaw),z=-n.x*Math.sin(camera.yaw)+depth*Math.cos(camera.yaw),y=n.y*Math.cos(camera.pitch)-z*Math.sin(camera.pitch),d=n.y*Math.sin(camera.pitch)+z*Math.cos(camera.pitch),s=900/Math.max(250,1000+d)*Math.min(width/850,height/650)*camera.zoom;return {x:width/2+x*s,y:height/2-y*s,s,d};}
 function draw(){if(dead||frame)return;frame=requestAnimationFrame(paint);}
 function paint(now){frame=0;if(dead)return;
 const dt=Math.min(50,lastPaint?now-lastPaint:16);lastPaint=now;
 time=reducedMotion?targetTime:time+(targetTime-time)*(1-Math.exp(-dt/110));if(Math.abs(time-targetTime)<.002)time=targetTime;
 const focus=Math.round(time);if(focus!==current){current=focus;onYear(current);rebuild();}
 camera.time=time;scrub.setAttribute('aria-valuetext',String(current));
 ctx.clearRect(0,0,width,height);hits=[];const labelQueue=[];
 const projected=new Map(nodes.map(n=>[n,project(n)]));
 ctx.save();ctx.strokeStyle='rgba(114,215,247,.2)';ctx.lineWidth=1;ctx.setLineDash([2,7]);for(const [a,b] of traces){const alpha=Math.min(opacity(a),opacity(b));if(alpha<.02)continue;ctx.globalAlpha=alpha;const p=projected.get(a),q=projected.get(b);ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.stroke();}ctx.setLineDash([]);ctx.restore();
 for(const edge of [...edges].sort((a,b)=>b.depth-a.depth)){const alpha=opacity(edge.a);if(alpha<.02)continue;const p=projected.get(edge.a),q=projected.get(edge.b),dx=q.x-p.x,dy=q.y-p.y,len=Math.hypot(dx,dy);if(len<1)continue;const padA=Math.max(12,23*p.s),padB=Math.max(12,23*q.s);if(len<padA+padB)continue;const a={x:p.x+dx/len*padA,y:p.y+dy/len*padA},b={x:q.x-dx/len*padB,y:q.y-dy/len*padB};ctx.save();ctx.globalAlpha=alpha*.9;ctx.strokeStyle=ctx.fillStyle=color([edge.entry.row]);ctx.lineWidth=edge.depth?1:1.6;ctx.shadowColor=ctx.strokeStyle;ctx.shadowBlur=edge.depth?0:6;ctx.beginPath();ctx.moveTo(a.x,a.y);ctx.lineTo(b.x,b.y);ctx.stroke();if(edge.entry.row.direction==='directed'){const theta=Math.atan2(dy,dx);ctx.beginPath();ctx.moveTo(b.x,b.y);ctx.lineTo(b.x-8*Math.cos(theta-.4),b.y-8*Math.sin(theta-.4));ctx.lineTo(b.x-8*Math.cos(theta+.4),b.y-8*Math.sin(theta+.4));ctx.fill();}ctx.restore();hits.push({a,b,edge});
 const focused=selectedId&&[edge.a.id,edge.b.id].includes(selectedId),hover=hovered===edge.entry.row.relationship_id||inspected===edge.entry.row.relationship_id;
 if(hover||((focused||entries(current).length<=8)&&edge.a.year===current))labelQueue.push({edge,a,b,alpha,hover,focused});}
 for(const n of [...nodes].sort((a,b)=>projected.get(b).d-projected.get(a).d)){const alpha=opacity(n);if(alpha<.02)continue;const p=projected.get(n),size=Math.max(20,Math.min(66,44*p.s));ctx.save();ctx.globalAlpha=alpha;ctx.shadowColor='#68e7ff';ctx.shadowBlur=n.id===selectedId?28:n.depth?0:18;ctx.fillStyle='#fff';ctx.beginPath();ctx.roundRect(p.x-size/2,p.y-size/2,size,size,Math.max(4,size*.16));ctx.fill();ctx.shadowBlur=0;const img=images.get(logo(n.id));if(img?.complete&&img.naturalWidth){const scale=(size-6)/Math.max(img.naturalWidth,img.naturalHeight);ctx.drawImage(img,p.x-img.naturalWidth*scale/2,p.y-img.naturalHeight*scale/2,img.naturalWidth*scale,img.naturalHeight*scale);}else{ctx.fillStyle='#173049';ctx.font='bold 10px system-ui';ctx.textAlign='center';ctx.fillText(name(n.id).slice(0,5),p.x,p.y+4);}if(n.year===current){ctx.fillStyle='#e7f7ff';ctx.font='12px system-ui';ctx.textAlign='center';ctx.fillText(name(n.id),p.x,p.y+size/2+17);}ctx.restore();hits.push({n,p,size});}
 // Keep annotations outside logo/name rectangles and already placed labels.
 const occupied=hits.filter(h=>h.n).map(h=>({x:h.p.x-h.size/2-8,y:h.p.y-h.size/2-8,w:h.size+16,h:h.size+34}));
 const overlaps=(a,b)=>a.x<b.x+b.w&&a.x+a.w>b.x&&a.y<b.y+b.h&&a.y+a.h>b.y;
 ctx.font='12px system-ui';ctx.textAlign='center';
 for(const item of labelQueue.sort((a,b)=>Number(b.hover)-Number(a.hover)||Number(b.focused)-Number(a.focused))){
 const text=label(item.edge.entry.row);if(!text)continue;const lines=[];let line='';const maxWidth=Math.min(320,width-40);for(const char of text){if(line&&ctx.measureText(line+char).width>maxWidth){lines.push(line);line='';}line+=char;}if(line)lines.push(line);const w=Math.max(...lines.map(l=>ctx.measureText(l).width))+16,h=lines.length*17+8;
 let box=null;for(const fraction of [.5,.35,.65]){for(const offset of [-22,22,-48,48,-76,76]){const candidate={x:item.a.x+(item.b.x-item.a.x)*fraction-w/2,y:item.a.y+(item.b.y-item.a.y)*fraction+offset-h/2,w,h};if(candidate.x<8||candidate.x+w>width-8||candidate.y<8||candidate.y+h>height-8||occupied.some(b=>overlaps(candidate,b)))continue;box=candidate;break;}if(box)break;}
 if(!box)continue;occupied.push(box);ctx.save();ctx.globalAlpha=item.hover?1:Math.max(.65,item.alpha);ctx.fillStyle='#0c2137';ctx.beginPath();ctx.roundRect(box.x,box.y,w,h,5);ctx.fill();ctx.fillStyle='#e6f5ff';lines.forEach((line,i)=>ctx.fillText(line,box.x+w/2,box.y+17+i*17));ctx.restore();hits.push({a:item.a,b:item.b,edge:item.edge,box});
 }
 if(time!==targetTime)draw();
 }
 function zoom(f){camera.zoom=Math.max(.45,Math.min(2.8,camera.zoom*f));draw();}
 function hit(x,y){for(const h of [...hits].reverse()){if(h.n&&Math.abs(x-h.p.x)<h.size/2+4&&Math.abs(y-h.p.y)<h.size/2+4)return h;if(h.box&&x>=h.box.x&&x<=h.box.x+h.box.w&&y>=h.box.y&&y<=h.box.y+h.box.h)return h;if(h.edge){const dx=h.b.x-h.a.x,dy=h.b.y-h.a.y,u=Math.max(0,Math.min(1,((x-h.a.x)*dx+(y-h.a.y)*dy)/(dx*dx+dy*dy)));if(Math.hypot(x-h.a.x-u*dx,y-h.a.y-u*dy)<7)return h;}}}
 let pointer=null;canvas.onpointerdown=e=>{pointer={id:e.pointerId,x:e.clientX,y:e.clientY,startX:e.clientX,startY:e.clientY,moved:false};canvas.setPointerCapture(e.pointerId);};canvas.onpointermove=e=>{if(pointer){if(Math.hypot(e.clientX-pointer.startX,e.clientY-pointer.startY)>5)pointer.moved=true;camera.yaw+=(e.clientX-pointer.x)*.006;camera.pitch=Math.max(-.65,Math.min(.65,camera.pitch+(e.clientY-pointer.y)*.005));pointer.x=e.clientX;pointer.y=e.clientY;draw();}else{const r=canvas.getBoundingClientRect(),h=hit(e.clientX-r.left,e.clientY-r.top);canvas.style.cursor=h?'pointer':'grab';hovered=h?.edge?.entry.row.relationship_id||null;draw();if(h)hint.textContent=h.n?`${name(h.n.id)} · ${h.n.year}`:`${label(h.edge.entry.row)} · ${description(h.edge.entry)}`;}};
 canvas.onpointerup=e=>{if(pointer&&!pointer.moved){const r=canvas.getBoundingClientRect(),h=hit(e.clientX-r.left,e.clientY-r.top);if(h?.n){selectedId=h.n.id;draw();onCompany(h.n.id);}else if(h?.edge)onEvent(h.edge.entry);}pointer=null;};canvas.onpointercancel=()=>pointer=null;
 canvas.addEventListener('wheel',e=>{e.preventDefault();const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?height:1);travel(targetTime-delta/600);},{passive:false});canvas.onkeydown=e=>{if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','PageUp','PageDown','+','-','='].includes(e.key)){e.preventDefault();if(e.key==='ArrowLeft')camera.yaw-=.1;else if(e.key==='ArrowRight')camera.yaw+=.1;else if(e.key==='ArrowUp')camera.pitch=Math.min(.65,camera.pitch+.1);else if(e.key==='ArrowDown')camera.pitch=Math.max(-.65,camera.pitch-.1);else if(e.key==='PageUp')travel(targetTime+1);else if(e.key==='PageDown')travel(targetTime-1);else zoom(e.key==='-'?.85:1.18);draw();}};
 const observer=new ResizeObserver(()=>{const r=canvas.getBoundingClientRect();width=r.width;height=r.height;const dpr=Math.min(2,window.devicePixelRatio||1);canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);draw();});observer.observe(canvas);cleanups.set(root,()=>{dead=true;observer.disconnect();cancelAnimationFrame(frame);});rebuild();
}
