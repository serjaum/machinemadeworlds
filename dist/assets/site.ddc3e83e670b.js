/* Reading enhancements only. Articles and navigation never depend on JS. */
(() => {
  "use strict";
  const root = document.documentElement;
  const toggle = document.querySelector("[data-theme-toggle]");
  function syncTheme() {
    const dark = root.dataset.theme === "dark";
    toggle.setAttribute("aria-pressed", String(dark));
    toggle.setAttribute("aria-label", `Switch to ${dark ? "light" : "dark"} theme`);
    toggle.querySelector("[data-theme-label]").textContent = dark ? "Light" : "Dark";
    document.querySelector('meta[name="theme-color"]').content = dark ? "#171d1a" : "#f7f8f4";
  }
  syncTheme();
  toggle.hidden = false;
  toggle.addEventListener("click", () => {
    root.dataset.theme = root.dataset.theme === "dark" ? "light" : "dark";
    try { localStorage.setItem("mmw-theme", root.dataset.theme); } catch (_) { /* Private browsing still toggles. */ }
    syncTheme();
  });

  const search = document.querySelector("[data-search]");
  if (search) {
    const items = Array.from(document.querySelectorAll("[data-search-item]"));
    const searchable = items.map(item => item.textContent.toLocaleLowerCase());
    const empty = document.querySelector("[data-empty]");
    const status = document.querySelector("[data-search-status]");
    function filter() {
      const query = search.value.trim().toLocaleLowerCase();
      let count = 0;
      items.forEach((item, index) => {
        item.hidden = !searchable[index].includes(query);
        if (!item.hidden) count++;
      });
      document.querySelector("[data-result-count]").textContent = String(count);
      empty.hidden = count !== 0;
      status.textContent = `${count} articles found${query ? ` for “${search.value.trim()}”` : ""}.`;
    }
    document.querySelector("[data-search-control]").hidden = false;
    search.addEventListener("input", filter);
    document.querySelector("[data-clear-search]").addEventListener("click", () => {
      search.value = "";
      filter();
      search.focus();
    });
  }

  /* Global search (MAC-349): header GETs /search/?q=; page lazy-loads index once. */
  let gIdx=null,gP=null;
  const gLow=s=>String(s||"").toLocaleLowerCase();
  function gLoad(){if(gIdx)return Promise.resolve(gIdx);if(!gP)gP=fetch("/search-index.json",{credentials:"same-origin"}).then(r=>{if(!r.ok)throw 0;return r.json()}).then(d=>(gIdx=Array.isArray(d)?d:[])).catch(()=>{gIdx=[]});return gP}
  function gRank(s){const t=gLow(s).split(/\s+/).filter(Boolean).slice(0,8);if(!t.length||!gIdx)return[];const o=[];for(const d of gIdx){const T=gLow(d.title),D=gLow(d.description),C=gLow(d.topic_name||d.topic),B=gLow(d.body);let c=0,k=1;for(const w of t){let h=0;if(T.includes(w))h+=10;if(D.includes(w))h+=5;if(C.includes(w))h+=3;if(B.includes(w))h++;if(!h){k=0;break}c+=h}if(k)o.push([c,String(d.date||""),d])}o.sort((a,b)=>b[0]-a[0]||(b[1]<a[1]?-1:b[1]>a[1]?1:0));return o.slice(0,30).map(x=>x[2])}
  function gCard(d){const a=document.createElement("article");a.className="story";a.setAttribute("data-search-item","");const m=document.createElement("div");m.className="story-meta";const t=document.createElement("a");t.className="topic-label";t.href="/topics/"+d.topic+"/";t.textContent=d.topic_name||d.topic;m.appendChild(t);a.appendChild(m);const h=document.createElement("h3"),l=document.createElement("a");l.href=d.url;l.textContent=d.title;h.appendChild(l);a.appendChild(h);const e=document.createElement("p");e.textContent=d.description||"";a.appendChild(e);return a}
  const gInputs=Array.from(document.querySelectorAll("[data-global-search]")),gPage=document.querySelector("[data-search-page]"),gList=document.querySelector("[data-global-results]"),gIsSearch=location.pathname==="/search/"||location.pathname==="/search";
  if(gIsSearch&&gList){
    const gCount=document.querySelector("[data-result-count]"),gEmpty=document.querySelector("[data-empty]"),gStatus=document.querySelector("[data-search-status]"),gCtl=document.querySelector("[data-search-control]"),gClear=document.querySelector("[data-clear-search]");
    if(gCtl)gCtl.hidden=false;
    const gQ=(new URLSearchParams(location.search).get("q")||"").slice(0,120);
    if(gPage)gPage.value=gQ;
    gInputs.forEach(n=>{if(!n.value)n.value=gQ});
    let gT=0;
    function gCur(){return((gPage&&document.activeElement===gPage)?gPage.value:(gInputs[0]&&gInputs[0].value)||(gPage&&gPage.value)||gQ)}
    function gRender(){const s=gCur().trim().slice(0,120);if(!s){gList.replaceChildren();if(gCount)gCount.textContent="0";if(gEmpty)gEmpty.hidden=true;if(gStatus)gStatus.textContent="Type to search the full journal.";return}gLoad().then(()=>{const h=gRank(s);gList.replaceChildren(...h.map(gCard));if(gCount)gCount.textContent=String(h.length);if(gEmpty)gEmpty.hidden=h.length!==0;if(gStatus)gStatus.textContent=h.length?h.length+" articles found for \u201c"+s+"\u201d.":"No articles found for \u201c"+s+"\u201d. Try a different word."})}
    function gSched(){clearTimeout(gT);gT=setTimeout(()=>{const s=(gPage?gPage.value:"").trim().slice(0,120);gInputs.forEach(n=>{if(n!==document.activeElement)n.value=s});history.replaceState(null,"",s?"/search/?q="+encodeURIComponent(s):"/search/");gRender()},120)}
    function gWipe(f){if(gPage)gPage.value="";gInputs.forEach(n=>{n.value=""});history.replaceState(null,"","/search/");gRender();(f||gPage||gInputs[0]).focus()}
    if(gPage){gPage.addEventListener("input",gSched);gPage.addEventListener("keydown",e=>{if(e.key==="Escape"){e.preventDefault();gWipe(gPage)}})}
    gInputs.forEach(n=>{n.addEventListener("focus",gLoad);n.addEventListener("input",()=>{if(gPage&&n!==gPage){gPage.value=n.value;gSched()}});n.addEventListener("keydown",e=>{if(e.key==="Escape"){e.preventDefault();gWipe(n)}})});
    if(gClear)gClear.addEventListener("click",()=>gWipe());
    document.addEventListener("keydown",e=>{if(e.key==="Escape"&&!e.metaKey&&!e.ctrlKey&&!e.altKey){e.preventDefault();gWipe()}});
    if(gQ)gLoad().then(gRender);else gRender();
  }else{
    gInputs.forEach(n=>{n.addEventListener("focus",gLoad,{once:true});n.addEventListener("keydown",e=>{if(e.key==="Escape"){e.preventDefault();n.value=""}})});
  }
  document.addEventListener("keydown",e=>{if(e.key!=="/"||e.metaKey||e.ctrlKey||e.altKey)return;const t=e.target;if(t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.tagName==="SELECT"||t.isContentEditable))return;const f=document.querySelector("[data-global-search]");if(f){e.preventDefault();f.focus()}});
  document.querySelectorAll(".topic-tabs a").forEach(link => {
    if (link.pathname === location.pathname) link.setAttribute("aria-current", "page");
  });
})();
