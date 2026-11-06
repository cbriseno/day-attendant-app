// Run by test_dependency_ui.py in an isolated browser against disposable SQLite state.
await page.eval(async()=>{
 const rows=daySnapshot().tasks;window.u8ids=rows.map(t=>t.id);
 window.u8={times:[],checks:[],posts:0};const original=window.fetch;window.fetch=(url,opts)=>{if(opts?.method==='POST'&&url==='/api/proposals')u8.posts++;return original(url,opts)};
 window.u8test={
 check:(name,ok)=>{if(!ok)throw Error(name);u8.checks.push(name)},
 task:id=>daySnapshot().tasks.find(t=>t.id===id),
 el:id=>document.querySelector('[data-task-id="'+id+'"]'),
 wait:async fn=>{for(let i=0;i<150;i++){if(await fn())return;await new Promise(r=>setTimeout(r,40))}throw Error('save timeout')},
 saved:async()=>{await u8test.wait(async()=>{const s=await(await fetch('/api/state')).json();return s.data.revision===daySnapshot().revision&&s.data.lastFact?.id===daySnapshot().lastFact?.id&&s.data.tasks.every(t=>JSON.stringify(t.dependsOn)===JSON.stringify(u8test.task(t.id).dependsOn)&&JSON.stringify(t.relatedTo)===JSON.stringify(u8test.task(t.id).relatedTo))})},
 drag:(from,to,knob=false,kind='blocks')=>{const target=u8test.el(to),source=knob?document.querySelector('.link-knob'):u8test.el(from).querySelector('.port'),p=source.getBoundingClientRect(),q=target.getBoundingClientRect(),x=p.x+p.width/2,y=p.y+p.height/2,tx=q.x+q.width/2,ty=q.y+q.height/2;
 const options={bubbles:true,pointerType:'mouse',pointerId:31,isPrimary:true,button:0,buttons:1};const start=performance.now();source.dispatchEvent(new PointerEvent('pointerdown',{...options,clientX:x,clientY:y}));document.dispatchEvent(new PointerEvent('pointermove',{...options,clientX:tx,clientY:ty}));document.dispatchEvent(new PointerEvent('pointerup',{...options,buttons:0,clientX:tx,clientY:ty}));if(!knob){const choice=document.querySelector('[data-menu-act="relation-add"][data-value="'+kind+'"]:not([disabled])');if(choice){choice.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,isPrimary:true}));choice.click()}}u8.times.push({action:knob?'move':'create',ms:performance.now()-start})},
 select:(from,to,type='dep')=>{u8test.el(from).dispatchEvent(new PointerEvent('pointerover',{bubbles:true,pointerType:'mouse'}));const path=[...document.querySelectorAll('[data-link]')].find(x=>x.dataset.link===from+'|'+to+'|'+type);if(!path)throw Error('link missing '+from+' '+to);path.dispatchEvent(new MouseEvent('click',{bubbles:true}));u8test.check('select '+type,!!document.querySelector('.link-line.selected'))},
 click:selector=>{const start=performance.now();document.querySelector(selector).click();u8.times.push({action:selector,ms:performance.now()-start})}
 };return {ready:true}
});

console.log(JSON.stringify(await page.eval(`(async()=>{const [a,b,c,d,e]=u8ids;const {check,task,drag,saved,select,click,wait}=u8test;
 drag(a,b);check('create shown synchronously',task(b).dependsOn.includes(a));check('the linking style waits for the change to show',document.body.classList.contains('linking'));await saved();
 await new Promise(r=>setTimeout(r,260));check('the linking style leaves after the release',!document.body.classList.contains('linking'));
 drag(a,c);check('preserve existing prerequisite',task(c).dependsOn.includes(a)&&task(c).dependsOn.includes(b));await saved();
 const count=u8.posts;drag(c,a);check('cycle refused before saving',u8.posts===count&&!task(a).dependsOn.length);drag(a,b);check('duplicate refused before saving',u8.posts===count);drag(a,a);check('self link refused before saving',u8.posts===count);
 await new Promise(r=>setTimeout(r,30));select(a,c);click('[data-line="type"]');check('related shown synchronously',task(a).relatedTo.includes(c)&&task(c).relatedTo.includes(a)&&task(c).dependsOn.includes(b)&&!task(c).dependsOn.includes(a));await saved();
 click('#undo');await saved();check('undo type restores both lists',task(c).dependsOn.includes(a)&&!task(a).relatedTo.includes(c));
 select(a,c);click('[data-line="type"]');await saved();
 let [from,to]=[a,c].sort();select(from,to,'rel');
 if(from===c){const count=u8.posts;click('[data-line="type"]');check('type conversion cycle refused before saving',u8.posts===count);}
 drag(from,d,true);check('related move shown synchronously',task(from).relatedTo.includes(d)&&!task(from).relatedTo.includes(to));await saved();
 [from,to]=[from,d].sort();select(from,to,'rel');click('[data-line="type"]');await saved();check('converted back to blocking',task(to).dependsOn.includes(from));
 select(from,to);drag(from,e,true);check('move shown synchronously',task(e).dependsOn.includes(from)&&!task(to).dependsOn.includes(from));await saved();
 click('#undo');await saved();check('undo move restores both tasks',task(to).dependsOn.includes(from)&&!task(e).dependsOn.includes(from));
 select(from,to);drag(from,e,true);await saved();
 select(from,e);click('[data-line="remove"]');check('remove shown synchronously',!task(e).dependsOn.includes(from));await saved();
 click('#undo');await saved();check('undo remove restores relation',task(e).dependsOn.includes(from));
 check('unrequested link remains',task(c).dependsOn.includes(b));
 return u8;
})()`)));
// PHONE
if(await page.eval(()=>document.querySelector('#chat-dialog').open))await page.click('#chat-close');
const [a,b,c,d,e]=await page.eval(()=>u8ids);
const action=(id,name)=>'[data-id="'+id+'"][data-action="'+name+'"]';
await page.click(action(b,'dependencies'));
console.log(JSON.stringify(await page.eval(()=>{u8test.check('phone sheet opens from chip',!!document.querySelector('.row-menu.sheet'));return {sheet:true}})));
await page.click('[data-menu-act="link-go"][data-value="'+a+'"]');
await page.eval(()=>u8test.check('phone go to task',document.activeElement.dataset.id===u8ids[0]));
await page.click(action(b,'dependencies'));
await page.click('[data-menu-act="link-remove"][data-value="dep:'+a+'"]');
await page.eval(async()=>{u8test.check('phone remove shown immediately',!u8test.task(u8ids[1]).dependsOn.includes(u8ids[0]));await u8test.saved()});
await page.click('[data-menu-act="connect-needs"]');
await page.click(action(d,'title'));await page.click('[data-menu-act="relation-add"][data-value="needs"]');
await page.eval(async()=>{u8test.check('phone add requirement',u8test.task(u8ids[1]).dependsOn.includes(u8ids[3]));await u8test.saved()});
await page.click(action(b,'more'));await page.click('[data-menu-act="connect"]');
await page.click(action(e,'title'));await page.click('[data-menu-act="relation-add"][data-value="blocks"]');
await page.eval(async()=>{u8test.check('phone add dependent',u8test.task(u8ids[4]).dependsOn.includes(u8ids[1]));await u8test.saved()});
await page.eval(()=>{const card=u8test.el(u8ids[2]),r=card.querySelector('.row-main').getBoundingClientRect();card.querySelector('.row-main').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerType:'touch',pointerId:32,isPrimary:true,clientX:r.x+10,clientY:r.y+10}));});
await page.wait(500);
await page.eval(()=>document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerType:'touch',pointerId:32,isPrimary:true})));
await page.eval(()=>u8test.check('long press offers connect',!!document.querySelector('[data-menu-act="connect"]')));
await page.click('[data-menu-act="connect"]');await page.click('[data-connect-cancel]');
await page.eval(()=>{for(const locale of ['en','es']){const el=document.querySelector('#locale-choice');el.value=locale;el.dispatchEvent(new Event('change',{bubbles:true}));u8test.check('phone fits '+locale,document.documentElement.scrollWidth<=innerWidth)}});
console.log(JSON.stringify(await page.eval(()=>u8)));
// RELATIONS
console.log(JSON.stringify(await page.eval(async()=>{
 const {check,wait,saved,drag}=u8test;
 const send=async(action,payload)=>{const state=(await(await fetch('/api/state')).json()).data;
  const reply=await(await fetch('/api/proposals',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action,payload,key:crypto.randomUUID(),expected_revision:state.revision})})).json();
  if(!['applied','unchanged'].includes(reply.data?.phase))throw Error(JSON.stringify(reply));
  await wait(()=>daySnapshot().revision>=(reply.data.result?.revision??state.revision));return reply.data.result};
 for(const t of daySnapshot().tasks)await send('task_cancel',{uuid:t.id,reason:'Synthetic fixture completed'});
 const ids=[];for(const title of ['Borrador ficticio','Preparar entrega ficticia','Revisión ficticia','Notas ficticias'])ids.push((await send('task_add',{title})).uuid);
 const [a,b,c,d]=ids,task=id=>daySnapshot().tasks.find(t=>t.id===id),row=id=>document.querySelector('[data-task-id="'+id+'"]'),lane=id=>row(id)?.closest('.lane')?.dataset.state;
 const click=selector=>{const el=document.querySelector(selector);if(!el)throw Error('missing '+selector);if(!el.matches('.port'))el.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,isPrimary:true}));el.click()};
 const action=(id,name)=>'[data-id="'+id+'"][data-action="'+name+'"]';
 drag(a,b,false,'related');check('drag chooses symmetric nonblocking relation',task(a).relatedTo.includes(b)&&task(b).relatedTo.includes(a)&&!task(b).blocked);await saved();
 await send('related_update',{uuid:a,relatedTo:[]});drag(a,b,false,'needs');check('drag chooses reverse dependency',task(a).dependsOn.includes(b));await saved();
 await send('dependency_update',{uuid:a,dependsOn:[]});drag(a,b);check('drag chooses forward dependency',task(b).dependsOn.includes(a));await saved();
 click('[data-task-id="'+c+'"] .port');click(action(d,'title'));check('keyboard connector offers all relationship types',document.querySelectorAll('[data-menu-act=relation-add]').length===3);click('[data-menu-act=keep]');
 row(c).dispatchEvent(new MouseEvent('contextmenu',{bubbles:true,clientX:100,clientY:100}));click('[data-menu-act=connect]');click(action(d,'title'));click('[data-menu-act=relation-add][data-value=needs]');await saved();check('context menu chooses reverse dependency',task(c).dependsOn.includes(d));
 click(action(d,'more'));click('[data-menu-act=details]');const input=row(d).querySelector('[data-search=rel]');input.value=task(a).title;input.dispatchEvent(new Event('input',{bubbles:true}));click('[data-pick="rel:'+a+'"]');check('editor offers all relationship types',document.querySelectorAll('[data-menu-act=relation-add]').length===3);click('[data-menu-act=relation-add][data-value=blocks]');await saved();check('editor can choose blocking instead of related',task(a).dependsOn.includes(d));
 await send('continuity_update',{uuid:d,checklist:[{id:'convert-test',text:'Paso ficticio convertido',done:false}]});click('[data-cl-convert="convert-test"]');click('[data-menu-act=cl-convert-dep]');await wait(()=>!!document.querySelector('[data-menu-act=relation-add]'));click('[data-menu-act=relation-add][data-value=related]');await saved();check('checklist conversion can choose a nonblocking relation',task(d).relatedTo.some(id=>task(id)?.title==='Paso ficticio convertido'));
 for(const id of ids)await send('dependency_update',{uuid:id,dependsOn:[]});
 document.querySelector('[data-unblocked-close]')?.click();
 await send('front_activate',{uuid:b});const started=task(b).startedAt;
 click(action(b,'more'));click('[data-menu-act=block]');document.querySelector('[data-menu-input=block]').value='Esperando revisión ficticia';click('[data-menu-act=block-save]');await wait(()=>task(b).blockReason==='Esperando revisión ficticia');await saved();
 check('manual block leaves active lane while retaining progress and highlight',lane(b)==='blocked'&&task(b).state==='active'&&task(b).startedAt===started&&row(b).classList.contains('is-active'));
 await send('dependency_update',{uuid:b,dependsOn:[a,c]});click(action(b,'block'));click('[data-menu-act=block-clear]');await wait(()=>!task(b).blockReason);await saved();
 check('clearing manual block still waits for prerequisites',lane(b)==='blocked'&&!document.querySelector('[data-unblocked-go="'+b+'"]'));
 await send('task_done',{uuid:a});check('first prerequisite does not unblock',lane(b)==='blocked'&&!document.querySelector('[data-unblocked-go="'+b+'"]'));
 await send('task_done',{uuid:c});check('last prerequisite resumes active lane without restarting progress',lane(b)==='active'&&task(b).startedAt===started);
 check('last prerequisite announces and highlights ready task',!!document.querySelector('[data-unblocked-go="'+b+'"]')&&row(b).classList.contains('just-unblocked'));
 await send('continuity_update',{uuid:b,blockReason:'Falta respuesta ficticia'});check('reblocking removes stale ready notice',lane(b)==='blocked'&&!document.querySelector('[data-unblocked-go="'+b+'"]'));
 await send('continuity_update',{uuid:b,blockReason:''});check('manual unblock announces active task',!!document.querySelector('[data-unblocked-go="'+b+'"]'));
 await send('front_activate',{uuid:d});await send('dependency_update',{uuid:d,dependsOn:[b]});check('dependency block retains active marker',lane(d)==='blocked'&&row(d).classList.contains('is-active'));
 await send('dependency_update',{uuid:d,dependsOn:[]});check('removing dependency announces all newly ready tasks',!!document.querySelector('[data-unblocked-go="'+b+'"]')&&!!document.querySelector('[data-unblocked-go="'+d+'"]'));
 // Leave a blocked active task visible beside the resumed task.
 await send('continuity_update',{uuid:d,blockReason:'Esperando aprobación ficticia'});
 sessionStorage.setItem('relations-test-ids',JSON.stringify(ids));return {checks:u8.checks.slice(-15),ids};
})));
// The notice survives a reload and a change that happens while the board is not looking.
await page.eval(()=>location.reload());await page.wait('[data-unblocked-go]');
console.log(JSON.stringify(await page.eval(()=>{const [a,b,c,d]=JSON.parse(sessionStorage.getItem('relations-test-ids'));if(!document.querySelector('[data-unblocked-go="'+b+'"]')||!document.querySelector('[data-task-id="'+b+'"].just-unblocked'))throw Error('ready notice lost on reload');return {reload:true}})));

// Following the ready notice reveals the task even when its lane was folded.
console.log(JSON.stringify(await page.eval(()=>{
 const [a,b]=JSON.parse(sessionStorage.getItem('relations-test-ids'));
 const row=()=>document.querySelector('[data-task-id="'+b+'"]');
 row().closest('.lane').querySelector('.fold').click();
 if(row().getClientRects().length)throw Error('Fixture lane must be folded');
 document.querySelector('[data-unblocked-go="'+b+'"]').click();
 if(!row().getClientRects().length||document.activeElement.dataset.id!==b)throw Error('Ready link must reveal and focus folded task');
 return {foldedReadyNavigation:true};
})));
