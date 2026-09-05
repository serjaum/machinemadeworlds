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
  document.querySelectorAll(".topic-tabs a").forEach(link => {
    if (link.pathname === location.pathname) link.setAttribute("aria-current", "page");
  });
})();
