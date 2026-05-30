// Progressive-enhancement tab switching. Server renders the first panel active;
// without JS every panel is still reachable (they're all in the DOM). Used by the
// coach profile (career / teams / endorsements) and, later, schedule and results.
(function () {
  "use strict";
  document.addEventListener("click", function (event) {
    var btn = event.target.closest("[data-tab]");
    if (!btn) return;
    var scope = btn.closest("[data-tabs]");
    if (!scope) return;
    var name = btn.getAttribute("data-tab");
    scope.querySelectorAll("[data-tab]").forEach(function (b) {
      b.classList.toggle("is-active", b === btn);
    });
    scope.querySelectorAll("[data-panel]").forEach(function (panel) {
      panel.classList.toggle("is-active", panel.getAttribute("data-panel") === name);
    });
  });
})();
