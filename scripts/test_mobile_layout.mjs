await page.wait('[data-task-id]');
console.log(JSON.stringify(await page.eval(async()=>{
 const check=(ok,msg)=>{if(!ok)throw Error(msg)};
 const visible=e=>e.getClientRects().length&&getComputedStyle(e).visibility==='visible'&&getComputedStyle(e).clipPath!=='inset(50%)';
 const rect=e=>e.getBoundingClientRect();
 const overlap=(a,b)=>a.left<b.right-.5&&a.right>b.left+.5&&a.top<b.bottom-.5&&a.bottom>b.top+.5;
 const measure=()=>{
  check(document.documentElement.scrollWidth<=innerWidth,'page overflow');
  for(const selector of ['.app-controls','.toolbar-left','.toolbar-right','.row-actions'])for(const parent of document.querySelectorAll(selector)){
   const children=[...parent.children].filter(visible);
   for(let i=0;i<children.length;i++)for(let j=i+1;j<children.length;j++)check(!overlap(rect(children[i]),rect(children[j])),`overlap ${selector} ${children[i].id||children[i].className} ${children[j].id||children[j].className}`);
  }
  for(const e of document.querySelectorAll('.app-controls button,.app-controls select,.view-tabs button,#task-count'))if(visible(e))check(e.scrollWidth<=e.clientWidth+1,`clipped ${e.id}`);
  check(visible(document.querySelector('#task-count')),'missing task count');
  for(const row of document.querySelectorAll('.task')){const title=row.querySelector('.task-title'),actions=row.querySelector('.row-actions'),mark=row.querySelector('.assistant-mark');if(title&&actions)check(!overlap(rect(title),rect(actions)),'title/actions overlap');if(title&&mark)check(!overlap(rect(title),rect(mark)),'title/mark overlap')}
  const pills=[...document.querySelectorAll('.row-actions .priority-pill')];check(pills.every(e=>Math.abs(rect(e).width-rect(pills[0]).width)<1),'priority widths');
  return [...document.querySelectorAll('.task-title')].map(e=>({height:rect(e).height, lines:Math.round(rect(e).height/parseFloat(getComputedStyle(e).lineHeight))}));
 };
 await dayAnonymize.setActive(false);const before=measure();await dayAnonymize.setActive(true);await dayAnonymize.ready;const after=measure();
 check(before.length===after.length,'title count');before.forEach((v,i)=>check(v.lines===after[i].lines&&Math.abs(v.height-after[i].height)<=Math.max(1,v.height*.02),'title geometry'));
 for(const e of document.querySelectorAll('.task-title span span'))check(getComputedStyle(e).letterSpacing==='normal','stretched letters');
 await dayAnonymize.setActive(false);return {titles:before.length,checked:true};
})));
