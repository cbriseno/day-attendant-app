/* Screenshot presentation only. Originals live in WeakMaps, never in DOM attributes. */
(() => {
'use strict';
const root=document.documentElement, key='day-attendant-anonymize';
const attrs=['title','aria-label','alt','placeholder','value'];
const originals=new WeakMap(), runs=new WeakMap(), textOriginals=new WeakMap(), candidates=new Map();
const generated=new WeakSet(), controls=new WeakMap(), observed=new Set(),buttons=new WeakMap();
const words={en:['amber','beam','cube','delta','echo','glow','halo','isle','loop','mist','orbit','tile'],es:['ámbar','bruma','cubo','delta','eco','giro','hilo','isla','marea','nube','onda','vela']};
const candidateWidths=new Map();
const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');
let generation=0,ready=Promise.resolve(),timing={},active=false,busy=false,queued=false,dirty=new Set(),known=new Set(),templates=[],lang='en';
const hash=s=>{let h=2166136261;for(const c of s){h=Math.imul(h^c.codePointAt(0),16777619)}return h>>>0};
function fake(s){
 const n=Math.min(64,Array.from(s).length),k=lang+':'+n;let list=candidates.get(k);
 if(!list){list=words[lang].map(w=>Array.from(w.repeat(Math.ceil(n/w.length)+1)).slice(0,n).join(''));candidates.set(k,list)}
 const h=hash(s),v=list[h%list.length];return v===s?list[(h+1)%list.length]:v;
}
function catalog(){
 if(candidateWidths.size>4096)candidateWidths.clear();
 lang=root.lang==='es'?'es':'en';known=new Set();templates=[];
 // Catalogs include both text and legacy HTML fragments. Extract authored copy, never rendered data.
 for(const value of Object.values(globalThis.dayTranslations[lang])){
  const template=document.createElement('template');template.innerHTML=value;
  const texts=[value];const walker=document.createTreeWalker(template.content,NodeFilter.SHOW_TEXT);
  while(walker.nextNode())texts.push(walker.currentNode.data);
  for(const el of template.content.querySelectorAll('*'))for(const a of attrs)if(el.hasAttribute(a))texts.push(el.getAttribute(a));
  for(const text of texts){if(!text.includes('{')){known.add(text.trim());continue}
   const parts=text.split(/\{\w+\}/g);if(!parts.some(Boolean))continue;
   const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
   templates.push({parts,re:new RegExp('^'+parts.map(escape).join('([\\s\\S]*?)')+'$')});
  }
 }
}
function segments(s,el,surface='text'){
 if(!s.trim())return [{s,safe:true}];
 const privateHost=el.closest('[data-anon-private]'),privateText=privateHost&&(privateHost.getAttribute('data-anon-private')===''||privateHost.getAttribute('data-anon-private').split(' ').includes(surface));
 const safe=(el.getAttribute('data-anon-safe')||'').split(' ').includes(surface);
 if(safe||!privateText&&known.has(s.trim()))return [{s,safe:true}];
 if(!privateText)for(const {parts,re} of templates){if(!s.startsWith(parts[0])||!s.endsWith(parts.at(-1)))continue;const m=s.match(re);if(m){const out=[];parts.forEach((p,i)=>{if(p)out.push({s:p,safe:true});if(i<parts.length-1)out.push({s:m[i+1],safe:false})});return out}}
 return [{s,safe:false}];
}
const replacement=(s,el,surface)=>segments(s,el,surface).map(p=>p.safe?p.s:p.s.replace(/\S+/gu,fake)).join('');
function remember(el,name,value,masked){let m=originals.get(el);if(!m){m=new Map();originals.set(el,m)}m.set(name,{value,masked})}
function scrubAttributes(el){
 for(const name of attrs){if(!el.hasAttribute(name))continue;const source=el.getAttribute(name);if(name==='value'&&(chromeValue(el,source)||dateValue(el,source)))continue;const old=originals.get(el)?.get(name);if(old?.masked===source)continue;
  const masked=replacement(source,el,name);if(source!==masked){remember(el,name,source,masked);el.setAttribute(name,masked)}else originals.get(el)?.delete(name);
 }
}
const presentationSelect=el=>['locale-choice','theme-choice','palette-choice','order-choice'].includes(el.id);
const chromeValues=new WeakMap([...document.querySelectorAll('#locale-choice,#theme-choice,#palette-choice,#order-choice')].map(el=>[el,new Set([...el.options].map(o=>o.value))]));
const chromeValue=(el,value)=>chromeValues.get(el.tagName==='OPTION'?el.parentElement:el)?.has(value);
const dateValue=(el,value)=>el.matches('input[type=date],input[type=datetime-local],input[type=time]')&&/^(?:\d{4}-\d{2}-\d{2}(?:T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)?|\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?)$/.test(value);
function scrubControl(el,cache){
 if(el.matches('button[type=submit],#send-message,#backup-create,#recovery-complete,#chat-clear,#undo,[data-review-action],[data-suggestion-action],[data-reopen-id]')){if(!buttons.has(el))buttons.set(el,el.disabled);el.disabled=true}
 if(!el.matches('input,textarea,select,option'))return;
 if(!controls.has(el))controls.set(el,{readOnly:el.readOnly,aria:el.getAttribute('aria-readonly'),valueAttr:el.getAttribute('value'),width:el.style.width,height:el.style.height,box:el.style.boxSizing});
 const isPresentation=presentationSelect(el)||el.tagName==='OPTION'&&presentationSelect(el.parentElement);
 const box=cache.get(el)?.rect;if(el.tagName==='SELECT'&&!isPresentation&&box?.width){const saved=controls.get(el);saved.frozenWidth=box.width+'px';saved.frozenHeight=box.height+'px';el.style.boxSizing='border-box';el.style.width=saved.frozenWidth;el.style.height=saved.frozenHeight}
 if(!isPresentation&&el.tagName!=='OPTION'){if('readOnly'in el)el.readOnly=true;el.setAttribute('aria-readonly','true')}
 const old=originals.get(el)?.get('$value'),source=el.value;
 if(old?.masked===source)return;
 const masked=chromeValue(el,source)||dateValue(el,source)?source:replacement(source,el,'value');
 if(source!==masked){rawValue(el,masked);remember(el,'$value',source,el.value)}else originals.get(el)?.delete('$value');
}
const valueDescriptors=new Map();
function rawValue(el,value){const d=valueDescriptors.get(el.constructor);if(d)d.set.call(el,value)}
// MutationObserver cannot see assignments to .value. Observe those setters as well, before the next paint.
for(const C of [HTMLInputElement,HTMLTextAreaElement,HTMLSelectElement,HTMLOptionElement]){
 const d=Object.getOwnPropertyDescriptor(C.prototype,'value');valueDescriptors.set(C,d);
 Object.defineProperty(C.prototype,'value',{...d,set(value){d.set.call(this,value);if(active&&this.isConnected){originals.get(this)?.delete('$value');schedule(this)}}});
}
function styleFor(el,cache){
 if(cache.has(el))return cache.get(el);const c=getComputedStyle(el);
 const style={font:c.font,spacing:parseFloat(c.letterSpacing)||0,wordSpacing:parseFloat(c.wordSpacing)||0,width:el.clientWidth,rect:el.tagName==='SELECT'?el.getBoundingClientRect():null,svgWidth:el.getComputedTextLength?.()};cache.set(el,style);return style;
}
function width(s,style){if(ctx.font!==style.font)ctx.font=style.font;return ctx.measureText(s).width+Math.max(0,Array.from(s).length-1)*style.spacing}
function maskNode(node,cache,writes){
 const el=node.parentElement;if(!el||!node.data.trim()||el.closest('script,style,template'))return;
 if(textOriginals.get(node)?.masked===node.data)return;
 const source=node.data,parts=segments(source,el);if(parts.every(p=>p.safe))return;
 if(el.namespaceURI!=='http://www.w3.org/1999/xhtml'||el.closest('option,textarea')){
  const masked=replacement(source,el,'text');writes.push(()=>{if(node.data!==source)return;textOriginals.set(node,{source,masked});if(el.getComputedTextLength){const w=cache.get(el)?.svgWidth;for(const [a,v] of [['textLength',String(w)],['lengthAdjust','spacingAndGlyphs']]){remember(el,a,el.getAttribute(a),v);el.setAttribute(a,v)}}node.data=masked});return;
 }
 const style=styleFor(el,cache),host=document.createElement('span');generated.add(host);runs.set(host,node);
 host.style.cssText='display:inline;min-width:0';
 for(const p of parts){if(p.safe){host.append(document.createTextNode(p.s));continue}
  // Keep whitespace and break opportunities, including hyphens and paths. Long words are split
  // into graphemes only when necessary, keeping work linear and candidate storage bounded.
  for(const chunk of p.s.split(/(\s+|(?<=[\/-]))/u)){if(!chunk)continue;if(/^\s+$/u.test(chunk)){host.append(document.createTextNode(chunk));continue}
   const chunkWidth=width(chunk,style),pieces=style.width&&chunkWidth>style.width?Array.from(chunk):[chunk];
   for(const word of pieces){const outer=document.createElement('span'),v=fake(word),w=pieces.length===1?chunkWidth:width(word,style),ck=lang+':'+v+':'+style.font;
    let vw=candidateWidths.get(ck);if(vw===undefined){if(ctx.font!==style.font)ctx.font=style.font;vw=ctx.measureText(v).width;candidateWidths.set(ck,vw)}
    if(Math.abs(w-vw)<.05){host.append(document.createTextNode(v));continue}
    // One inline box per word: spacing fits its glyphs to the measured width without another DOM layer.
    outer.style.cssText='display:inline-block;white-space:pre;width:'+w+'px;letter-spacing:'+((w-vw)/Array.from(v).length)+'px';
    outer.textContent=v;host.append(outer);
   }
  }
 }
 writes.push(()=>{if(node.data===source)node.replaceWith(host)});
}
function collect(container,texts,elements){
 const visit=el=>{if(el.matches('script,style,template'))return false;elements.push(el);if(generated.has(el))return false;if(el.shadowRoot){watch(el.shadowRoot);collect(el.shadowRoot,texts,elements)}return true};
 if(container.nodeType===Node.TEXT_NODE){texts.push(container);return}
 if(container.nodeType===Node.ELEMENT_NODE&&!visit(container))return;
 const walker=document.createTreeWalker(container,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT,{acceptNode:n=>n.nodeType===1&&(generated.has(n)||n.matches('script,style,template'))?NodeFilter.FILTER_REJECT:NodeFilter.FILTER_ACCEPT});
 while(walker.nextNode()){const n=walker.currentNode;if(n.nodeType===1)visit(n);else texts.push(n)}
}
function watch(node){if(!observed.has(node))observed.add(node);observer.observe(node,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:[...attrs,'lang']})}
function reconnect(){if(active)for(const node of observed){if(node.isConnected)watch(node);else observed.delete(node)}}
function flush(){
 queued=false;if(!active||busy)return;
 if(dirty.has(root)){ready=refresh();return}
 const roots=[...dirty].filter(node=>{for(let p=node.parentNode;p;p=p.parentNode)if(dirty.has(p))return false;return node.isConnected});dirty.clear();
 ready=sweep(roots);
}
async function sweep(roots){
 const epoch=generation,start=performance.now(),texts=[],elements=[],cache=new Map();busy=true;pauseObserver();
 for(const node of roots)collect(node,texts,elements);
 const staged=texts.length>100;if(staged)root.setAttribute('data-anon-loading','');
 let maxBatch=performance.now()-start,batches=0;
 const frame=()=>new Promise(resolve=>requestAnimationFrame(resolve));
 async function phase(items,fn){
  for(let i=0;i<items.length;){if(epoch!==generation)return false;pauseObserver();const begin=performance.now();
   do{fn(items[i++])}while(i<items.length&&(!staged||performance.now()-begin<12));
   // Include style/layout in the pause measurement, rather than timing DOM writes alone.
   if(staged)document.body.getBoundingClientRect();maxBatch=Math.max(maxBatch,performance.now()-begin);batches++;reconnect();
   if(staged&&i<items.length)await frame();
  }return epoch===generation;
 }
 try{
  // All geometry reads precede value/attribute changes and detached-node calculation.
  if(!await phase(elements,el=>{if(el.tagName==='SELECT')styleFor(el,cache)}))return;
  if(!await phase(texts,node=>{if(node.parentElement)styleFor(node.parentElement,cache)}))return;
  if(!await phase(elements,el=>{scrubControl(el,cache);scrubAttributes(el)}))return;
  const writes=[];if(!await phase(texts,node=>maskNode(node,cache,writes)))return;
  if(!await phase(writes,write=>write()))return;
  timing={totalMs:performance.now()-start,maxBatchMs:maxBatch,batches,staged};
 }finally{if(epoch===generation){busy=false;reconnect();if(dirty.size){const pending=[...dirty];dirty.clear();if(pending.includes(root))await refresh();else await sweep(pending)}root.removeAttribute('data-anon-loading')}}
}

function schedule(node){if(!active)return;dirty.add(node);if(!queued){queued=true;queueMicrotask(flush)}}
function consume(records){for(const r of records){if(r.type==='childList')for(const n of r.addedNodes)schedule(n);else if(r.type==='characterData'){textOriginals.delete(r.target);schedule(r.target)}else schedule(r.target)}}
const observer=new MutationObserver(consume);
// Disconnect discards queued records. Drain first: a framework microtask may have mutated
// another branch after the observer callback queued our sweep, but before that sweep runs.
function pauseObserver(){consume(observer.takeRecords());observer.disconnect()}
// There is currently no shadow DOM in the app; future open roots get the same treatment.
const attach=Element.prototype.attachShadow;
Element.prototype.attachShadow=function(options){const shadow=attach.call(this,options);if(active&&options.mode==='open'){watch(shadow);schedule(shadow)}return shadow};
function restore(container){
 const visit=node=>{if(runs.has(node)){node.replaceWith(runs.get(node));return}
  const saved=textOriginals.get(node);if(saved){if(node.data===saved.masked)node.data=saved.source;textOriginals.delete(node)}
  const m=originals.get(node),c=controls.get(node);
  if(node.nodeType===1){if(buttons.has(node)){node.disabled=buttons.get(node);buttons.delete(node)}
   if(m)for(const [name,v] of m)if(name!=='$value'&&node.getAttribute(name)===v.masked){if(v.value===null)node.removeAttribute(name);else node.setAttribute(name,v.value)}
   if(c){if(c.frozenWidth&&node.style.width===c.frozenWidth){node.style.width=c.width;node.style.height=c.height;node.style.boxSizing=c.box}if('readOnly'in node)node.readOnly=c.readOnly;if(c.aria===null)node.removeAttribute('aria-readonly');else node.setAttribute('aria-readonly',c.aria);controls.delete(node)}
   if(node.shadowRoot)restore(node.shadowRoot);
  }
  for(const child of [...node.childNodes])visit(child);
  const v=m?.get('$value');if(v&&node.value===v.masked)rawValue(node,v.value);
  if(node.nodeType===1&&node.tagName==='OPTION'&&c?.valueAttr===null)node.removeAttribute('value');
  originals.delete(node);
 };visit(container);
}

async function refresh(notify=false){
 generation++;busy=true;pauseObserver();root.setAttribute('data-anon-loading','');
 restore(document.body);dirty.clear();catalog();
 if(notify)document.dispatchEvent(new Event('day-anonymize-change'));
 if(active){observed.clear();watch(document.body);watch(root);await sweep([document.body])}
 else{busy=false;root.removeAttribute('data-anon-loading')}
}
function setActive(on){
 active=!!on;try{sessionStorage.setItem(key,active?'1':'0')}catch{}
 root.toggleAttribute('data-anonymize',active);document.getElementById('anonymize-toggle').setAttribute('aria-pressed',String(active));
 ready=refresh(true);return ready;
}
// Readonly controls retain focus. Submit/input handlers cannot read and save a mask.
for(const type of ['beforeinput','input','change','submit','keydown','mousedown','click','focusout'])document.addEventListener(type,e=>{
 if(!active)return;const el=e.target;
 if(el.matches?.('#anonymize-toggle')||presentationSelect(el))return;
 const edit=el.matches?.('input,textarea,select,[contenteditable=true]');
 if(type==='submit'||edit&&(type!=='keydown'||!['Tab','Escape','ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key))){if(type!=='focusout')e.preventDefault();e.stopImmediatePropagation()}
},true);
const toggle=document.getElementById('anonymize-toggle');toggle.onclick=()=>setActive(!active);
window.addEventListener('resize',()=>{if(active)ready=refresh()});document.fonts?.addEventListener('loadingdone',()=>{if(active)ready=refresh()});
globalThis.dayAnonymize={get active(){return active},get ready(){return (async()=>{for(;;){const pending=ready;await pending;await new Promise(queueMicrotask);if(pending===ready&&!busy&&!dirty.size)return}})()},get timing(){return timing},value:el=>originals.get(el)?.get('$value')?.value??el.value,setActive,refresh:()=>{ready=refresh();return ready}};
let stored=false;try{stored=sessionStorage.getItem(key)==='1'}catch{}setActive(stored);
})();
