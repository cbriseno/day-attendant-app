// Runs in the head, before body parsing, under the existing self-only script CSP.
try {
 if(sessionStorage.getItem("day-attendant-anonymize")==="1")document.documentElement.setAttribute("data-anon-loading","");
} catch {}
