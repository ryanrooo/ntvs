// Résumé editor (US3). Progressive enhancement: add/remove positions and request
// verification via the JSON API, mirroring the live preview + profile-strength meter.
// Strength formula mirrors view_models.compute_profile_strength.
(function () {
  "use strict";
  var root = document.querySelector(".editor-layout");
  if (!root) return;
  var coachKey = root.getAttribute("data-coach");
  var clubKey = root.getAttribute("data-club");
  var hasAbout = root.getAttribute("data-has-about") === "1";

  var list = document.getElementById("position-list");
  var timeline = document.getElementById("pv-timeline");
  var form = document.getElementById("position-form");
  var posMsg = document.getElementById("pos-msg");

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function recompute() {
    var count = list.querySelectorAll(".pos-card").length;
    var strength = Math.min(100, 40 + count * 14 + (hasAbout ? 10 : 0));
    document.getElementById("pv-count").textContent = String(count);
    document.getElementById("strength-pct").textContent = strength + "%";
    document.getElementById("strength-fill").style.width = strength + "%";
    document.getElementById("strength-note").textContent =
      strength < 100 ? "Add a photo & more positions to reach 100%" : "Looking great — ready to publish!";
  }

  function addCards(p) {
    var color = p.club_color || "#5bb8ff";

    var card = el("div", "pos-card");
    card.setAttribute("data-pos", p.position_id);
    card.style.borderLeftColor = color;
    var info = el("div", "pos-info");
    var club = el("div", "pos-club");
    club.appendChild(document.createTextNode(p.club_label + " "));
    club.appendChild(el("span", "chip chip-amber", "Pending"));
    info.appendChild(club);
    info.appendChild(el("div", "pos-role", p.role + (p.age_group ? " · " + p.age_group : "")));
    if (p.years) info.appendChild(el("div", "pos-years mono", p.years));
    card.appendChild(info);
    var rm = el("button", "pos-remove", "✕");
    rm.type = "button";
    rm.setAttribute("data-pos", p.position_id);
    rm.title = "Remove";
    card.appendChild(rm);
    list.appendChild(card);

    var item = el("div", "pv-item");
    item.setAttribute("data-pos", p.position_id);
    var dot = el("span", "pv-dot");
    dot.style.background = color;
    item.appendChild(dot);
    var body = el("div");
    body.appendChild(el("span", "pv-club", p.club_label));
    body.appendChild(document.createTextNode(" "));
    body.appendChild(el("span", "pv-pending", "● pending"));
    body.appendChild(el("div", "pv-role", p.role + (p.years ? " · " + p.years : "")));
    item.appendChild(body);
    timeline.appendChild(item);

    recompute();
  }

  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    posMsg.textContent = "";
    posMsg.className = "pos-form-msg";
    var fd = new FormData(form);
    var payload = {
      club_label: (fd.get("club_label") || "").trim(),
      role: (fd.get("role") || "").trim(),
      age_group: (fd.get("age_group") || "").trim(),
      years: (fd.get("years") || "").trim(),
      website: fd.get("website") || "",
    };
    if (!payload.club_label || !payload.role) {
      posMsg.textContent = "Club and role are required.";
      posMsg.className = "pos-form-msg is-bad";
      return;
    }
    fetch("/api/coaches/" + encodeURIComponent(coachKey) + "/positions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (b) { return { s: r.status, b: b }; }); })
      .then(function (r) {
        if (r.s === 201) {
          addCards(r.b);
          form.reset();
          posMsg.textContent = r.b.applied === false ? "Already on your résumé." : "Added to your résumé.";
          posMsg.className = "pos-form-msg is-good";
        } else {
          posMsg.textContent = (r.b && r.b.message) || "Could not add position.";
          posMsg.className = "pos-form-msg is-bad";
        }
      })
      .catch(function () { posMsg.textContent = "Network error."; posMsg.className = "pos-form-msg is-bad"; });
  });

  list.addEventListener("click", function (ev) {
    var btn = ev.target.closest(".pos-remove");
    if (!btn) return;
    var pid = btn.getAttribute("data-pos");
    fetch("/api/coaches/" + encodeURIComponent(coachKey) + "/positions/" + encodeURIComponent(pid), { method: "DELETE" })
      .then(function (r) {
        if (r.status === 204) {
          var c = list.querySelector('.pos-card[data-pos="' + pid + '"]');
          if (c) c.remove();
          var t = timeline.querySelector('.pv-item[data-pos="' + pid + '"]');
          if (t) t.remove();
          recompute();
        } else if (r.status === 409) {
          alert("Verified positions can't be removed.");
        }
      });
  });

  var verifyBtn = document.getElementById("verify-btn");
  var verifyMsg = document.getElementById("verify-msg");
  if (verifyBtn) {
    verifyBtn.addEventListener("click", function () {
      if (!clubKey) return;
      var pendingRemove = list.querySelector(".pos-card .pos-remove");
      var posId = pendingRemove ? parseInt(pendingRemove.getAttribute("data-pos"), 10) : null;
      verifyBtn.disabled = true;
      fetch("/api/coaches/" + encodeURIComponent(coachKey) + "/verification-requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ club_key: clubKey, position_id: posId }),
      })
        .then(function (r) { return r.json().then(function (b) { return { s: r.status, b: b }; }); })
        .then(function (r) {
          verifyBtn.disabled = false;
          if (r.s === 201) {
            verifyMsg.textContent = r.b.applied ? "Verification request sent to the club director." : "A request for this club is already pending.";
            verifyMsg.className = "verify-msg is-good";
          } else {
            verifyMsg.textContent = (r.b && r.b.message) || "Could not send request.";
            verifyMsg.className = "verify-msg is-bad";
          }
        })
        .catch(function () { verifyBtn.disabled = false; verifyMsg.textContent = "Network error."; verifyMsg.className = "verify-msg is-bad"; });
    });
  }
})();
