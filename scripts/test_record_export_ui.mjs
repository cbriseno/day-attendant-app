await page.wait('[data-key="record:assistant"] [data-record-export]');
await page.click('[data-key="record:assistant"] [data-record-export]');
console.log(JSON.stringify(await page.eval(async()=>{
 const $=id=>document.getElementById(id),checks=[];
 const assert=(ok,name)=>{if(!ok)throw Error(name);checks.push(name)};
 let form=$('record-export-dialog').querySelector('form'),save=form.querySelector('[type=submit]');
 const tick=()=>new Promise(r=>setTimeout(r,0));
 const submit=async()=>{form.requestSubmit();await tick();for(let i=0;save.disabled&&i<200;i++)await new Promise(r=>setTimeout(r,10))};
 assert($('record-export-content').value==='# Registro 🚀\n\nCafé, español y 日本語.\n\nOmitir esta línea.','only selected original Markdown');
 assert(!$('record-export-content').value.includes('PRIVATE'),'no unselected history or task state');
 const content='# Sólo café 🚀\n\n日本語: 確認済み\n';
 $('record-export-content').value=content;
 for(const name of ['../escape.md','bad\\file.md','report.txt']){
  $('record-export-name').value=name;await submit();assert(!$('record-export-error').hidden,'invalid filename rejected: '+name);
 }
 $('record-export-name').value='registro-café-🚀.md';
 $('record-export-content').value='   ';await submit();assert(!$('record-export-error').hidden,'empty content rejected');
 $('record-export-content').value=content;
 let written,closed=false,suggested;
 window.showSaveFilePicker=async options=>{suggested=options.suggestedName;return {createWritable:async()=>({write:async blob=>{written=await blob.text()},close:async()=>{closed=true},abort:async()=>{}})}};
 await submit();
 assert(closed&&written===content&&suggested==='registro-café-🚀.md','picker writes exact edited Unicode content and filename');
 assert($('record-export-status').textContent==='File saved.','success only after stream close');
 $('record-export-dialog').close();
 document.querySelector('[data-key="support:assistant"] [data-record-export]').click();
 form=$('record-export-dialog').querySelector('form');save=form.querySelector('[type=submit]');
 const report=$('record-export-content').value;
 for(const section of ['# Solicitud: sincronización','Clasificación: carencia','## Contexto','## Flujo deseado','## Resultado actual','## Resultado esperado','## Datos pendientes'])assert(report.includes(section),'support report contains '+section);
 assert(!report.includes('PRIVATE')&&!report.includes('Café'),'support report excludes other messages and task state');
 $('record-export-name').value='solicitud.md';written=undefined;closed=false;
 await submit();assert(closed&&written===report&&suggested==='solicitud.md','support report downloads exact selected Markdown');
 $('record-export-dialog').close();
 document.querySelector('[data-key="record:assistant"] [data-record-export]').click();
 form=$('record-export-dialog').querySelector('form');save=form.querySelector('[type=submit]');
 $('record-export-content').value=content;
 $('record-export-name').value='registro-café-🚀.md';
 for(const stage of ['picker','write','close']){
  window.showSaveFilePicker=async()=>{if(stage==='picker')throw Error('Controlled error');return {createWritable:async()=>({write:async()=>{if(stage==='write')throw Error('Controlled error')},close:async()=>{throw Error('Controlled error')},abort:async()=>{}})}};
  await submit();assert(!$('record-export-error').hidden&&!$('record-export-status').textContent,'failure shown without success: '+stage);
  assert($('record-export-content').value===content&&!save.disabled,'draft retained and retry enabled: '+stage);
 }
 window.showSaveFilePicker=async()=>{throw new DOMException('Canceled','AbortError')};
 await submit();assert($('record-export-error').hidden&&$('record-export-status').textContent.includes('canceled'),'cancellation never reports saved');
 window.showSaveFilePicker=undefined;
 const create=URL.createObjectURL;URL.createObjectURL=()=>{throw Error('Controlled Blob failure')};
 await submit();assert(!$('record-export-error').hidden&&!$('record-export-status').textContent,'fallback failure shown without success');URL.createObjectURL=create;
 const locale=$('locale-choice');locale.value='es';locale.dispatchEvent(new Event('change',{bubbles:true}));await tick();
 $('record-export-dialog').close();document.querySelector('[data-key="record:assistant"] [data-record-export]').click();
 assert($('record-export-title').textContent==='Descargar registro','Spanish controls');
 $('record-export-content').value=content;
 $('record-export-name').value='registro-café-🚀.md';
 return checks;
})));
