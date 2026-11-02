const checks=[];const assert=(ok,label)=>{checks.push({label,ok:!!ok});if(!ok)throw Error(label)};
try{
await page.wait('#board .task');
await page.eval(async()=>{const data=dayUI.flow.snapshot(),a=data.tasks.find(t=>t.title==='Revisar propuesta'),target=data.tasks.find(t=>t.title==='Grupo 0');await dayUI.flow.request('task_update',{uuid:a.id,groups:['Casa']});await dayUI.flow.request('task_update',{uuid:target.id,title:'Revisar destino'});const order=document.querySelector('#order-choice');order.value='group';order.dispatchEvent(new Event('change'))});
await page.fill('#task-search','Revisar');await page.click('[data-fold="grupo 0"]');
await page.eval(()=>{const source=document.querySelector('.group-section[data-group="Casa"] .drag-handle'),target=document.querySelector('.group-section[data-group="Grupo 0"] .lane-heading'),a=source.getBoundingClientRect(),b=target.getBoundingClientRect(),x=a.left+a.width/2,y=a.top+a.height/2,tx=b.left+b.width/2,ty=b.top+b.height/2;
source.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,isPrimary:true,pointerId:93,pointerType:'mouse',button:0,buttons:1,clientX:x,clientY:y}));document.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,isPrimary:true,pointerId:93,pointerType:'mouse',buttons:1,clientX:tx,clientY:ty}));document.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,isPrimary:true,pointerId:93,pointerType:'mouse',button:0,buttons:0,clientX:tx,clientY:ty}));});
await page.wait(450);
assert(await page.eval(()=>dayUI.flow.snapshot().tasks.find(t=>t.title==='Revisar propuesta').groups[0]==='Grupo 0'&&!document.body.classList.contains('dragging-task')),'folded target saves and releases shield');
await page.click('#undo');await page.wait(400);
assert(await page.eval(()=>{const t=dayUI.flow.snapshot().tasks.find(t=>t.title==='Revisar propuesta'),card=document.querySelector('[data-task-id="'+t.id+'"]');return t.groups[0]==='Casa'&&card.getClientRects().length>0&&!card.classList.contains('placeholder')&&getComputedStyle(card).opacity==='1'}),'Undo reuses a visible card without a cached drag placeholder');
await page.fill('#task-search','');
await page.eval(async()=>{const a='GrupoAmpliado_A'+'a'.repeat(90),b='GrupoAmpliado_B'+'b'.repeat(90);for(let i=0;i<3;i++)await dayUI.flow.request('task_add',{title:'Escala '+i,groups:[a,b]});const button=[...document.querySelectorAll('[data-filter]')].find(n=>n.dataset.filter.startsWith('group:grupoampliado_a'));button.click()});
assert(await page.eval(()=>!!document.querySelector('[data-rename-group]')&&!!document.querySelector('[data-more-groups]')),'long selected group retains rename and More controls');
console.log(JSON.stringify({passed:true,checks}));
}catch(error){console.log(JSON.stringify({passed:false,checks,error:String(error)}))}
