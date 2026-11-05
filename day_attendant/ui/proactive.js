/* Check-ins are requested only by this open page; the native scheduler never calls a model. */
(() => {
'use strict';
const {api,flow,safely,tr,esc}=globalThis.dayUI,$=id=>document.getElementById(id);
Object.assign(globalThis.dayTranslations.en,{checkins:'Check-ins',check_now:'Check now',checking:'Checking…',checkin_empty:'Nothing to ask right now.',checkin_limited:'Daily question limit reached.',checkin_done:'Done',checkin_start:'Start',checkin_snooze:'Tomorrow',checkin_retire:'No longer relevant',checkin_later:'Later',proactive_title:'Proactive assistant',proactive_enabled:'Ask follow-up questions',proactive_every:'Check every',proactive_max:'Maximum questions per day',proactive_from:'Rest from',proactive_until:'Rest until',proactive_about:'About',proactive_stale:'No movement',proactive_important:'Important tasks',proactive_due:'Due or overdue',proactive_risk:'Blocked work',proactive_hint:'Checks use the assistant while this page is open and respect rest hours and the daily limit.',proactive_30:'30 minutes',proactive_60:'1 hour',proactive_120:'2 hours',checkin_next:'Next check',checkin_rest:'Rest hours',checkin_off:'Check-ins off',checkin_paused:'Assistant paused'});
Object.assign(globalThis.dayTranslations.es,{checkins:'Seguimiento',check_now:'Revisar ahora',checking:'Revisando…',checkin_empty:'No hay preguntas por ahora.',checkin_limited:'Llegué al máximo de preguntas de hoy.',checkin_done:'Ya la hice',checkin_start:'Empezar',checkin_snooze:'Mañana',checkin_retire:'Ya no aplica',checkin_later:'Luego',proactive_title:'Asistente proactivo',proactive_enabled:'Hacerme preguntas de seguimiento',proactive_every:'Revisar cada',proactive_max:'Máximo de preguntas al día',proactive_from:'Descanso desde',proactive_until:'Descanso hasta',proactive_about:'Sobre qué',proactive_stale:'Sin movimiento',proactive_important:'Tareas importantes',proactive_due:'Por vencer o vencidas',proactive_risk:'Trabajo bloqueado',proactive_hint:'Revisa con el asistente mientras esta página está abierta y respeta el descanso y el límite diario.',proactive_30:'30 minutos',proactive_60:'1 hora',proactive_120:'2 horas',checkin_next:'Próxima revisión',checkin_rest:'Horas de descanso',checkin_off:'Seguimiento apagado',checkin_paused:'Asistente en pausa'});
const box=document.createElement('section');box.className='checkins';box.setAttribute('aria-label',tr('checkins'));document.querySelector('.assistant-header').after(box);
let state=null,busy=false,flash='',started=false;
function render(){
 if(!state?.proactive)return;
 const data=state.proactive;
 const meta=!data.settings.enabled?tr('checkin_off'):data.quiet?tr('checkin_rest'):state.agentMode.mode!=='active'?tr('checkin_paused'):tr('checkin_next')+' '+new Date(data.nextPass).toLocaleTimeString(document.documentElement.lang||'en',{timeZone:state.timezone,hour:'2-digit',minute:'2-digit'});
 box.setAttribute('aria-label',tr('checkins'));
 box.innerHTML=`<div class="checkins-head"><h3>${esc(tr('checkins'))}</h3><button class="link-button" type="button" id="checkins-run" ${busy?'disabled':''}>${esc(tr(busy?'checking':'check_now'))}</button></div>`+
  `<p class="hint">${esc(meta)}</p>`+(flash?`<p class="hint" role="status">${esc(flash)}</p>`:'')+
  (data.checkins.length?data.checkins.map(c=>`<article class="checkin"><p data-anon-private="text">${esc(c.message)}</p><div class="checkin-actions">${c.answers.map(a=>`<button type="button" class="btn" data-checkin="${esc(c.id)}" data-answer="${esc(a)}" ${state.readOnly?'disabled':''}>${esc(tr('checkin_'+a))}</button>`).join('')}</div></article>`).join(''):`<p class="hint">${esc(tr('checkin_empty'))}</p>`);
}
async function tick(manual=false){
 if(busy||!state?.profile||state.readOnly)return;
 busy=true;if(manual){flash='';render()}
 try{const result=await api('/api/proactive',{op:manual?'run':'tick'});if(manual&&result.limited)flash=tr('checkin_limited');await flow.refresh()}
 catch(error){if(manual)throw error}
 finally{busy=false;render()}
}
box.addEventListener('click',e=>{
 if(e.target.closest('#checkins-run')){safely(()=>tick(true));return}
 const b=e.target.closest('[data-checkin]');if(!b)return;
 const card=state.proactive.checkins.find(c=>c.id===b.dataset.checkin),task=state.tasks.find(t=>t.id===card?.task);
 if(b.dataset.answer==='done'&&task?.blockReason&&!window.confirm(tr('block_done_confirm').replace('{reason}',task.blockReason)))return;
 b.disabled=true;safely(async()=>{try{await api('/api/proactive',{op:'answer',id:b.dataset.checkin,answer:b.dataset.answer,key:crypto.randomUUID()});await flow.refresh()}finally{b.disabled=false}})
});
function update(s){state=s;render();if(!started){started=true;void tick();setInterval(()=>void tick(),60000)}}
function settingsHtml(){return `<details class="daily-section"><summary>${esc(tr('proactive_title'))}</summary><label class="context-checkbox"><input type="checkbox" id="proactive-enabled">${esc(tr('proactive_enabled'))}</label><div class="daily-grid"><label class="field"><span>${esc(tr('proactive_every'))}</span><select id="proactive-every">${[30,60,120].map(n=>`<option value="${n}">${esc(tr('proactive_'+n))}</option>`).join('')}</select></label><label class="field"><span>${esc(tr('proactive_max'))}</span><input type="number" id="proactive-max" min="1" max="20"></label><label class="field"><span>${esc(tr('proactive_from'))}</span><input type="time" id="proactive-from"></label><label class="field"><span>${esc(tr('proactive_until'))}</span><input type="time" id="proactive-until"></label></div><fieldset class="proactive-kinds"><legend>${esc(tr('proactive_about'))}</legend>${['stale','important','due','risk'].map(k=>`<label class="context-checkbox"><input type="checkbox" data-proactive-kind="${k}">${esc(tr('proactive_'+k))}</label>`).join('')}</fieldset><p class="hint">${esc(tr('proactive_hint'))}</p></details>`}
function wireSettings(s){const cfg=s.proactive.settings;for(const [id,value] of [['proactive-enabled',cfg.enabled],['proactive-every',cfg.every],['proactive-max',cfg.maxPerDay],['proactive-from',cfg.quietStart],['proactive-until',cfg.quietEnd]]){if(id==='proactive-enabled')$(id).checked=value;else $(id).value=value}
 const save=values=>safely(async()=>{await api('/api/proactive',{op:'settings',values});await flow.refresh()});
 $('proactive-enabled').onchange=e=>save({enabled:e.target.checked});$('proactive-every').onchange=e=>save({every:Number(e.target.value)});$('proactive-max').onchange=e=>save({maxPerDay:Number(e.target.value)});$('proactive-from').onchange=e=>save({quietStart:e.target.value});$('proactive-until').onchange=e=>save({quietEnd:e.target.value});for(const el of document.querySelectorAll('[data-proactive-kind]')){el.checked=cfg.kinds[el.dataset.proactiveKind];el.onchange=()=>save({kinds:{[el.dataset.proactiveKind]:el.checked}})}
}
globalThis.dayProactive={update,settingsHtml,wireSettings};
})();
