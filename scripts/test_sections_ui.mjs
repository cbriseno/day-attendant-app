await page.wait('[data-state=todo] [data-section-fold]');
const check=async(script)=>page.eval(new Function(script));
await check(`window.sectionAssert=(ok,message)=>{if(!ok)throw Error(message)};window.folded=()=>document.querySelector('[data-state=todo]').classList.contains('collapsed');`);
await page.eval(()=>document.querySelector('[data-state=todo] [data-section-fold]').focus());
await page.click('[data-state=todo] [data-section-fold]');
await check(`sectionAssert(folded(),'Click collapses');sectionAssert(getComputedStyle(document.querySelector('[data-state=todo] .lane-cards')).display==='none','Rows hidden');sectionAssert(document.querySelector('[data-state=blocked]').getBoundingClientRect().top<innerHeight,'Blocked is reachable');sectionAssert(document.activeElement.getAttribute('aria-expanded')==='false','Accessible collapsed state');sectionAssert(document.getElementById(document.activeElement.getAttribute('aria-controls')),'Controls target exists');`);
await page.press('Enter');
await check(`sectionAssert(!folded(),'Enter expands');`);
await page.press('Space');
await check(`sectionAssert(folded(),'Space collapses');`);
await page.eval(()=>location.reload());await page.wait('[data-state=todo] [data-section-fold]');
await check(`if(!document.querySelector('[data-state=todo]').classList.contains('collapsed'))throw Error('Reload lost state');`);
// Every ordering and Board uses the same fold preference; expansion is persisted too.
for(const order of ['manual','newest','suggested','priority']){
 await check(`const e=document.querySelector('#order-choice');e.value='${order}';e.dispatchEvent(new Event('change',{bubbles:true}));`);
 await check(`if(!document.querySelector('[data-state=todo]').classList.contains('collapsed'))throw Error('Ordering lost fold');`);
}
await page.click('#board-view');
await check(`if(!document.querySelector('[data-state=todo]').classList.contains('collapsed'))throw Error('Board lost fold');`);
await page.click('[data-state=todo] [data-section-fold]');
await page.eval(()=>location.reload());await page.wait('[data-state=todo] [data-section-fold]');
await check(`if(document.querySelector('[data-state=todo]').classList.contains('collapsed'))throw Error('Expansion not persisted');`);
await page.click('#group-view');await page.click('.group-section:not(.group-sub) [data-fold]');
await check(`if(!document.querySelector('.group-sub.parent-folded'))throw Error('Parent must fold subgroup');`);
await page.eval(()=>location.reload());await page.wait('[data-state=todo]');await page.click('#group-view');await page.wait('.group-section [data-fold]');
await check(`if(!document.querySelector('.group-sub.parent-folded'))throw Error('Group fold not persisted');`);
await page.click('#chains-view');await page.click('.chain-section [data-section-fold]');
await page.eval(()=>location.reload());await page.wait('[data-state=todo]');await page.click('#chains-view');await page.wait('.chain-section [data-section-fold]');
await check(`if(!document.querySelector('.chain-section.collapsed'))throw Error('Chain fold not persisted');`);
await page.click('#list-view');await page.click('[data-section-fold="lane:next-up"]');
await page.eval(()=>location.reload());await page.wait('[data-section-fold="lane:next-up"]');
await check(`if(document.querySelector('[data-section-fold="lane:next-up"]').getAttribute('aria-expanded')!=='false')throw Error('Up next fold lost');`);
// Native disclosures use Enter/Space and remember both open and closed states.
for(const selector of ['.closed-list:first-of-type>summary','.closed-list:last-of-type>summary','#calendar-area summary']){
 await check(`document.querySelector('${selector}').focus();`);await page.click(selector);await page.press('Enter');await page.press('Space');
}
await page.click('#settings-open');await page.click('#settings-dialog details.daily-section>summary');
await page.eval(()=>document.querySelector('#settings-dialog').close());await page.click('#settings-open');
await check(`if(!document.querySelector('#settings-dialog details.daily-section').open)throw Error('Settings fold lost');`);
await page.click('[data-org-history]');await page.wait('details.org-item');
await page.click('details.org-item>summary');
await page.eval(()=>document.querySelector('#org-dialog').close());
await page.eval(()=>location.reload());await page.wait('#settings-open');
await check(`if(![...document.querySelectorAll('.closed-list')].every(d=>d.open))throw Error('Closed/canceled open state lost');if(document.querySelector('#calendar-area details').open)throw Error('Calendar fold lost');`);
await page.click('#settings-open');await page.click('[data-org-history]');await page.wait('details.org-item');
await check(`if(document.querySelector('details.org-item').open)throw Error('Organization fold lost');document.querySelector('#org-dialog').close();document.querySelector('#settings-dialog')?.close();`);

await page.click('#list-view');
await check(`const b=document.querySelector('[data-state=todo] [data-section-fold]');if(b.getBoundingClientRect().height<28)throw Error('Touch target too small');if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal overflow');const set=Storage.prototype.setItem;Storage.prototype.setItem=()=>{throw Error('Unavailable storage')};try{b.click()}finally{Storage.prototype.setItem=set}if(b.getAttribute('aria-expanded')!=='false')throw Error('Fold must work without storage');`);
// Long lists inside a task can be folded independently without closing the task.
await page.eval(()=>dayUI.expandTask(daySnapshot().tasks.find(t=>t.checklist?.length).id));
await page.wait('.checklist .task-section');
await check(`const lists=[...document.querySelectorAll('details.task-section')];if(lists.length<3)throw Error('Checklist and relation lists need controls');for(const d of lists)d.open=false;if(!document.querySelector('[data-expand]'))throw Error('Folding a list closed the task');`);
await page.eval(()=>location.reload());await page.wait('[data-cl-open]');
await page.eval(()=>dayUI.expandTask(daySnapshot().tasks.find(t=>t.checklist?.length).id));
await check(`if([...document.querySelectorAll('details.task-section')].some(d=>d.open))throw Error('Task list folds lost after reload');`);
await page.click('.checklist .task-section>summary');
await check(`if(!document.querySelector('.checklist details').open||!document.querySelector('[data-expand]'))throw Error('Checklist summary must expand only the list');`);
await page.click('.checklist .task-section>summary');await page.click('[data-cl-open]');
await check(`if(!document.querySelector('.checklist details').open)throw Error('Checklist chip must reveal its list');`);
console.log(JSON.stringify({click:true,enterSpace:true,reload:true,orderings:4,board:true,nestedGroups:true,chains:true,nextUp:true,closedCanceled:true,settings:true,calendar:true,history:true,taskLists:true,storageUnavailable:true}));
