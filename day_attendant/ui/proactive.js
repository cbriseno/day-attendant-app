/* Approved #42 presentation, using the current model and pause endpoints. */
(() => {
'use strict';
const {tr,esc,api,flow,safely}=globalThis.dayUI,$=id=>document.getElementById(id);
const lang=()=>(document.documentElement.lang||'en').startsWith('es')?'es-MX':'en-US',tz=()=>state?.timezone||'UTC';
Object.assign(globalThis.dayTranslations.es,{
 checkins_title:'Seguimiento',checkins_run:'Revisar ahora',checkins_running:'Revisando…',checkins_next:'Próxima revisión {time}',checkins_quiet:'En horas de descanso: no te escribo',checkins_off:'Seguimiento apagado',
 checkins_empty:'Todo en orden por ahora. Te escribo si algo se atora.',checkins_limit:'Ya llegué al máximo de {n} preguntas por hoy; lo puedes cambiar en Configuración.',checkins_nothing_new:'Revisé y no hay nada nuevo que preguntarte.',checkins_more:'y {n} más',
 checkins_demo_tag:'ejemplo',checkin_overdue:'«{title}» ya venció ({due}). ¿Ya la hiciste? Si no, la muevo para que no se te pierda.',
 checkin_due_soon:'«{title}» vence {due}. ¿Quieres empezarla hoy?',checkin_active_long:'«{title}» lleva {days} días en curso. ¿Ya quedó o la dejamos para mañana?',
 checkin_stale:'Veo que «{title}» lleva {days} días sin movimiento. ¿Sigue en pie, la pospongo o ya no aplica?',
 checkin_important:'«{title}» suena muy importante. ¿Ya la hiciste o la empezamos ahora?',
 checkin_risk:'«{title}» espera a «{blocker}», que no se ha movido. Si empiezas por «{blocker}», destrabas lo importante.',
 why_due:'Por qué: tiene fecha',why_stale:'Por qué: sin movimiento',why_important:'Por qué: prioridad alta y sin empezar',why_risk:'Por qué: un requisito detiene algo importante',
 answer_done:'Ya la hice',answer_start:'Empezar',answer_snooze:'Mañana',answer_retire:'Ya no aplica',answer_later:'Luego',
 answered_done:'Listo, la marqué como hecha.',answered_start:'La puse en curso.',answered_snooze:'La moví a mañana a las 9:00.',answered_retire:'La retiré; Deshacer la regresa.',answered_later:'Te pregunto más tarde.',
 agent_mode_active:'Activo',agent_mode_paused:'En pausa',agent_mode_off:'Desactivado',agent_mode_label:'Uso del asistente',
 agent_pause_1h:'Pausar 1 hora',agent_pause_today:'Pausar por hoy',agent_pause_forever:'Pausar hasta que lo reanude',agent_turn_off:'Desactivar',agent_resume:'Reanudar',
 agent_paused_state:'En pausa: no gasta tokens',agent_paused_until:'En pausa hasta {time}: no gasta tokens',agent_off_state:'Desactivado: no gasta tokens',
 agent_paused_short:'No gasta tokens; recordatorios, copias y reglas locales siguen.',agent_paused_composer:'El asistente está en pausa. Reanúdalo para escribirle.',agent_paused_hint:'Sin el asistente siguen los recordatorios, las copias y las reglas locales; no se manda nada al modelo.',
 proactive_section:'Asistente proactivo',proactive_enabled:'Hacerme preguntas de seguimiento',proactive_every:'Revisar cada',every_30:'30 minutos',every_60:'1 hora',every_120:'2 horas',
 proactive_quiet_start:'Descanso desde',proactive_quiet_end:'Descanso hasta',proactive_max:'Máximo de preguntas al día',proactive_kinds:'Sobre qué',
 kind_stale:'Tareas sin movimiento',kind_important:'Lo que suena importante',kind_due:'Lo que vence o venció',kind_risk:'Riesgos (requisitos atorados)',
 proactive_hint:'Mientras la app está abierta revisa con el asistente cada intervalo; respeta el descanso y el límite diario.',
 agent_mode_hint:'Pausa o desactiva toda llamada al modelo: conversación, revisión posterior, orden sugerido y seguimiento.'});
Object.assign(globalThis.dayTranslations.en,{
 checkins_title:'Check-ins',checkins_run:'Check now',checkins_running:'Checking…',checkins_next:'Next check {time}',checkins_quiet:'Rest hours: I will not write',checkins_off:'Check-ins off',
 checkins_empty:'All good for now. I will write if something gets stuck.',checkins_limit:'I reached the limit of {n} questions for today; change it in Settings.',checkins_nothing_new:'Checked: nothing new to ask.',checkins_more:'and {n} more',
 checkins_demo_tag:'example',checkin_overdue:'«{title}» is past due ({due}). Did you do it? If not, I can move it so it does not get lost.',
 checkin_due_soon:'«{title}» is due {due}. Want to start it today?',checkin_active_long:'«{title}» has been in progress for {days} days. Is it done, or tomorrow?',
 checkin_stale:'«{title}» has not moved in {days} days. Still on, postpone, or no longer relevant?',
 checkin_important:'«{title}» sounds important. Did you do it, or shall we start now?',
 checkin_risk:'«{title}» waits for «{blocker}», which has not moved. Starting «{blocker}» unblocks what matters.',
 why_due:'Why: it has a date',why_stale:'Why: no movement',why_important:'Why: high priority, not started',why_risk:'Why: a prerequisite holds something important',
 answer_done:'Done',answer_start:'Start',answer_snooze:'Tomorrow',answer_retire:'No longer relevant',answer_later:'Later',
 answered_done:'Marked as done.',answered_start:'Started.',answered_snooze:'Moved to tomorrow 9:00.',answered_retire:'Retired; Undo brings it back.',answered_later:'I will ask later.',
 agent_mode_active:'Active',agent_mode_paused:'Paused',agent_mode_off:'Off',agent_mode_label:'Assistant use',
 agent_pause_1h:'Pause 1 hour',agent_pause_today:'Pause for today',agent_pause_forever:'Pause until I resume',agent_turn_off:'Turn off',agent_resume:'Resume',
 agent_paused_state:'Paused: no tokens spent',agent_paused_until:'Paused until {time}: no tokens spent',agent_off_state:'Off: no tokens spent',
 agent_paused_short:'No tokens spent; reminders, backups and local rules keep working.',agent_paused_composer:'The assistant is paused. Resume it to write.',agent_paused_hint:'Reminders, backups and local rules keep working; nothing is sent to the model.',
 proactive_section:'Proactive assistant',proactive_enabled:'Ask me follow-up questions',proactive_every:'Check every',every_30:'30 minutes',every_60:'1 hour',every_120:'2 hours',
 proactive_quiet_start:'Rest from',proactive_quiet_end:'Rest until',proactive_max:'Most questions per day',proactive_kinds:'About',
 kind_stale:'Tasks without movement',kind_important:'What sounds important',kind_due:'What is due or overdue',kind_risk:'Risks (stuck prerequisites)',
 proactive_hint:'While the app is open, checks use the assistant at each interval and respect rest hours and the daily limit.',
 agent_mode_hint:'Pause or turn off every model call: conversation, later review, suggested order and check-ins.'});
const T=(k,p={})=>Object.entries(p).reduce((s,[a,b])=>s.split('{'+a+'}').join(b),tr(k));
const when=iso=>new Date(iso).toLocaleString(lang(),{timeZone:tz(),weekday:'short',day:'numeric',month:'short',hour:'2-digit',minute:'2-digit',hour12:lang()==='en-US'});
const hour=iso=>new Date(iso).toLocaleTimeString(lang(),{timeZone:tz(),hour:'2-digit',minute:'2-digit',hour12:lang()==='en-US'});
let state=null,busy=false,flash='',started=false;
function modeOf(s){return s?.agentMode||s?.proactive?.agentMode||{mode:'active'}}
function stateLabel(s){const m=modeOf(s);return m.mode==='off'?tr('agent_off_state'):m.mode==='paused'?(m.until?T('agent_paused_until',{time:hour(m.until)}):tr('agent_paused_state')):null}
function message(c){return c.message}
function render(){
 const box=$('checkins');if(!box||!state?.proactive)return;const P=state.proactive,s=P.settings,tasks=state.tasks;
 const meta=!s.enabled?tr('checkins_off'):P.quiet?tr('checkins_quiet'):stateLabel(state)||T('checkins_next',{time:hour(P.nextPass)});
 const shown=P.checkins.slice(0,3),rest=P.checkins.length-shown.length;
 box.innerHTML='<div class="checkins-head"><h3 id="checkins-title">'+esc(tr('checkins_title'))+(P.checkins.length?' <span class="checkins-count">'+P.checkins.length+'</span>':'')+'</h3><span class="checkins-meta" data-anon-safe="text">'+esc(meta)+'</span><button type="button" class="link-button" id="checkins-run"'+(busy||state.readOnly||modeOf(state).mode!=='active'?' disabled':'')+'>'+esc(tr(busy?'checkins_running':'checkins_run'))+'</button></div>'
  +(flash?'<p class="checkins-flash" role="status">'+esc(flash)+'</p>':'')
  +(shown.length?shown.map(c=>'<article class="checkin" data-kind="'+c.kind+'" aria-label="'+esc(message(c))+'"><p class="checkin-text" data-anon-private="text">'+esc(message(c))+'</p><p class="checkin-why"><span>'+esc(tr('why_'+c.kind))+'</span>'+(c.origin==='demo-model'?'<span class="checkin-tag" title="'+esc(tr('checkins_demo'))+'">'+esc(tr('checkins_demo_tag'))+'</span>':'')+'</p><div class="checkin-actions">'
   +c.answers.filter(a=>a!=='later').map((a,i)=>'<button type="button" class="btn'+(i===0?' primary':'')+'" data-checkin="'+c.id+'" data-answer="'+a+'"'+(state.readOnly?' disabled':'')+'>'+esc(tr('answer_'+a))+'</button>').join('')
   +'<button type="button" class="link-button" data-checkin="'+c.id+'" data-answer="later">'+esc(tr('answer_later'))+'</button></div></article>').join('')
   +(rest>0?'<p class="checkins-more">'+esc(T('checkins_more',{n:rest}))+'</p>':''):'<p class="checkins-empty">'+esc(tr('checkins_empty'))+'</p>')
;
 const m=modeOf(state),b=$('agent-mode');if(b){b.dataset.mode=m.mode;b.querySelector('.agent-mode-label').textContent=tr('agent_mode_'+m.mode);b.title=tr('agent_mode_hint')}
 $('agent-bar-label')&&($('agent-bar-label').textContent=tr('agent_mode_label'));$('agent-bar-note')&&($('agent-bar-note').textContent=modeOf(state).mode==='active'?'':tr('agent_paused_short'));
 const input=$('conversation-input'),off=m.mode!=='active';if(input){input.disabled=off;input.placeholder=off?tr('agent_paused_composer'):tr('write_what_you_want_to_return_to')}
 $('send-message')&&($('send-message').disabled=off);document.documentElement.classList.toggle('agent-paused',off);
}
function update(s){state=s;render();if(!started){started=true;void tick();setInterval(()=>void tick(),60000)}}
async function tick(){if(busy||!state?.profile||state.readOnly||modeOf(state).mode!=='active')return;busy=true;try{await post({op:'tick'});await flow.refresh()}catch{}finally{busy=false;render()}}
async function post(body){return api('/api/proactive',body)}
document.addEventListener('click',e=>{
 const run=e.target.closest('#checkins-run');if(run){busy=true;flash='';render();safely(async()=>{try{const r=await post({op:'run'});if(!r.added.length)flash=r.limited?T('checkins_limit',{n:state.proactive.settings.maxPerDay}):tr('checkins_nothing_new')}finally{busy=false;await flow.refresh();render()}});return}
 const a=e.target.closest('[data-checkin]');if(a){const answer=a.dataset.answer,card=state.proactive.checkins.find(c=>c.id===a.dataset.checkin),task=state.tasks.find(t=>t.id===card?.task);if(answer==='done'&&task?.blockReason){confirmAnswer(a,task);return}for(const x of a.parentElement.querySelectorAll('button'))x.disabled=true;
  safely(async()=>{try{await post({op:'answer',id:a.dataset.checkin,answer,key:crypto.randomUUID()});flash=tr('answered_'+answer)}finally{await flow.refresh();render()}});return}
 const mode=e.target.closest('#agent-mode');if(mode){e.stopPropagation();toggleMenu(mode);return}
 const item=e.target.closest('[data-agent-mode]');if(item){closeModeMenu();const [m,until]=item.dataset.agentMode.split(':');safely(async()=>{await api('/api/agent-mode',{mode:m,...(until?{duration:until}:{})});await flow.refresh();render();$('agent-mode')?.focus()});return}
 if(!e.target.closest('.agent-mode-menu'))closeModeMenu();
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&document.querySelector('.agent-mode-menu')){closeModeMenu();$('agent-mode')?.focus()}});
function confirmAnswer(anchor,task){
 closeModeMenu();const node=document.createElement('div');node.className='row-menu';node.setAttribute('role','dialog');node.setAttribute('aria-label',tr('block_done_anyway'));
 node.innerHTML='<p class="menu-confirm">'+esc(tr('block_done_confirm').replace('{reason}',task.blockReason))+'</p><div class="menu-confirm-actions"><button class="btn" type="button" data-keep>'+esc(tr('cancel'))+'</button><button class="btn" type="button" data-finish>'+esc(tr('block_done_anyway'))+'</button></div>';
 const host=anchor.closest('dialog')||document.body;host.append(node);const sheet=matchMedia('(max-width:600px)').matches,scrim=document.createElement('div');
 scrim.className='menu-scrim';host.insertBefore(scrim,node);if(sheet)node.classList.add('sheet');else{const r=anchor.getBoundingClientRect();node.style.top=Math.min(r.bottom+6,innerHeight-node.offsetHeight-8)+'px';node.style.left=Math.max(8,Math.min(r.left,innerWidth-node.offsetWidth-8))+'px'}
 const close=()=>{node.remove();scrim.remove();document.removeEventListener('keydown',escape);anchor.focus()};const escape=e=>{if(e.key==='Escape'){e.preventDefault();close()}};
 document.addEventListener('keydown',escape);scrim.onclick=close;node.querySelector('[data-keep]').onclick=close;node.querySelector('[data-finish]').onclick=()=>{close();safely(async()=>{await post({op:'answer',id:anchor.dataset.checkin,answer:'done',key:crypto.randomUUID()});flash=tr('answered_done');await flow.refresh()})};node.querySelector('[data-keep]').focus();
}
function closeModeMenu(){document.querySelector('.agent-mode-menu')?.remove();document.querySelector('.agent-mode-scrim')?.remove();$('agent-mode')?.setAttribute('aria-expanded','false')}
function toggleMenu(anchor){if(document.querySelector('.agent-mode-menu')){closeModeMenu();return}const m=modeOf(state).mode;
 const opts=[['active','agent_resume',m==='active'?'agent_mode_active':'agent_resume'],['paused:1h','agent_pause_1h'],['paused:today','agent_pause_today'],['paused:forever','agent_pause_forever'],['off','agent_turn_off']];
 const node=document.createElement('div');node.className='row-menu agent-mode-menu';node.setAttribute('role','menu');
 const cur=m==='paused'?('paused:'+(modeOf(state).duration||(modeOf(state).until?'1h':'forever'))):m;
 node.innerHTML='<p class="menu-title">'+esc(tr('agent_mode_label'))+'</p>'+opts.map(([v,k,label])=>'<button type="button" class="menu-item" role="menuitemradio" aria-checked="'+(v===cur)+'" data-agent-mode="'+v+'">'+esc(v===cur&&v==='paused:1h'?T('agent_paused_until',{time:hour(modeOf(state).until)}):tr(label||k))+'</button>').join('')+'<p class="menu-confirm agent-mode-foot">'+esc(tr('agent_mode_hint'))+' '+esc(tr('agent_paused_hint'))+'</p>';
 const host=anchor.closest('dialog')||document.body,sheet=matchMedia('(max-width: 600px)').matches;if(sheet){node.classList.add('sheet');const scrim=document.createElement('div');scrim.className='menu-scrim agent-mode-scrim';host.append(scrim)}
 host.append(node);anchor.setAttribute('aria-expanded','true');
 if(!sheet){const r=anchor.getBoundingClientRect();node.style.position='fixed';node.style.top=(r.bottom+6)+'px';node.style.left=Math.max(8,Math.min(r.right-node.offsetWidth,innerWidth-node.offsetWidth-8))+'px'}
 (node.querySelector('[aria-checked=true]')||node.querySelector('button')).focus()}
// Settings: two sections inside «Configuración diaria»; each control saves at once.
function settingsHtml(){const k=['stale','important','due','risk'];
 return `<details class="daily-section" open id="agent-use-section"><summary>${esc(tr('agent_mode_label'))}</summary><div class="daily-grid"><label class="field"><span>${esc(tr('agent_mode_label'))}</span><select id="setting-agent-mode"><option value="active">${esc(tr('agent_mode_active'))}</option><option value="paused:1h">${esc(tr('agent_pause_1h'))}</option><option value="paused:today">${esc(tr('agent_pause_today'))}</option><option value="paused:forever">${esc(tr('agent_pause_forever'))}</option><option value="off">${esc(tr('agent_turn_off'))}</option></select></label></div><p class="hint">${esc(tr('agent_mode_hint'))} ${esc(tr('agent_paused_hint'))}</p></details>`
 +`<details class="daily-section" open id="proactive-section"><summary>${esc(tr('proactive_section'))}</summary><label class="context-checkbox"><input id="proactive-enabled" type="checkbox">${esc(tr('proactive_enabled'))}</label><div class="daily-grid"><label class="field"><span>${esc(tr('proactive_every'))}</span><select id="proactive-every"><option value="30">${esc(tr('every_30'))}</option><option value="60">${esc(tr('every_60'))}</option><option value="120">${esc(tr('every_120'))}</option></select></label><label class="field"><span>${esc(tr('proactive_max'))}</span><input id="proactive-max" type="number" min="1" max="20"></label><label class="field"><span>${esc(tr('proactive_quiet_start'))}</span><input id="proactive-quiet-start" type="time"></label><label class="field"><span>${esc(tr('proactive_quiet_end'))}</span><input id="proactive-quiet-end" type="time"></label></div><fieldset class="proactive-kinds"><legend>${esc(tr('proactive_kinds'))}</legend>${k.map(x=>`<label class="context-checkbox"><input type="checkbox" data-proactive-kind="${x}">${esc(tr('kind_'+x))}</label>`).join('')}</fieldset><p class="hint">${esc(tr('proactive_hint'))}</p></details>`}
function wireSettings(){const P=state?.proactive;if(!P||!$('proactive-section'))return;const s=P.settings,m=modeOf(state);
 $('setting-agent-mode').value=m.mode==='paused'?('paused:'+(m.duration||(m.until?'1h':'forever'))):m.mode;if(m.mode==='paused'&&m.until)$('setting-agent-mode').selectedOptions[0].textContent=T('agent_paused_until',{time:hour(m.until)});
 $('proactive-enabled').checked=s.enabled;$('proactive-every').value=String(s.every);$('proactive-max').value=s.maxPerDay;$('proactive-quiet-start').value=s.quietStart;$('proactive-quiet-end').value=s.quietEnd;
 for(const box of document.querySelectorAll('[data-proactive-kind]'))box.checked=s.kinds[box.dataset.proactiveKind];
 const save=values=>safely(async()=>{await post({op:'settings',values});await flow.refresh()});
 $('setting-agent-mode').onchange=e=>{const [mode,until]=e.target.value.split(':');safely(async()=>{await api('/api/agent-mode',{mode,...(until?{duration:until}:{})});await flow.refresh()})};
 $('proactive-enabled').onchange=e=>save({enabled:e.target.checked});$('proactive-every').onchange=e=>save({every:Number(e.target.value)});
 $('proactive-max').onchange=e=>{const n=Math.round(Number(e.target.value));if(n>=1&&n<=20)save({maxPerDay:n})};
 for(const id of ['proactive-quiet-start','proactive-quiet-end'])$(id).onchange=()=>{if($('proactive-quiet-start').value&&$('proactive-quiet-end').value)save({quietStart:$('proactive-quiet-start').value,quietEnd:$('proactive-quiet-end').value})};
 for(const box of document.querySelectorAll('[data-proactive-kind]'))box.onchange=()=>save({kinds:{[box.dataset.proactiveKind]:box.checked}})}
globalThis.dayProactive={update,stateLabel,settingsHtml,wireSettings};
})();
