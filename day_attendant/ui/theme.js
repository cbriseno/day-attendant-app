(() => {
'use strict';
const root=document.documentElement,media=matchMedia('(prefers-color-scheme:dark)');
let mode='system',palette='grafito';
try{mode=localStorage.getItem('day-attendant-theme')||mode;palette=localStorage.getItem('day-attendant-palette')||palette}catch{}
if(!['system','light','dark'].includes(mode))mode='system';
if(!['grafito','papel','oceano'].includes(palette))palette='grafito';
const apply=()=>{root.dataset.theme=mode==='system'?(media.matches?'dark':'light'):mode;root.dataset.palette=palette;root.style.colorScheme=root.dataset.theme};
globalThis.dayTheme={get mode(){return mode},get palette(){return palette},set(nextMode,nextPalette){mode=nextMode;palette=nextPalette;try{localStorage.setItem('day-attendant-theme',mode);localStorage.setItem('day-attendant-palette',palette)}catch{}apply()}};
media.addEventListener('change',apply);apply();
})();
