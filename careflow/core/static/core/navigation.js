(() => {
  "use strict";
  // Only decorate existing links. Never create routes or infer permissions.
  const update = () => {
    document.querySelectorAll('nav[aria-label]').forEach(nav => {
      const links = [...nav.querySelectorAll("a[href]")];
      links.forEach(link => link.removeAttribute("aria-current"));
      const current = links.find(link => {
        const url = new URL(link.href);
        return url.origin === location.origin && url.pathname === location.pathname &&
          url.hash === location.hash;
      });
      if (current) current.setAttribute("aria-current", "page");
    });
  };
  update();
  window.addEventListener("hashchange", update);
  window.addEventListener("pageshow", update);
})();
