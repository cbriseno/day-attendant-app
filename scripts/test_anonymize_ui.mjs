await page.wait('[data-task-id]');
console.log(JSON.stringify(await page.eval(async()=>{
 const assert=(ok,msg)=>{if(!ok)throw Error(msg)};
 const frame=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
 const tick=()=>new Promise(r=>setTimeout(r,0));
 await dayAnonymize.setActive(true);const localeReset=document.getElementById('locale-choice');localeReset.value='en';localeReset.dispatchEvent(new Event('change',{bubbles:true}));await tick();await dayAnonymize.ready;await dayAnonymize.setActive(false);
 document.getElementById('chat-close').click();await tick();
 const fixture=document.createElement('section');fixture.id='anon-fixture';fixture.style.cssText='width:min(600px,90vw);padding:12px';
 fixture.innerHTML=`<h2 data-copy>Settings</h2><p data-block>CANARY_PARAGRAPH_101 A reasonably long synthetic paragraph with different words and narrow iiiiii and wide WWWWWW.</p>
 <p data-block style="font-weight:700">CANARY_BOLD_102 another multiline fixture with several different words to wrap naturally.</p>
 <div data-block style="display:inline-flex;gap:8px">CANARY_FLEX_103 secret multiple words</div>
 <p data-mixed>Links of «CANARY_TEMPLATE_104»</p><p data-anon-safe="text" data-struct>60% · 3/5 · 2026-11-02 · 14:30</p>
 <p data-private-label data-anon-private="text">Settings</p><p data-short-private data-anon-private="text">i</p><p data-long-private data-anon-private="text">CANARY_UNUSUALLY_LONG_PRIVATE_IDENTIFIER_130</p><p data-free>123456789012345678901</p><div hidden>CANARY_HIDDEN_105</div><div role="menu">CANARY_MENU_106</div>
 <dialog open><p>CANARY_DIALOG_107</p></dialog><svg width="100%" viewBox="0 0 400 30" height="30"><text x="0" y="20">CANARY_SVG_108</text></svg>
 <input value="CANARY_INPUT_109" title="CANARY_TITLE_110" aria-label="CANARY_ARIA_111" placeholder="CANARY_PLACEHOLDER_112">
 <textarea>CANARY_TEXTAREA_113</textarea><select><option value="CANARY_OPTION_VALUE_114">CANARY_OPTION_115</option></select>
 <input type="datetime-local" value="CANARY_INVALID_DATE_129"><input type="datetime-local" data-date value="2026-11-02T14:30"><img alt="CANARY_ALT_116"><p data-error>CANARY_ERROR_117 /CANARY_PATH_118/file.log</p><p>CANARY_ATTACHMENT_119.png</p>
 <div data-conversation>CANARY_CONVERSATION_120</div><p data-data-date>2026-12-24</p>`;
 document.body.append(fixture);const shadowHost=document.createElement('div');fixture.append(shadowHost);shadowHost.attachShadow({mode:'open'}).innerHTML='<span>CANARY_SHADOW_121</span>';
 const surfaces=container=>{let s='';const walker=document.createTreeWalker(container,NodeFilter.SHOW_ELEMENT|NodeFilter.SHOW_TEXT);while(walker.nextNode()){const n=walker.currentNode;if(n.nodeType===3){if(!n.parentElement?.closest('script,style'))s+=n.data+'\n'}else{for(const a of ['title','aria-label','alt','placeholder','value'])s+=(n.getAttribute(a)||'')+'\n';if('value'in n)s+=n.value+'\n';if(n.shadowRoot)s+=surfaces(n.shadowRoot)}}return s};
 const geometry=()=>[...document.querySelectorAll('[data-block],#anon-fixture input,#anon-fixture textarea,#anon-fixture select,.task,.page-heading,.appbar')].filter(e=>{const r=e.getBoundingClientRect();return e.getClientRects().length&&r.bottom>0&&r.top<innerHeight}).map(e=>{const r=e.getBoundingClientRect();const lines=new Set(),walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT);while(walker.nextNode()){const range=document.createRange();range.selectNodeContents(walker.currentNode);for(const rect of range.getClientRects())if(rect.width)lines.add(Math.round(rect.y))}return {x:r.x,y:r.y,w:r.width,h:r.height,lines:lines.size}});
 const beforeText=surfaces(fixture),title=document.title;let sampling=true,changed=true;const leaks=[];const sampler=new MutationObserver(()=>{changed=true});sampler.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true});const sample=()=>{if(!sampling)return;if(changed&&dayAnonymize.active&&getComputedStyle(document.body).visibility!=='hidden'){const exposed=surfaces(document.body).split('\n').filter(s=>s.includes('CANARY_'));if(exposed.length)leaks.push(exposed);changed=false}requestAnimationFrame(sample)};requestAnimationFrame(sample);
 const structures=[...document.querySelectorAll('.task-created,.task-due,.task-number,.lane-count,#closed-count,#task-count,.date')].map(e=>({e,text:e.textContent}));
 assert(!dayAnonymize.active,'Default off');
 const input=fixture.querySelector('input');input.focus();await dayAnonymize.setActive(true);await tick();await frame();
 assert(document.activeElement===input&&input.readOnly,'Readonly retains focus');
 assert(!surfaces(document.body).includes('CANARY_'),'All DOM surfaces scrubbed');
 const selectControl=fixture.querySelector('select');await dayAnonymize.setActive(false);assert(input.value==='CANARY_INPUT_109'&&selectControl.value==='CANARY_OPTION_VALUE_114','Initial values exactly restored');await dayAnonymize.setActive(true);
 assert(!fixture.querySelector('[data-free]').textContent.includes('123456789012345678901'),'Free numbers masked');
 assert(!fixture.querySelector('[data-data-date]').textContent.includes('2026-12-24'),'Free numeric dates masked by origin');
 assert(fixture.querySelector('[data-copy]').textContent==='Settings','Catalog copy retained');assert(fixture.querySelector('[data-private-label]').textContent!=='Settings','Data equal to a UI label is still private');assert(fixture.querySelector('[data-short-private]').textContent!=='i','Short private value masked');const neutral=fixture.querySelector('[data-long-private]').textContent.trim().split(/\s+/);assert(neutral.every((word,i)=>i===0||word!==neutral[i-1]),'No repeated adjacent replacement words');
 assert(fixture.querySelector('[data-mixed]').textContent.startsWith('Links of «')&&!fixture.querySelector('[data-mixed]').textContent.includes('CANARY'),'Template fixed part only');
 assert(fixture.querySelector('[data-struct]').textContent==='60% · 3/5 · 2026-11-02 · 14:30','Typed structure retained');
 assert(document.title===title,'Tab unchanged');assert(fixture.querySelector('[data-date]').value==='2026-11-02T14:30','Native typed date retained');assert(structures.every(({e,text})=>e.isConnected?e.textContent===text:true),'Real typed fields unchanged');
 const late=document.createElement('p');late.textContent='CANARY_LATE_122';fixture.append(late);await tick();assert(!surfaces(document.body).includes('CANARY_'),'Late content before paint');
 input.value='CANARY_PROPERTY_123';fixture.querySelector('textarea').value='CANARY_PROPERTY_124';await tick();assert(!surfaces(document.body).includes('CANARY_'),'Value setter updates');
 const text=document.createTextNode('Settings');late.replaceChildren(text);await tick();text.data='CANARY_CHARACTER_126';await tick();assert(!surfaces(document.body).includes('CANARY_'),'Character data updates');
 const queuedOne=document.createElement('p');queuedOne.textContent='CANARY_MICROTASK_127';fixture.append(queuedOne);queueMicrotask(()=>{const queuedTwo=document.createElement('p');queuedTwo.textContent='CANARY_MICROTASK_128';fixture.append(queuedTwo)});await tick();await dayAnonymize.ready;assert(!surfaces(document.body).includes('CANARY_'),'Queued mutation records drained before disconnect');
 const revision=daySnapshot().revision;document.getElementById('send-message').click();fixture.querySelector('input').dispatchEvent(new Event('input',{bubbles:true}));fixture.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}));await tick();assert(daySnapshot().revision===revision,'No writes');
 await dayAnonymize.setActive(false);await tick();assert(input.value==='CANARY_PROPERTY_123'&&!input.readOnly,'Latest real value restored');assert(surfaces(fixture).includes('CANARY_TITLE_110')&&surfaces(fixture).includes('CANARY_SHADOW_121'),'Original text, attributes and shadow restored');
 await dayAnonymize.setActive(true);
 const safeView=async label=>{await tick();await dayAnonymize.ready;await frame();await dayAnonymize.ready;assert(!surfaces(document.body).includes('CANARY_'),'App view '+label+' '+surfaces(document.body).split('\n').filter(s=>s.includes('CANARY_')).join('|'))};
 document.querySelector('.task-title').click();await safeView('expanded source and continuity');
 document.getElementById('settings-open').click();await safeView('settings values');
 document.getElementById('diagnostics-open').click();await safeView('diagnostics');
 for(const d of document.querySelectorAll('dialog[open]'))d.close();
 document.querySelector('#calendar-area .link-button').click();await safeView('event capture');
 document.getElementById('capture-title').value='CANARY_CAPTURE_204';await safeView('capture late value');
 for(const d of document.querySelectorAll('dialog[open]'))d.close();
 document.querySelector('[data-action=more]').click();await safeView('menu');document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}));
 for(const id of ['board-view','focus-view','list-view']){document.getElementById(id).click();await safeView(id)}
 const order=document.getElementById('order-choice');order.value='group';order.dispatchEvent(new Event('change',{bubbles:true}));await safeView('group progress');order.value='priority';order.dispatchEvent(new Event('change',{bubbles:true}));await safeView('priority');
 await dayAnonymize.setActive(false);
 const layouts=[];
 for(const font of ['Arial, sans-serif','Georgia, serif']){fixture.style.fontFamily=font;document.body.style.fontFamily=font;await document.fonts.ready;for(const a of document.getAnimations())a.finish();await frame();const a=geometry();await dayAnonymize.setActive(true);await dayAnonymize.ready;for(const a of document.getAnimations())a.finish();await frame();const b=geometry();assert(a.length===b.length,'Same block count');assert(a.every((r,i)=>r.lines===b[i].lines),'Same line count '+JSON.stringify({a,b}));const errors=a.map((r,i)=>Math.max(...['x','y','w','h'].map(k=>Math.abs(r[k]-b[i][k])/Math.max(1,r[k==='x'?'w':k==='y'?'h':k]))));const max=Math.max(...errors);assert(max<=.02,'Layout '+font+' '+JSON.stringify({a,b,max}));layouts.push({font,maxRelativeError:max});await dayAnonymize.setActive(false);await tick()}
 document.body.style.fontFamily='';const perf=[];
 for(const rows of [500,2000]){const list=document.createElement('section');list.style.width='600px';list.innerHTML=Array.from({length:rows},(_,i)=>'<p>CANARY_ROW_'+i+' synthetic private words</p>').join('');document.body.append(list);await frame();const start=performance.now();await dayAnonymize.setActive(true);list.getBoundingClientRect();const ms=performance.now()-start;assert(!surfaces(list).includes('CANARY_'),'Performance fixture canaries');perf.push({rows,ms,...dayAnonymize.timing});if(rows===500)assert(dayAnonymize.timing.maxBatchMs<=200,"500-row perceived pause above 200 ms "+JSON.stringify(perf));await dayAnonymize.setActive(false);list.remove();await tick()}
 // Locale changes regenerate both known copy and neutral replacements.
 const locale=document.getElementById('locale-choice');locale.value='es';await dayAnonymize.setActive(true);locale.dispatchEvent(new Event('change',{bubbles:true}));await tick();await dayAnonymize.ready;await frame();await dayAnonymize.ready;assert(document.getElementById('anonymize-toggle').textContent==='Anonimizar','Spanish switch retained');assert(!surfaces(document.body).includes('CANARY_'),'Locale rerender safe');await dayAnonymize.setActive(false);sampling=false;sampler.disconnect();assert(leaks.length===0,'No visible-frame canaries '+JSON.stringify(leaks));fixture.remove();
 return {canaries:true,visibleFrameLeaks:leaks.length,restoration:true,readOnly:true,layouts,perf,session:sessionStorage.getItem('day-attendant-anonymize')};
})));
