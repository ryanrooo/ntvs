// Director verification dashboard (US4). Approve/deny pending requests via the
// JSON API; on success the card leaves the queue and the counts update. The
// resolve endpoint is idempotent server-side, so double-clicks are harmless.
(function () {
  "use strict";
  var root = document.querySelector(".dir-layout");
  if (!root) return;
  var list = document.getElementById("request-list");

  function bump(id, delta) {
    var el = document.getElementById(id);
    if (el) el.textContent = String(Math.max(0, (parseInt(el.textContent, 10) || 0) + delta));
  }

  function resolve(rid, decision, card, btn) {
    if (btn) btn.disabled = true;
    fetch("/api/director/requests/" + encodeURIComponent(rid) + "/resolve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision: decision }),
    })
      .then(function (r) { return r.json().then(function (b) { return { s: r.status, b: b }; }); })
      .then(function (r) {
        if (r.s === 200) {
          if (card) card.remove();
          bump("st-pending", -1);
          var pend = document.getElementById("st-pending");
          var badge = document.getElementById("pending-badge");
          if (badge && pend) badge.textContent = pend.textContent + " awaiting review";
          if (decision === "approve") bump("st-verified", 1);
          if (!list.querySelector(".req-card")) {
            var empty = document.getElementById("dir-empty");
            if (empty) empty.style.display = "";
          }
        } else if (r.s === 403) {
          alert((r.b && r.b.message) || "A director token is required.");
          if (btn) btn.disabled = false;
        } else {
          if (btn) btn.disabled = false;
        }
      })
      .catch(function () { if (btn) btn.disabled = false; });
  }

  list.addEventListener("click", function (ev) {
    var approve = ev.target.closest(".req-approve");
    var deny = ev.target.closest(".req-deny");
    if (approve) resolve(approve.getAttribute("data-req"), "approve", approve.closest(".req-card"), approve);
    else if (deny) resolve(deny.getAttribute("data-req"), "deny", deny.closest(".req-card"), deny);
  });
})();
