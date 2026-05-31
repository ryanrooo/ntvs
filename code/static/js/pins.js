// Club pin set (US5). Stored in the `ntvs_pins` cookie (≤4 club_keys) so the
// server can read it to render pin state and drive /compare. Shared across the
// clubs directory, club profiles, and the comparison page.
(function () {
  "use strict";
  var MAX = 4;

  function get() {
    var m = document.cookie.match(/(?:^|; )ntvs_pins=([^;]*)/);
    return m ? decodeURIComponent(m[1]).split(",").filter(Boolean) : [];
  }
  function save(arr) {
    document.cookie = "ntvs_pins=" + encodeURIComponent(arr.slice(0, MAX).join(",")) + "; path=/; max-age=2592000; samesite=lax";
  }
  function has(key) { return get().indexOf(key) >= 0; }
  function add(key) {
    var a = get();
    if (a.indexOf(key) >= 0) return true;
    if (a.length >= MAX) return false;
    a.push(key); save(a); return true;
  }
  function remove(key) { save(get().filter(function (k) { return k !== key; })); }
  function toggle(key) {
    if (has(key)) { remove(key); return { ok: true, pinned: false }; }
    return add(key) ? { ok: true, pinned: true } : { ok: false, reason: "max" };
  }

  function syncBtn(btn) {
    var on = has(btn.getAttribute("data-pin"));
    btn.classList.toggle("is-pinned", on);
    btn.textContent = on ? "✓ Pinned" : "+ Pin";
  }
  function updateCount() {
    var n = get().length;
    document.querySelectorAll("[data-pin-count]").forEach(function (el) { el.textContent = String(n); });
  }

  document.addEventListener("DOMContentLoaded", function () {
    // Toggle buttons on directory / profile.
    document.querySelectorAll("[data-pin]").forEach(function (btn) {
      syncBtn(btn);
      btn.addEventListener("click", function (ev) {
        ev.preventDefault();
        var res = toggle(btn.getAttribute("data-pin"));
        if (!res.ok && res.reason === "max") { alert("You can pin up to 4 clubs."); return; }
        syncBtn(btn);
        updateCount();
      });
    });
    updateCount();

    // Compare page: remove / add / reset (reload so the server re-renders the set).
    document.querySelectorAll("[data-unpin]").forEach(function (btn) {
      btn.addEventListener("click", function () { remove(btn.getAttribute("data-unpin")); location.reload(); });
    });
    var adder = document.querySelector("[data-add-club]");
    if (adder) adder.addEventListener("change", function () {
      var v = adder.value;
      if (!v) return;
      if (!add(v)) { alert("You can pin up to 4 clubs."); adder.value = ""; return; }
      location.reload();
    });
    var reset = document.querySelector("[data-reset-pins]");
    if (reset) reset.addEventListener("click", function () { save([]); location.reload(); });
  });
})();
