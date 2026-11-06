/* A document starts from one human-selected reply, never a profile snapshot. */
(() => {
'use strict';
const ui=globalThis.dayUI,{tr,esc}=ui,$=id=>document.getElementById(id);
function openRecord(message,origin){
 if(globalThis.dayAnonymize?.active)return;
 $('record-export-dialog')?.remove();
 const d=document.createElement('dialog');d.id='record-export-dialog';d.setAttribute('aria-labelledby','record-export-title');
 d.innerHTML=`<form class="modal-form"><header class="modal-header"><h2 id="record-export-title">${esc(tr('record_export'))}</h2><button type="button" class="btn icon ghost" data-close aria-label="${esc(tr('close'))}">${ui.icons.close}</button></header><div class="modal-body"><p class="hint">${esc(tr('record_scope'))}</p><label class="field"><span>${esc(tr('record_filename'))}</span><input id="record-export-name" maxlength="120" required></label><label class="field"><span>${esc(tr('record_content'))}</span><textarea class="draft-box" id="record-export-content" required></textarea></label><p class="error" id="record-export-error" role="alert" hidden></p><p class="hint" id="record-export-status" role="status"></p></div><footer class="modal-footer"><button type="button" class="btn" data-close>${esc(tr('close'))}</button><button type="submit" class="btn primary">${esc(tr('record_download'))}</button></footer></form>`;
 document.body.append(d);ui.registerDialog(d);
 $('record-export-name').value='record.md';$('record-export-content').value=message.text;
 for(const b of d.querySelectorAll('[data-close]'))b.onclick=()=>d.close();
 d.querySelector('form').onsubmit=async e=>{
  e.preventDefault();if(globalThis.dayAnonymize?.active)return;
  const error=$('record-export-error'),status=$('record-export-status'),save=d.querySelector('[type=submit]');error.hidden=true;status.textContent='';
  const name=$('record-export-name').value.trim(),text=$('record-export-content').value;
  if(!name.endsWith('.md')||name.length<=3||name.length>120||/[\x00-\x1f\x7f/\\]/.test(name)){error.textContent=tr('record_name_error');error.hidden=false;return}
  if(!text.trim()){error.textContent=tr('record_empty');error.hidden=false;return}
  save.disabled=true;
  try{
   const blob=new Blob([text],{type:'text/markdown;charset=utf-8'});
   if(typeof globalThis.showSaveFilePicker==='function'){
    const file=await showSaveFilePicker({suggestedName:name,types:[{description:'Markdown',accept:{'text/markdown':['.md']}}]});
    const stream=await file.createWritable();
    try{await stream.write(blob);await stream.close()}catch(e){try{await stream.abort()}catch{}throw e}
    status.textContent=tr('record_saved');
   }else{
    const url=URL.createObjectURL(blob),a=document.createElement('a');
    try{a.href=url;a.download=name;d.append(a);a.click();status.textContent=tr('record_requested')}
    finally{a.remove();setTimeout(()=>URL.revokeObjectURL(url),60000)}
   }
  }catch(e){if(e.name==='AbortError')status.textContent=tr('record_cancelled');else{error.textContent=tr('record_failed');error.hidden=false}}
  finally{save.disabled=false}
 };
 ui.openDialog(d,origin);$('record-export-name').focus();
}
function update(state){
 for(const el of $('messages').children){
  const message=state.messages.find(m=>m.key===el.dataset.key);
  if(message?.role!=='assistant'||message.status!=='completed')continue;
  let b=el.querySelector('[data-record-export]');
  if(!b){b=document.createElement('button');b.type='button';b.className='link-button';b.dataset.recordExport='';b.setAttribute('aria-haspopup','dialog');b.onclick=()=>openRecord(message,b);el.append(b)}
  b.textContent=tr('record_export');b.disabled=!!globalThis.dayAnonymize?.active;
 }
}
globalThis.dayRecordExport={update};
})();
