/* Daily controls extend the approved interface without owning domain decisions. */
(() => {
'use strict';
const ui=globalThis.dayUI;
const $=id=>document.getElementById(id),{tr,esc,api,deliver,flow,safely,notice,taskGroups,groupKey,rankedGroups}=ui;
const button=(id,key,extra='')=>`<button type="button" class="btn ${extra}" id="${id}">${esc(tr(key))}</button>`;
function field(id,key,type='text',extra=''){return `<label class="field"><span>${esc(tr(key))}</span><input id="${id}" type="${type}" ${extra}></label>`}
function dialog(id,title,body,footer){
 const el=document.createElement('dialog');el.id=id;el.setAttribute('aria-labelledby',id+'-title');el.innerHTML=`<form class="modal-form"><header class="modal-header"><h2 id="${id}-title">${esc(title)}</h2><button type="button" class="btn icon ghost" aria-label="${esc(tr('cancel'))}" data-dismiss>×</button></header><div class="modal-body">${body}<p class="error" role="alert" id="${id}-error" hidden></p></div><footer class="modal-footer">${footer}</footer></form>`;
 document.body.append(el);ui.registerDialog(el);el.querySelector('[data-dismiss]').onclick=()=>el.close('cancel');return el;
}
function fail(id,error){$(id+'-error').hidden=false;$(id+'-error').textContent=error.message}
async function formAction(id,fn){$(id+'-error').hidden=true;const buttons=[...$(id).querySelectorAll('button[type=submit]')];buttons.forEach(b=>b.disabled=true);try{await ui.zoneReady($(id));await fn()}catch(e){fail(id,e)}finally{buttons.forEach(b=>b.disabled=false)}}
function requiredTime(id){const raw=$(id).value;if(!raw)return null;const date=ui.parseLocal(raw);if(!Number.isFinite(date.getTime())||ui.localValue(date)!==raw||ui.ambiguous(date))throw Error(tr('daily_c641536258'));return date.toISOString()}
function storedTime(id,instant){$(id).value=instant?ui.localValue(new Date(instant)):'';const opening=$(id).value;return ()=>$(id).value===opening?instant||null:requiredTime(id)}
function submit(label){return `<button type="submit" class="btn primary">${esc(label)}</button>`}
function open(el,origin){ui.openDialog(el,origin);el.querySelector('input,select,button')?.focus()}
let eventId=null,captureRevision=null,settingsRevision=null,lastProfile=null,lastDailyDigest='',lastDiagnostics='',lastCalendar='',selectedImages=[];
const toolbar=document.querySelector('.toolbar-right');toolbar.insertAdjacentHTML('afterbegin',button('capture-open','daily_54e17efed4'));
document.querySelector('.app-controls').insertAdjacentHTML('beforeend','<button type="button" class="btn" id="settings-open" aria-label="Settings"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="3"/><path d="M12 2v3m0 14v3M2 12h3m14 0h3M5 5l2 2m10 10 2 2M19 5l-2 2M7 17l-2 2"/></svg> <span>Settings</span></button>');
const diagnostic=document.createElement('div');diagnostic.className='diagnostic-banner';diagnostic.hidden=true;diagnostic.id='daily-diagnostics';$('tasks-area').insertBefore(diagnostic,document.querySelector('.toolbar'));
const calendar=document.createElement('section');calendar.className='calendar-area';calendar.id='calendar-area';$('tasks-area').append(calendar);

function groupField(id){return '<div class="field group-picker" id="'+id+'-picker"><span>'+esc(tr('groups_open'))+'</span><input id="'+id+'" type="text" maxlength="120" placeholder="'+esc(tr('group_search_create'))+'" aria-label="'+esc(tr('group_search_create'))+'"><div class="group-list"></div><button type="button" class="btn ghost" data-create-group>'+esc(tr('add_group'))+'</button></div>'}
function wireGroupPicker(id,selected=[]){const box=$(id+'-picker'),input=$(id),list=box.querySelector('.group-list');let labels=[...new Set([...selected,...rankedGroups().map(g=>g.label)])],chosen=[...selected];
 const add=()=>{const value=input.value.trim();if(!value)return;if(!labels.some(g=>groupKey(g)===groupKey(value)))labels.unshift(value);if(!chosen.some(g=>groupKey(g)===groupKey(value)))chosen.push(value);input.value='';draw()};
 const draw=()=>{list.replaceChildren();for(const label of labels.filter(g=>groupKey(g).includes(groupKey(input.value)))){const row=document.createElement('label');row.className='group-list-row';const check=document.createElement('input');check.type='checkbox';check.checked=chosen.some(g=>groupKey(g)===groupKey(label));check.onchange=()=>{chosen=check.checked?[...chosen,label]:chosen.filter(g=>groupKey(g)!==groupKey(label))};row.append(check,document.createTextNode(label));list.append(row)}};
 input.oninput=draw;input.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();add()}};box.querySelector('[data-create-group]').onclick=add;draw();return ()=>[...chosen,...(input.value.trim()&&!chosen.some(g=>groupKey(g)===groupKey(input.value))?[input.value.trim()]:[])];
}
// Most pressing first; a new item starts at Medium.
const priorityOptions=()=>globalThis.dayOrdering.PRIORITIES.map(p=>`<option value="${p}"${p==='medium'?' selected':''}>${esc(tr('priority_'+p))}</option>`).join('');
function buildCapture(){
 $('capture-dialog')?.remove();return dialog('capture-dialog',tr('daily_4a91d6da82'),`<div class="daily-grid"><label class="field wide"><span>${tr('daily_e00ac23f2a')}</span><select id="capture-kind"><option value="task">${tr('daily_2550b1dcad')}</option><option value="event">${tr('daily_b95f485bf5')}</option></select></label>${field('capture-title','daily_768e0c1c69','text','maxlength="2000" required class="wide"')}<label class="field" id="capture-priority-field"><span>${tr('priority')}</span><select id="capture-priority">${priorityOptions()}</select></label>${field('capture-due','daily_46588ea318','datetime-local')}${groupField('capture-group')}<div id="event-fields" class="daily-grid wide" hidden>${field('capture-start','daily_fc612a2fcc','datetime-local')}${field('capture-end','daily_91856dcb7d','datetime-local')}</div><details class="wide daily-section"><summary>${tr('daily_8f71959ca4')}</summary><div class="daily-grid">${field('capture-person','daily_d3531f63ac')}${field('capture-reference','daily_e3039b8476')}<label class="field"><span>${tr('daily_6da13addb0')}</span><select id="capture-source"><option value="general">${tr('source_general')}</option><option value="chat">${tr('source_chat')}</option><option value="email">${tr('source_email')}</option><option value="call">${tr('daily_291a0a58df')}</option><option value="ticket">${tr('source_ticket')}</option><option value="pr">${tr('source_pr')}</option><option value="research">${tr('daily_be601df25e')}</option></select></label>${field('capture-observed','daily_97844eb51c','datetime-local')}</div><p class="hint">${tr('daily_ff25fb790f')}</p></details></div>`,submit(tr('save_context').replace(/ contexto?$/i,'')));
}
function openCapture(origin,event=null,draft=null){
 const d=buildCapture();eventId=event?.uuid||null;captureRevision=flow.snapshot().revision;$('capture-title').value=event?.title||draft?.title||'';
 if(draft){if(draft.priority)$('capture-priority').value=draft.priority;if(draft.due)$('capture-due').value=ui.localValue(new Date(draft.due))}
 const selectedGroups=wireGroupPicker('capture-group',draft?.groups||[]),files=ui.attachmentPicker(d.querySelector('.modal-body'),$('capture-title'));ui.formatInput($('capture-title'));
 $('capture-kind').value=event?'event':'task';$('capture-kind').disabled=!!event;
 const kind=()=>{const isEvent=$('capture-kind').value==='event';$('event-fields').hidden=!isEvent;$('capture-due').closest('label').hidden=isEvent;$('capture-priority-field').hidden=isEvent;$('capture-group-picker').hidden=isEvent};$('capture-kind').onchange=kind;kind();
 const start=storedTime('capture-start',event?.start_at),end=storedTime('capture-end',event?.end_at);if(event)d.querySelector('details').hidden=true;
 d.querySelector('form').onsubmit=e=>{e.preventDefault();formAction(d.id,async()=>{const title=$('capture-title').value.trim();if(!title)throw Error(tr('daily_9996af5999'));const isEvent=$('capture-kind').value==='event';let payload={title};if(isEvent){payload.start=start();payload.end=end();if(!payload.start||!payload.end)throw Error(tr('daily_ad3c3e9e8e'));if(eventId)payload.uuid=eventId}else{payload.priority=$('capture-priority').value;payload.due=requiredTime('capture-due');payload.groups=selectedGroups();payload.attachmentIds=files.ids()}
 if(!eventId){payload.source=$('capture-source').value;for(const [name,id] of [['person','capture-person'],['reference','capture-reference']])if($(id).value.trim())payload[name]=$(id).value.trim();const observed=requiredTime('capture-observed');if(observed)payload.observed_at=observed}
 await flow.request(eventId?'event_update':isEvent?'event_add':'task_add',payload,undefined,captureRevision);if(draft&&$('qa-input').value===draft.raw){$('qa-input').value='';renderQuick()}d.close('saved')})};open(d,origin);
}
// The full form starts from what the quick line already says; an unreadable line starts empty.
$('capture-open').onclick=e=>{const q=parseQuick($('qa-input').value);openCapture(e.currentTarget,null,q.error?null:q)};

// One line above the list: «pagar luz mañana !2 #Casa» and Enter. Every token it reads is shown in the
// preview before saving; a word it cannot place stays in the title, and a doubtful line is not saved.
const PRIORITY_WORDS={1:'urgent',2:'high',3:'medium',4:'low',urgente:'urgent',urgent:'urgent',alta:'high',high:'high',media:'medium',medium:'medium',baja:'low',low:'low',pronto:'soon',soon:'soon',algundia:'someday','algundía':'someday','algúndía':'someday',someday:'someday',luego:'someday'};
const DAY_WORDS={hoy:0,today:0,'mañana':1,manana:1,tomorrow:1};
const WEEKDAYS={domingo:0,sunday:0,lunes:1,monday:1,martes:2,tuesday:2,'miércoles':3,miercoles:3,wednesday:3,jueves:4,thursday:4,viernes:5,friday:5,'sábado':6,sabado:6,saturday:6};
// «la mañana», «esta mañana»: the morning, not tomorrow.
const MORNING=new Set(['la','esta','una','cada','toda','media','en']);
const LEADS=new Set(['el','para','on','by']);
const CLOCK=/^([01]?\d|2[0-3]):([0-5]\d)$/;
function quickDue(days,weekday,time){
 const [y,m,d]=ui.localValue(new Date(flow.snapshot().now||Date.now())).slice(0,10).split('-').map(Number),day=new Date(Date.UTC(y,m-1,d));
 // A weekday is its next occurrence; today's own weekday is a week ahead, as the approved demo does.
 if(weekday!==null){let add=(weekday-day.getUTCDay()+7)%7;days=add||7}
 day.setUTCDate(day.getUTCDate()+days);const raw=day.toISOString().slice(0,10)+'T'+(time||'18:00'),date=ui.parseLocal(raw);
 if(!Number.isFinite(date.getTime())||ui.localValue(date)!==raw||ui.ambiguous(date))return {error:tr('daily_28b99b54a4')};
 return {due:date.toISOString()};
}
const HASH=/^#([\p{L}\p{N}\p{M}\p{Extended_Pictographic}\p{Regional_Indicator}\u{1F3FB}-\u{1F3FF}\u200D\uFE0F_-]{1,120})$/u;
function readHash(word){const clean=word.replace(/[.,;]+$/,'');if(clean.startsWith('#"')){try{const label=JSON.parse(clean.slice(1));return typeof label==='string'&&label.trim()&&[...label].length<=120?label:null}catch{return null}}return HASH.exec(clean)?.[1]??null}
function parseQuick(value){
 const words=value.trim().match(/#"(?:[^"\\]|\\.)*"|\S+/gu)||[],title=[],errors=[];let priority=null,group=null,isNew=false,due=null,dated=false;const groups=[];
 const known=rankedGroups().map(g=>g.label);
 const twice=key=>errors.push(tr(key));
 for(let i=0;i<words.length;i++){
  const word=words[i],bare=word.toLocaleLowerCase().replace(/[.,;]+$/,''),next=(words[i+1]||'').toLocaleLowerCase().replace(/[.,;]+$/,'');
  const p=/^!(\S+)$/.exec(bare);if(p&&PRIORITY_WORDS[p[1]]){if(priority)twice('daily_6d210a3f16');priority=PRIORITY_WORDS[p[1]];continue}
  const label=readHash(word);if(label!==null){const match=known.find(k=>groupKey(k)===groupKey(label));group=match||label;isNew=isNew||!match;if(!groups.some(x=>groupKey(x)===groupKey(group)))groups.push(group);continue}
  let days=null,weekday=null,span=1;
  if(bare==='pasado'&&['mañana','manana'].includes(next)){days=2;span=2}
  else if(bare==='day'&&next==='after'&&(words[i+2]||'').toLocaleLowerCase().replace(/[.,;]+$/,'')==='tomorrow'){days=2;span=3}
  else if(bare in DAY_WORDS&&!(DAY_WORDS[bare]===1&&bare!=='tomorrow'&&MORNING.has((title.at(-1)||'').toLocaleLowerCase())))days=DAY_WORDS[bare];
  else if(bare in WEEKDAYS)weekday=WEEKDAYS[bare];
  if(days===null&&weekday===null){title.push(word);continue}
  if(dated)twice('daily_c6d5319e71');dated=true;
  while(title.length&&LEADS.has(title.at(-1).toLocaleLowerCase()))title.pop();
  i+=span-1;const clock=CLOCK.exec(words[i+1]||'');if(clock)i++;
  const result=quickDue(days,weekday,clock?clock[1].padStart(2,'0')+':'+clock[2]:null);if(result.error)errors.push(result.error);else due=result.due;
 }
 let name=title.join(' ');name=name.charAt(0).toLocaleUpperCase()+name.slice(1);
 if(!name&&words.length)errors.push(tr('daily_e7df37a6ec'));
 if(name.length>2000)errors.push(tr('daily_cbe3f1718c'));
 return {raw:value,title:name,priority,group,groups,isNew,due,error:errors[0]||null};
}
function renderQuick(showError=false){
 const value=$('qa-input').value,box=$('qa-preview');
 box.hidden=!value.trim();if(!value.trim()){box.innerHTML='';renderGroupSuggestions();return}

 const q=parseQuick(value);
 if(q.error&&(showError||!q.title)){box.innerHTML=`<span class="qa-error">${esc(q.error)}</span>`;return}
 const past=q.due&&new Date(q.due)<new Date(flow.snapshot().now||Date.now());
 box.innerHTML=`<span>${esc(tr('daily_68f93bc9de'))}</span><b>${ui.richText(q.title)}</b><select class="priority-pill qa-priority" aria-label="${esc(tr('priority'))}" data-priority="${q.priority||'medium'}">${globalThis.dayOrdering.PRIORITIES.map(p=>`<option value="${p}"${p===(q.priority||'medium')?' selected':''}>${esc(tr('priority_'+p))}</option>`).join('')}</select>`
  +q.groups.map(g=>{const near=similarGroup(g);return `<span class="qa-group">${ui.groupDot(g)}${esc(g)}${!rankedGroups().some(x=>groupKey(x.label)===groupKey(g))?' ('+esc(tr('new_group'))+')':''}</span>`+(near?`<span class="qa-similar">${esc(tr('group_similar').replace('{group}',near))} <button type="button" class="link-button" data-use-group="${esc(near)}" data-typed="${esc(g)}">${esc(tr('use_group').replace('{group}',near))}</button></span>`:'')}).join('')
  +(q.due?`<span${past?' class="qa-warn"':''}>${esc(tr('daily_655310dc3f')+ui.full(q.due))}${past?' · '+esc(tr('daily_846f78a2c1')):''}</span>`:'')
  +(q.error?`<span class="qa-error">${esc(q.error)}</span>`:`<span>· Enter</span>`);renderGroupSuggestions();
}
const quick=document.createElement('form');quick.className='quick-add';quick.id='quick-add';quick.autocomplete='off';
quick.innerHTML=`<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg><textarea id="qa-input" maxlength="2000" rows="1" enterkeyhint="done" aria-describedby="qa-preview"></textarea><button class="btn ghost qa-hash" type="button" id="qa-hash" aria-label="${esc(tr('groups_open'))}">#</button><button class="btn primary" type="submit" id="qa-submit"></button>`;
const quickFiles=ui.attachmentPicker(quick,quick.querySelector('#qa-input'));ui.formatInput(quick.querySelector('#qa-input'));
const skipOrganize=document.createElement('label');skipOrganize.className='skip-organize';skipOrganize.innerHTML='<input type="checkbox" id="skip-organize"> <span></span>';
const quickPreview=document.createElement('div');quickPreview.className='qa-preview';quickPreview.id='qa-preview';quickPreview.setAttribute('aria-live','polite');
$('tasks-area').insertBefore(quick,document.querySelector('.toolbar'));$('tasks-area').insertBefore(quickPreview,document.querySelector('.toolbar'));quick.after(skipOrganize);
const quickLabels=()=>{$('qa-input').removeAttribute('placeholder');$('qa-input').setAttribute('aria-label',tr('daily_8d72694f53'));$('qa-submit').textContent=tr('daily_61cc55aa04');skipOrganize.querySelector('span').textContent=tr('skip_organize')};
let quickFocused=false,hashOpen=false,hashIndex=-1;
const suggestions=document.createElement('div');suggestions.className='qa-groups';suggestions.hidden=true;
const hashList=document.createElement('div');hashList.id='qa-options';hashList.className='qa-options';hashList.setAttribute('role','listbox');hashList.hidden=true;
quickPreview.after(suggestions,hashList);
$('qa-input').setAttribute('role','combobox');$('qa-input').setAttribute('aria-controls','qa-options');$('qa-input').setAttribute('aria-autocomplete','list');
function hashToken(){const input=$('qa-input'),end=input.selectionStart??input.value.length,match=/(?:^|\s)#([^\s]*)$/.exec(input.value.slice(0,end));return match?{start:end-match[1].length-1,end,text:match[1]}:null}
const groupToken=label=>HASH.test('#'+label)?'#'+label:'#'+JSON.stringify(label);
function chooseGroup(label){const input=$('qa-input'),token=hashToken();if(token)input.setRangeText(groupToken(label)+' ',token.start,token.end,'end');else{const end=input.selectionStart??input.value.length;input.setRangeText((end&&!/\s/.test(input.value[end-1])?' ':'')+groupToken(label)+' ',end,end,'end')}hashOpen=false;hashIndex=-1;input.focus();renderQuick()}
function foldGroup(label){return label.normalize('NFD').replace(/[\p{M}\p{Extended_Pictographic}\p{Regional_Indicator}\p{Emoji_Modifier}\u200D\uFE0F]/gu,'').toLowerCase()}
function distance(a,b){const d=Array.from({length:a.length+1},(_,i)=>[i,...Array(b.length).fill(0)]);for(let j=1;j<=b.length;j++)d[0][j]=j;for(let i=1;i<=a.length;i++)for(let j=1;j<=b.length;j++){d[i][j]=Math.min(d[i-1][j]+1,d[i][j-1]+1,d[i-1][j-1]+(a[i-1]===b[j-1]?0:1));if(i>1&&j>1&&a[i-1]===b[j-2]&&a[i-2]===b[j-1])d[i][j]=Math.min(d[i][j],d[i-2][j-2]+1)}return d[a.length][b.length]}
function similarGroup(label){if(rankedGroups().some(g=>groupKey(g.label)===groupKey(label)))return null;const a=foldGroup(label);return rankedGroups().find(g=>{const b=foldGroup(g.label);return a&&a===b||a.length>=3&&b.length>=3&&distance(a,b)<=1})?.label}
function renderGroupSuggestions(){const all=rankedGroups(),token=hashToken(),exact=token&&token.text&&all.some(g=>groupKey(g.label)===groupKey(token.text));const options=quickFocused&&(hashOpen||token&&!exact)?all.filter(g=>!token||groupKey(g.label).includes(groupKey(token.text))):[];
 suggestions.hidden=!quickFocused||!!token||hashOpen;suggestions.innerHTML=all.slice(0,4).map(g=>'<button type="button" class="btn ghost" data-pick-group="'+esc(g.label)+'">'+ui.groupDot(g.label)+esc(g.label)+'</button>').join('');
 hashList.hidden=!options.length;hashIndex=Math.min(hashIndex,options.length-1);hashList.innerHTML=options.map((g,i)=>'<button type="button" id="qa-option-'+i+'" role="option" aria-selected="'+(i===hashIndex)+'" class="btn ghost" data-pick-group="'+esc(g.label)+'">'+ui.groupDot(g.label)+esc(g.label)+'</button>').join('');$('qa-input').setAttribute('aria-expanded',String(!!options.length));if(hashIndex>=0&&options.length)$('qa-input').setAttribute('aria-activedescendant','qa-option-'+hashIndex);else $('qa-input').removeAttribute('aria-activedescendant');
}
for(const node of [suggestions,hashList]){node.onpointerdown=e=>e.preventDefault();node.onclick=e=>{const b=e.target.closest('[data-pick-group]');if(b)chooseGroup(b.dataset.pickGroup)}}
$('qa-hash').onclick=()=>{hashOpen=!hashOpen;quickFocused=true;$('qa-input').focus();renderGroupSuggestions()};
$('qa-input').addEventListener('focus',()=>{quickFocused=true;renderGroupSuggestions()});$('qa-input').addEventListener('blur',()=>{quickFocused=false;hashOpen=false;hashIndex=-1;renderGroupSuggestions()});
$('qa-input').addEventListener('keydown',e=>{if(hashList.hidden)return;const options=[...hashList.querySelectorAll('button')];if(['ArrowDown','ArrowUp'].includes(e.key)){e.preventDefault();hashIndex=(hashIndex+(e.key==='ArrowDown'?1:-1)+options.length)%options.length;renderGroupSuggestions()}else if(['Enter','Tab'].includes(e.key)&&options.length){e.preventDefault();e.stopImmediatePropagation();chooseGroup(options[Math.max(0,hashIndex)].dataset.pickGroup)}else if(e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();hashOpen=false;quickFocused=false;renderGroupSuggestions()}});
quickPreview.addEventListener('change',e=>{
 if(!e.target.matches('.qa-priority'))return;
 const input=$('qa-input'),words=input.value.match(/#"(?:[^"\\]|\\.)*"|\S+/gu)||[];
 input.value=words.filter(word=>{const match=/^!(\S+)$/.exec(word.toLocaleLowerCase().replace(/[.,;]+$/,''));return !match||!PRIORITY_WORDS[match[1]]}).join(' ')+' !'+e.target.value;
 input.focus();renderQuick();
});
quickPreview.onclick=e=>{const b=e.target.closest('[data-use-group]');if(!b)return;const input=$('qa-input');input.value=input.value.replace(/#"(?:[^"\\]|\\.)*"|\S+/gu,word=>readHash(word)===b.dataset.typed?groupToken(b.dataset.useGroup):word);input.focus();renderQuick()};
$('qa-input').addEventListener('input',()=>{quickFocused=true;hashIndex=-1;renderQuick()});
$('qa-input').addEventListener('keydown',e=>{if(e.key!=='Enter'||e.isComposing||e.shiftKey)return;if(e.ctrlKey||e.metaKey){e.preventDefault();const i=e.target;i.setRangeText('\n',i.selectionStart,i.selectionEnd,'end');i.dispatchEvent(new Event('input',{bubbles:true}));return}e.preventDefault();quick.requestSubmit()});
// Local keys only: Enter adds, Esc clears the line, then leaves it.
$('qa-input').addEventListener('keydown',e=>{if(e.key!=='Escape')return;e.preventDefault();e.stopPropagation();if($('qa-input').value){$('qa-input').value='';renderQuick()}else $('qa-input').blur()});
quick.onsubmit=e=>{e.preventDefault();const input=$('qa-input'),raw=input.value;if(!raw.trim()){input.focus();return}const q=parseQuick(raw);if(q.error){renderQuick(true);input.focus();return}
 let ids;try{ids=quickFiles.ids()}catch(error){notice(error.message);return}const payload={title:raw.includes('\n')?raw.trim():q.title,priority:q.priority||'medium',source:'general',groups:q.groups,attachmentIds:ids,organize:!$('skip-organize').checked,captureText:raw.trim(),...(q.due?{due:q.due}:{})};
 // The card shows at once; the line is free for the next one while the service saves it.
 input.value='';renderQuick();input.focus();
 safely(async()=>{try{await flow.request('task_add',payload);quickFiles.clear(ids);$('skip-organize').checked=false}catch(error){if(!input.value){input.value=raw;renderQuick()}throw error}})};

function buildSettings(){
 $('settings-dialog')?.remove();const days=['mon','tue','wed','thu','fri','sat','sun'].map(k=>tr('weekday_'+k));
 return dialog('settings-dialog',tr('daily_7831a7f8c4'),`<div class="daily-grid">${field('setting-name','daily_77574766df')}${field('setting-zone','daily_d1f7dc891b')}<label class="field"><span>${tr('daily_1c34cc98bf')}</span><select id="setting-harness" data-anon-safe="value"><option data-anon-safe="value" value="codex">Codex</option><option data-anon-safe="value" value="claude">Claude Code</option></select></label><label class="field"><span>${tr('daily_68c2cc7f0c')}</span><select id="setting-model"></select></label><label class="field"><span>${tr('daily_6874c03787')}</span><select id="setting-effort"></select></label><p class="hint wide">${tr('daily_d13157cb0c')}</p><label class="context-checkbox wide"><input id="setting-organize" type="checkbox">${esc(tr('auto_organize'))}</label></div>${globalThis.dayProactive?.settingsHtml()||''}<details class="daily-section" open><summary>${tr('daily_88ad883d4c')}</summary><fieldset class="notify-block"><legend>${tr('notify_kinds_title')}</legend><div class="notify-kinds">${['soon','overdue','reminder'].map(k=>`<label class="context-checkbox"><input type="checkbox" id="policy-kind-${k}" data-kind="${k}">${tr('notify_kind_'+k)}</label>`).join('')}</div><button type="button" class="btn" id="notify-preview-open">${tr('notify_preview')}</button><div class="notify-preview" id="notify-preview" hidden role="img" aria-label="${tr('notify_preview')}"><span class="np-icon" aria-hidden="true">✓</span><div><b>Day Attendant</b><span id="notify-preview-text"></span></div></div><p class="hint" id="notify-preview-note" hidden>${tr('notify_preview_note')}</p><p class="xlabel">${tr('notify_upcoming')}</p><ul class="upcoming-list" id="notify-upcoming"></ul></fieldset><label class="context-checkbox"><input id="policy-enabled" type="checkbox">${tr('daily_73c69b1b29')}</label><div class="day-list">${days.map((day,i)=>`<label><input type="checkbox" data-day="${i}">${day}</label>`).join('')}</div><div class="daily-grid">${field('policy-start','daily_3f66052a10','time')}${field('policy-end','daily_96bdb66ba4','time')}${field('policy-quiet-start','daily_248ddd1447','time')}${field('policy-quiet-end','daily_f0448c3b89','time')}${field('policy-interval','daily_e8957f9619','number','min="1" max="1440"')}${field('policy-repeat','daily_7e738ef3d1','number','min="1" max="10080"')}${field('policy-budget','daily_c1673affd4','number','min="1" max="100"')}${field('policy-pause','daily_15c063aef3','datetime-local')}</div><p class="hint">${tr('daily_a3b96333fe')}</p></details><details class="daily-section"><summary>${tr('daily_0e3b339df0')}</summary><p class="hint">${tr('daily_30a01141ec')}</p><div class="actions">${button('backup-create','daily_527bf1aa5d')}${button('diagnostics-open','daily_3af2279f9e')}</div><div id="operations-info" class="hint"></div><div id="backup-list" class="hint"></div></details><details class="daily-section"><summary>${tr('daily_04a3ac8c63')}</summary><p class="hint">${tr('daily_55dd0e512b')}</p><div id="continuity-info" class="hint"></div></details>`,submit(tr('daily_913aba9f96')));
}
function openSettings(origin){
 const state=flow.snapshot(),d=buildSettings(),p=state.profile,n=state.notification_policy;settingsRevision=state.revision;
 globalThis.dayProactive?.wireSettings(state);$('setting-organize').checked=p.autoOrganize!==false;$('setting-name').value=p.name;$('setting-zone').value=p.timezone;$('setting-harness').value=p.harness;
 // Each harness lists its own models: Codex through model/list, Claude Code from its known IDs.
 // Without a catalog only the installed default and the saved choices are offered.
 let catalogs={[p.harness]:state.agent?.catalog||[]};
 const entry=()=>{const harness=$('setting-harness').value,model=$('setting-model').value,list=catalogs[harness]||[];return list.find(m=>m.model===(model||(harness===p.harness?state.agent?.model:null)))||(!model?list.find(m=>m.isDefault):undefined)};
 const efforts=()=>{const harness=$('setting-harness').value;return entry()?.efforts?.length?entry().efforts:harness==='claude'?['low','medium','high','xhigh','max']:['',...(harness===p.harness&&p.effort?[p.effort]:[])]};
 const fillModels=selected=>{const models=(catalogs[$('setting-harness').value]||[]).map(m=>m.model);if(selected&&!models.includes(selected))models.unshift(selected);$('setting-model').replaceChildren(...['',...models].map(value=>{const o=document.createElement('option');o.value=value;o.textContent=value||tr('daily_5b577baa11');return o}));$('setting-model').value=selected||''};
 const fillEfforts=selected=>{const select=$('setting-effort'),levels=efforts(),fallback=entry()?.defaultEffort;select.replaceChildren(...levels.map(value=>{const o=document.createElement('option');o.value=value;o.textContent=({low:tr('daily_a124947cbd'),medium:tr('daily_d404968ea9'),high:tr('daily_b1a5954a48'),xhigh:tr('daily_b8474282ef'),max:tr('daily_a8df2fec28'),minimal:tr('daily_a711cca9a4'),none:tr('daily_6eef664840')})[value]||value||tr('daily_cc498c1d11');return o}));select.value=levels.includes(selected)?selected:levels.includes('medium')?'medium':levels.includes(fallback)?fallback:levels[0]};
 fillModels(p.model||'');fillEfforts(p.effort||state.agent?.effort||'medium');const initialEffort=$('setting-effort').value;
 $('setting-harness').onchange=()=>{fillModels($('setting-harness').value===p.harness?p.model||'':'');fillEfforts($('setting-effort').value)};$('setting-model').onchange=()=>fillEfforts($('setting-effort').value);
 api('/api/models').then(data=>{if(!d.open)return;for(const harness of ['codex','claude'])if(data[harness]?.length)catalogs[harness]=data[harness];const model=dayAnonymize.value($('setting-model')),effort=dayAnonymize.value($('setting-effort'));fillModels(model);fillEfforts(effort)}).catch(()=>{});
 $('policy-enabled').checked=n.enabled;const kinds={soon:true,overdue:true,reminder:true,...(n.kinds||{})};for(const k of Object.keys(kinds))$('policy-kind-'+k).checked=kinds[k];
 const upcoming=()=>globalThis.dayUpcoming?.(state,Object.fromEntries(Object.keys(kinds).map(k=>[k,$('policy-kind-'+k).checked])))||[];
 const paintUpcoming=()=>{const list=upcoming(),ul=$('notify-upcoming');ul.replaceChildren(...(list.length?list.map(x=>{const li=document.createElement('li'),t=document.createElement('time');t.textContent=ui.short(x.at);t.title=ui.full(x.at);const b=document.createElement('span');b.textContent=tr('notify_kind_label_'+x.kind)+' · '+x.title;b.dataset.anonPrivate='text';li.append(t,b);return li}):[Object.assign(document.createElement('li'),{textContent:tr('notify_upcoming_none')})]))};
 for(const k of Object.keys(kinds))$('policy-kind-'+k).onchange=paintUpcoming;paintUpcoming();
 $('notify-preview-open').onclick=()=>{const first=upcoming()[0],title=first?first.title:(state.tasks.find(t=>!['done','retired'].includes(t.state))?.title||'Day Attendant'),kind=first?.kind||'reminder';$('notify-preview-text').textContent=tr('notify_kind_label_'+kind)+' · '+title;$('notify-preview').hidden=false;$('notify-preview-note').hidden=false};for(const item of d.querySelectorAll('[data-day]'))item.checked=n.weekdays.includes(Number(item.dataset.day));
 for(const [id,key] of [['start','start'],['end','end'],['quiet-start','quietStart'],['quiet-end','quietEnd'],['interval','intervalMinutes'],['repeat','unchangedRepeatMinutes'],['budget','dailyBudget']])$('policy-'+id).value=n[key];const pausedUntil=storedTime('policy-pause',n.pausedUntil);
 const info=state.operations_status||{};$('operations-info').textContent=tr('daily_9f17db4f34')+(info.scheduler?.installed?info.scheduler.backend:tr('daily_d49fe2c403'))+' · '+tr('daily_4873c0956f')+(info.last_tick?ui.full(info.last_tick.at)+' · '+info.last_tick.status:tr('daily_71f8e7976e'));
 $('continuity-info').textContent=tr('daily_aca266cd4d')+state.messages.length+(state.conversation?.clearedAt?' · '+tr('daily_32332d2e56')+ui.full(state.conversation.clearedAt):'');
 const loadBackups=()=>safely(async()=>{const list=await api('/api/backups');$('backup-list').replaceChildren();for(const b of list.backups.slice(0,8)){const row=document.createElement('p');row.textContent=(b.valid?ui.full(b.captured_at)+' · '+b.category:tr('daily_add55dfca1'))+' · '+b.path;$('backup-list').append(row)}});
 $('backup-create').onclick=()=>formAction(d.id,async()=>{$('backup-create').disabled=true;try{await deliver('/api/backups',{});await loadBackups();$('backup-create').textContent=tr('backup_created')}finally{$('backup-create').disabled=false}});
 $('diagnostics-open').onclick=e=>showDiagnostics(e.currentTarget);loadBackups();
 d.querySelector('form').onsubmit=e=>{e.preventDefault();formAction(d.id,async()=>{const harness=$('setting-harness').value,model=$('setting-model').value||null,effort=$('setting-effort').value;
 const policy={...n,enabled:$('policy-enabled').checked,weekdays:[...d.querySelectorAll('[data-day]:checked')].map(x=>Number(x.dataset.day)),start:$('policy-start').value,end:$('policy-end').value,quietStart:$('policy-quiet-start').value,quietEnd:$('policy-quiet-end').value,intervalMinutes:Number($('policy-interval').value),unchangedRepeatMinutes:Number($('policy-repeat').value),dailyBudget:Number($('policy-budget').value),pausedUntil:pausedUntil(),technicalDefault:false,kinds:Object.fromEntries(['soon','overdue','reminder'].map(k=>[k,$('policy-kind-'+k).checked]))};
 const values={name:$('setting-name').value.trim(),timezone:$('setting-zone').value.trim(),notification_policy:policy,autoOrganize:$('setting-organize').checked};if(harness!==p.harness||model!==p.model){values.harness=harness;values.model=harness!==p.harness&&model===p.model?null:model}if(effort!==initialEffort||values.harness)values.effort=effort||null
 await deliver('/api/settings',{values},settingsRevision);d.close('saved');await flow.refresh()})};open(d,origin);
}
$('settings-open').onclick=e=>openSettings(e.currentTarget);
async function showDiagnostics(origin){
 const id='diagnostic-dialog';$(id)?.remove();const data=await api('/api/doctor');const d=dialog(id,tr('daily_725e583a85'),'<div id="diagnostic-body"></div>',button('diagnostic-close','daily_bbfa773e5a'));
 const body=$('diagnostic-body'),pre=document.createElement('pre');pre.className='operation-result';pre.textContent=JSON.stringify(data,null,2);body.append(pre);
 for(const operation of data.operations){const b=document.createElement('button');b.className='btn';b.type='button';b.textContent=tr('daily_f6a34f2768')+operation.key;b.onclick=()=>safely(()=>reviewRecovery(operation.key,b));body.append(b)}
 $('diagnostic-close').onclick=()=>d.close('close');open(d,origin);
}
async function reviewRecovery(key,origin){
 const observed=await api('/api/recovery/inspect',{operation_key:key});const id='recovery-dialog';$(id)?.remove();const d=dialog(id,tr('daily_3f7cdad207'),`<p class="warning">${tr('daily_93cdc37ee4')}</p><pre id="recovery-data" class="operation-result"></pre>`,button('recovery-complete','daily_84fb7a04db')+button('recovery-keep','daily_7aa2480e49'));
 $('recovery-data').textContent=JSON.stringify(observed,null,2);$('recovery-complete').disabled=!observed.can_complete;
 for(const [id,resolution] of [['recovery-complete','complete'],['recovery-keep','keep_observed']])$(id).onclick=()=>formAction(d.id,async()=>{await api('/api/recovery/resolve',{operation_key:key,resolution,precondition:observed.precondition});d.close('resolved');await flow.refresh()});open(d,origin);
}

const upload=document.createElement('div');upload.className='attachment-list';upload.innerHTML=`<label class="link-button" for="chat-images" data-i18n="attach_images">${tr('daily_537c963567')}</label><input id="chat-images" type="file" accept="image/png,image/jpeg,image/webp" multiple hidden><div id="chat-image-list"></div>`;$('composer').after(upload);
$('chat-images').onchange=()=>safely(async()=>{const files=[...$('chat-images').files];for(const file of files){const encoded=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file)});const result=await deliver('/api/attachments',{name:file.name,mime:file.type,base64:encoded});selectedImages.push(result)}$('chat-images').value='';renderSelectedImages()});
function renderSelectedImages(){$('chat-image-list').replaceChildren();for(const item of selectedImages){const row=document.createElement('div'),b=document.createElement('button');row.textContent=item.name+' ';b.type='button';b.className='link-button';b.textContent=tr('daily_e963907dac');b.onclick=()=>{selectedImages=selectedImages.filter(x=>x.id!==item.id);renderSelectedImages()};row.append(b);$('chat-image-list').append(row)}}
const originalSend=$('send-message').onclick;$('send-message').onclick=()=>{if(!selectedImages.length||$('conversation-input').value.trim()==='/clear')return originalSend();return safely(async()=>{const input=$('conversation-input'),value=input.value.trim();if(!value)throw Error(tr('daily_f4314e5483'));$('send-message').disabled=true;const ids=selectedImages.map(x=>x.id);try{await deliver('/api/chat',{text:value,attachments:ids,capture_only:true});selectedImages=selectedImages.filter(x=>!ids.includes(x.id));renderSelectedImages();if(input.value.trim()===value)input.value=''}finally{$('send-message').disabled=false}})};
const undoneMessages=new Set();
function receipts(state){for(const el of $('messages').children){
 const message=state.messages.find(m=>m.key===el.dataset.key);if(message?.role!=='assistant')continue;let data;try{data=JSON.parse(message.data||'{}')||{}}catch{continue}
 let box=el.querySelector('.receipt-list');if(!box){box=document.createElement('div');box.className='receipt-list';el.append(box)}box.replaceChildren();
 const ids=data.proposal_ids||[];let saved=0,waiting=0,applied=0;
 for(const id of ids){const p=state.rawProposals?.find(x=>x.id===id)||state.proposals.find(x=>x.id===id);const row=document.createElement('span'),title=p?.intent?.payload?.title||state.tasks.find(t=>t.id===p?.intent?.payload?.uuid)?.title||tr('daily_64fbd995d3');
  if(['applied','unchanged'].includes(p?.phase))saved++;if(p?.phase==='applied')applied++;
  // A proposal waiting for the person says it was not saved and links to where it is decided.
  if(['unavailable','review','stale','invalid'].includes(p?.phase)){waiting++;const kind=p.phase==='unavailable'&&p.error_code==='review_insufficient'?'insufficient':p.phase;
   row.textContent=title+' · '+tr('receipt_wait_'+kind+(ui.creates(p.intent.action)?'':'_change'))+' ';const open=document.createElement('button');open.type='button';open.className='link-button';open.textContent=tr('receipt_open');open.onclick=()=>ui.showProposal(id);row.append(open)}
  else row.textContent=title+' · '+(p?tr('phase_'+p.phase):tr('daily_b82542983a'));
  box.append(row)}
 if(waiting){const summary=document.createElement('p');summary.className='receipt-summary';summary.textContent=ui.formatted(waiting===1?'receipt_saved_summary_one':'receipt_saved_summary',{saved,total:ids.length,waiting});box.prepend(summary)}
 // Changes from the conversation applied at once; one Undo reverts all of them, newest first.
 const user=message.key.replace(/:assistant$/,'');if(applied&&!undoneMessages.has(user)&&!state.readOnly){const undo=document.createElement('button');undo.type='button';undo.className='link-button';undo.textContent=tr(applied===1?'undo_message_change':'undo_message_changes');undo.onclick=()=>safely(async()=>{undo.disabled=true;await deliver('/api/undo',{message_key:user});undoneMessages.add(user);document.getElementById('status').textContent=tr('changes_undone');receipts(flow.snapshot())});box.append(undo)}
 for(const [items,label] of [[data.unprocessed,tr('daily_7b3bc9fd91')],[data.uncertainties,tr('daily_df84985b43')]])for(const item of items||[]){const row=document.createElement('p');row.textContent=label+': '+item;box.append(row)}
}}
const historyButton=document.createElement('button');historyButton.type='button';historyButton.id='organize-history';historyButton.className='btn ghost';historyButton.setAttribute('aria-haspopup','dialog');$('context-open').before(historyButton);
const organizationNotice=document.createElement('div');organizationNotice.className='organization-notice';organizationNotice.hidden=true;organizationNotice.setAttribute('role','status');quickPreview.after(organizationNotice);
let knownOrganizations=null;
async function undoOrganization(org,partial=false){await deliver('/api/organization/undo',{fact_id:org.factId,partial});await flow.refresh();organizationNotice.hidden=true}
function askUndo(org,origin){
 if(!org.touched.length){safely(()=>undoOrganization(org));return}
 const d=dialog('organize-undo-dialog',tr('organize_changed'),'<p>'+esc(tr('organize_partial_explain'))+'</p>',`<button type="button" class="btn" data-cancel>${esc(tr('cancel'))}</button><button type="button" class="btn primary" data-partial>${esc(tr('organize_partial'))}</button>`);
 d.querySelector('[data-cancel]').onclick=()=>d.close();d.querySelector('[data-partial]').onclick=()=>safely(async()=>{await undoOrganization(org,true);d.close()});d.addEventListener('close',()=>d.remove());open(d,origin);
}
function showHistory(origin){
 const state=flow.snapshot(),d=dialog('organize-history-dialog',tr('organize_history'),'<div class="organization-list"></div>','');const list=d.querySelector('.organization-list');
 for(const org of state.organizations||[]){const section=document.createElement('section'),title=document.createElement('p'),summary=document.createElement('p');title.textContent=org.original;title.setAttribute('data-anon-private','text');summary.textContent=tr('organize_summary').replace('{tasks}',org.tasks.length).replace('{dependencies}',org.dependencies)+(org.groups.length?' · '+org.groups.join(', '):'');section.append(title,summary);
  const names=document.createElement('p');names.textContent=org.tasks.map(id=>state.tasks.find(t=>t.id===id)?.title||'').filter(Boolean).join(' · ');names.setAttribute('data-anon-private','text');section.append(names);
  if(!org.undone){const undo=document.createElement('button');undo.type='button';undo.className='btn';undo.textContent=tr('organize_undo');undo.onclick=()=>{d.close();askUndo(org,origin)};section.append(undo)}else{const label=document.createElement('p');label.textContent=tr('organize_undone');section.append(label)}list.append(section)
 }
 if(!list.children.length)list.textContent=tr('organize_empty');d.addEventListener('close',()=>d.remove());open(d,origin);
}
historyButton.onclick=()=>showHistory(historyButton);
function updateOrganizations(state){const items=state.organizations||[];historyButton.textContent=tr('organize_count').replace('{n}',items.length);
 const ids=new Set(items.map(x=>x.factId));if(knownOrganizations){const newest=items.find(x=>!knownOrganizations.has(x.factId)&&!x.undone);if(newest){organizationNotice.replaceChildren();const label=document.createElement('span');label.textContent=tr('organize_notice').replace('{tasks}',newest.tasks.length);const view=document.createElement('button');view.type='button';view.className='link-button';view.textContent=tr('organize_view');view.onclick=()=>showHistory(view);const undo=document.createElement('button');undo.type='button';undo.className='link-button';undo.textContent=tr('organize_undo');undo.onclick=()=>askUndo((flow.snapshot().organizations||[]).find(x=>x.factId===newest.factId)||newest,undo);organizationNotice.append(label,view,undo);organizationNotice.hidden=false}}knownOrganizations=ids;
}
function update(state){
 if(!state.profile)return;
 updateOrganizations(state);
 globalThis.dayProactive?.update(state);
 const digest=JSON.stringify([state.agentMode,state.profile,state.notification_policy,state.diagnostics,state.operations_status,state.calendar_events,state.tasks,state.rawProposals,state.messages,state.readOnly,document.documentElement.lang,state.timezone,(state.calendar_events||[]).map(e=>new Date(e.end_at)>=new Date(state.now))]);if(digest===lastDailyDigest)return;lastDailyDigest=digest;

 $('profile-badge').toggleAttribute('data-anon-private',!state.synthetic);$('profile-badge').textContent=state.synthetic?tr('daily_ab7047d4a0'):state.profile.name;$('profile-footer').textContent=tr('daily_916bf2d05b');$('settings-open').title=tr('daily_7831a7f8c4');$('settings-open').setAttribute('aria-label',tr('daily_7831a7f8c4'));$('settings-open').querySelector('span').textContent=tr('daily_c7f73bb54d');$('capture-open').textContent=tr('daily_54e17efed4');renderQuick();
 const diag=JSON.stringify([state.diagnostics,state.operations_status?.last_tick?.status]);if(diag!==lastDiagnostics){lastDiagnostics=diag;const issue=state.readOnly||state.diagnostics?.reminders?.length>0||state.operations_status?.last_tick?.status==='failed';diagnostic.hidden=!issue;diagnostic.replaceChildren();if(issue){const p=document.createElement('p');p.textContent=state.readOnly?tr('daily_02380a21f9'):state.diagnostics?.reminders?.length?tr('daily_5a9ce773f4'):tr('daily_e8d5e4fb5d');const b=document.createElement('button');b.className='link-button';b.textContent=tr('daily_ed54f97283');b.onclick=()=>safely(()=>showDiagnostics(b));diagnostic.append(p,b)}}
 const events=(state.calendar_events||[]).filter(e=>new Date(e.end_at)>=new Date(state.now)),eventDigest=JSON.stringify([events,state.timezone,document.documentElement.lang]);if(lastCalendar!==eventDigest){lastCalendar=eventDigest;calendar.innerHTML=`<h2>${tr('daily_4342720ce3')}</h2>${events.length?'':`<p class="hint">${tr('daily_b910be6fd3')}</p>`}`;for(const event of events){const row=document.createElement('div');row.className='daily-row';const copy=document.createElement('div'),b=document.createElement('button'),time=document.createElement('p');b.type='button';b.className='link-button';b.setAttribute('data-anon-private','text');b.textContent=event.title;b.onclick=()=>openCapture(b,event);time.setAttribute('data-anon-safe','text');time.textContent=ui.full(event.start_at)+' — '+ui.full(event.end_at);copy.append(b,time);const cancel=document.createElement('button');cancel.type='button';cancel.className='btn ghost';cancel.textContent=tr('cancel');cancel.onclick=()=>safely(async()=>{await flow.request('event_cancel',{uuid:event.uuid});await flow.refresh()});if(event.pending)b.disabled=cancel.disabled=true;row.append(copy,cancel);calendar.append(row)}}
 queueMicrotask(()=>{receipts(state);$('capture-open').disabled=state.readOnly;$('qa-input').disabled=$('qa-submit').disabled=state.readOnly;$('send-message').disabled=state.agentMode.mode!=='active'||state.readOnly||state.messages.some(m=>m.role==='user'&&m.status==='pending')});
}
// Localization changes labels only; typed task content is never translated.
$('locale-choice').addEventListener('change',()=>{lastCalendar='';lastDiagnostics='';quickLabels();renderQuick();update(flow.snapshot())});
quickLabels();renderQuick();
globalThis.dayDaily={update};if(flow.snapshot().profile)update(flow.snapshot());
})();
