// Endorsement composer (US2). Progressive enhancement over the server-rendered
// coach profile: the page reads fine without JS; this adds the interactive
// composer. The negative-tone regex is mirrored from endorsement_policy.py — keep
// the two in sync. The server re-validates everything regardless of this check.
(function () {
  "use strict";
  var form = document.getElementById("endorse-form");
  if (!form) return;

  var NEGATIVE = /\b(bad|awful|terrible|hate|worst|rude|unfair)\b/i;
  var STAR_LABELS = { 4: "Great", 5: "Outstanding" };

  var fStars = document.getElementById("f-stars");
  var fRel = document.getElementById("f-rel");
  var fAuthor = document.getElementById("f-author");
  var fBody = document.getElementById("f-body");
  var starLabel = document.getElementById("star-label");
  var charNow = document.getElementById("char-now");
  var toneInd = document.getElementById("tone-ind");
  var msg = document.getElementById("composer-msg");
  var submitBtn = document.getElementById("composer-submit");
  var coachKey = form.getAttribute("data-coach");

  // ── star picker (only 4 and 5 are selectable) ──
  var stars = Array.prototype.slice.call(form.querySelectorAll(".star"));
  function paintStars(val) {
    stars.forEach(function (s) {
      s.classList.toggle("is-on", parseInt(s.getAttribute("data-val"), 10) <= val);
    });
  }
  stars.forEach(function (s) {
    if (s.disabled) return;
    s.addEventListener("click", function () {
      var val = parseInt(s.getAttribute("data-val"), 10);
      fStars.value = String(val);
      paintStars(val);
      starLabel.textContent = STAR_LABELS[val] || "";
      validate();
    });
  });

  // ── single-select relationship pills ──
  form.querySelectorAll("#rel-row .pill").forEach(function (p) {
    p.addEventListener("click", function () {
      form.querySelectorAll("#rel-row .pill").forEach(function (o) { o.classList.remove("is-on"); });
      p.classList.add("is-on");
      fRel.value = p.getAttribute("data-rel");
      validate();
    });
  });

  // ── multi-select strength tags ──
  form.querySelectorAll("#tag-row .pill").forEach(function (p) {
    p.addEventListener("click", function () { p.classList.toggle("is-on"); });
  });
  function selectedTags() {
    return Array.prototype.map.call(
      form.querySelectorAll("#tag-row .pill.is-on"),
      function (p) { return p.getAttribute("data-tag"); }
    );
  }

  // ── body: char counter + live tone gate ──
  function updateBody() {
    var text = fBody.value;
    charNow.textContent = String(text.length);
    if (!text.trim()) {
      toneInd.textContent = "";
      toneInd.className = "tone-ind";
    } else if (NEGATIVE.test(text)) {
      toneInd.textContent = "⚠ Let's keep it positive";
      toneInd.className = "tone-ind is-bad";
    } else {
      toneInd.textContent = "✓ Positive tone detected";
      toneInd.className = "tone-ind is-good";
    }
    validate();
  }
  fBody.addEventListener("input", updateBody);

  function isValid() {
    return (
      (fStars.value === "4" || fStars.value === "5") &&
      !!fRel.value &&
      fBody.value.trim().length > 0 &&
      fBody.value.length <= 500 &&
      !NEGATIVE.test(fBody.value)
    );
  }
  function validate() {
    submitBtn.disabled = !isValid();
  }
  validate();

  // ── submit via fetch; prepend the new card on success ──
  form.addEventListener("submit", function (ev) {
    ev.preventDefault();
    if (!isValid()) return;
    submitBtn.disabled = true;
    msg.textContent = "";
    msg.className = "composer-msg";

    var payload = {
      author_label: fAuthor.value.trim(),
      relationship: fRel.value,
      stars: parseInt(fStars.value, 10),
      tags: selectedTags(),
      body: fBody.value.trim(),
      website: form.querySelector('input[name="website"]').value, // honeypot
    };

    fetch("/api/coaches/" + encodeURIComponent(coachKey) + "/endorsements", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (res) { return res.json().then(function (b) { return { status: res.status, body: b }; }); })
      .then(function (r) {
        if (r.status === 201) {
          prependEndorsement(r.body);
          msg.textContent = "Thanks — your endorsement is posted.";
          msg.className = "composer-msg is-good";
          resetForm();
        } else {
          msg.textContent = (r.body && r.body.message) || "Could not post — please try again.";
          msg.className = "composer-msg is-bad";
          submitBtn.disabled = false;
        }
      })
      .catch(function () {
        msg.textContent = "Network error — please try again.";
        msg.className = "composer-msg is-bad";
        submitBtn.disabled = false;
      });
  });

  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }

  function prependEndorsement(e) {
    var list = document.getElementById("endorse-list");
    var empty = document.getElementById("endorse-empty");
    if (empty) empty.style.display = "none";

    var li = el("li", "endorse-item");
    var head = el("div", "endorse-head");
    head.appendChild(el("span", "endorse-avatar", (e.author_label || "?").charAt(0).toUpperCase()));
    var who = el("div", "endorse-who");
    who.appendChild(el("strong", null, e.author_label));
    who.appendChild(el("span", "endorse-rel", e.relationship));
    head.appendChild(who);
    head.appendChild(el("span", "endorse-stars", "★".repeat(e.stars)));
    head.appendChild(el("span", "endorse-date", e.date || ""));
    li.appendChild(head);
    li.appendChild(el("p", "endorse-body", e.body));
    if (e.tags && e.tags.length) {
      var row = el("div", "endorse-chiprow");
      e.tags.forEach(function (t) { row.appendChild(el("span", "chip", t)); });
      li.appendChild(row);
    }
    list.insertBefore(li, list.firstChild);

    var count = document.getElementById("endorse-count");
    if (count) count.textContent = String((parseInt(count.textContent, 10) || 0) + 1);
  }

  function resetForm() {
    fStars.value = "";
    fRel.value = "";
    fAuthor.value = "";
    fBody.value = "";
    paintStars(0);
    starLabel.textContent = "Pick 4 or 5";
    form.querySelectorAll(".pill.is-on").forEach(function (p) { p.classList.remove("is-on"); });
    updateBody();
  }
})();
