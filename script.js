/* FC Basarabia — afișează datele din data.js (generat de scripts/update.py) */
(function () {
  var D = window.__DATA__ || {};
  var TEAM = "FC BASARABIA";
  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };
  var isMe = function (t) { return String(t).toUpperCase().indexOf("BASARABIA") > -1; };
  var teamName = function (t) { return isMe(t) ? "FC Basarabia" : t; };
  var dmy = function (iso) { var p = String(iso).split("-"); return p[2] + "." + p[1] + "." + p[0]; };

  /* ── clasament + statistici ── */
  var standings = D.standings || [];
  $("tb").innerHTML = standings.map(function (r) {
    return "<tr" + (isMe(r.team) ? ' class="me"' : "") + "><td>" + r.pos + "</td><td>" + esc(teamName(r.team)) +
      "</td><td>" + [r.m, r.v, r.e, r.i, r.gm, r.gp, r.pct].join("</td><td>") + "</td></tr>";
  }).join("");
  var me = standings.filter(function (r) { return isMe(r.team); })[0];
  $("s-gm").textContent = me ? me.gm : "—";
  $("s-gp").textContent = me ? me.gp : "—";

  /* ── meciurile echipei ── */
  var mine = (D.matches || []).filter(function (m) { return isMe(m.home) || isMe(m.away); });
  var played = mine.filter(function (m) { return m.hs != null; });
  var best = 0, run = 0;
  played.forEach(function (m) {
    var f = isMe(m.home) ? m.hs : m.aw, a = isMe(m.home) ? m.aw : m.hs;
    run = f > a ? run + 1 : 0;
    if (run > best) best = run;
  });
  $("s-vc").textContent = played.length ? best : "—";

  var today = new Date().toISOString().slice(0, 10);
  function row(m) {
    var c = "", box;
    if (m.hs != null) {
      var f = isMe(m.home) ? m.hs : m.aw, a = isMe(m.home) ? m.aw : m.hs;
      c = f > a ? "V" : f === a ? "E" : "I";
      box = '<span class="sc ' + c + '">' + m.hs + " - " + m.aw + "</span>";
    } else if (m.date < today) {
      box = '<span class="sc n" title="Scorul nu a fost introdus încă">–</span>';
    } else {
      box = '<span class="sc n">' + esc(m.time || "") + "</span>";
    }
    var h = isMe(m.home) ? "<b>FC Basarabia</b>" : esc(m.home);
    var a2 = isMe(m.away) ? "<b>FC Basarabia</b>" : esc(m.away);
    return '<div class="m"><small>Etapa ' + m.round + "<br>" + dmy(m.date) + "</small><span>" + h + " – " + a2 + "</span>" + box + "</div>";
  }
  var results = played.slice().reverse();
  var upcoming = mine.filter(function (m) { return m.hs == null; });
  $("ml").innerHTML = mine.length
    ? (results.length ? '<div class="sub">Rezultate</div>' + results.map(row).join("") : "") +
      (upcoming.length ? '<div class="sub">Program</div>' + upcoming.map(row).join("") : "")
    : '<p class="empty">Meciurile sezonului ' + esc(D.season || "") + " vor apărea aici.</p>";

  /* ── lotul ── */
  var PL = (D.players || []).slice().sort(function (x, y) { return x.name.localeCompare(y.name, "ro"); });
  var POS = { P: "Portar", A: "Apărător", M: "Mijlocaș", T: "Atacant" };
  var GROUPS = { P: "Portari", A: "Apărători", M: "Mijlocași", T: "Atacanți", "": "Alți jucători" };
  function ph(p) { return p.photo ? '<img src="' + esc(p.photo) + '" alt="' + esc(p.name) + '" loading="lazy">' : "[poză]"; }
  function card(p) {
    return '<button class="pl" data-i="' + PL.indexOf(p) + '"><div>' + ph(p) + "</div><b>" + esc(p.name) + "</b></button>";
  }
  $("gr").innerHTML = PL.map(card).join("");
  var gp = "";
  ["P", "A", "M", "T", ""].forEach(function (k) {
    var q = PL.filter(function (p) { return (p.pos || "") === k; });
    if (q.length) gp += '<div class="sub">' + GROUPS[k] + " (" + q.length + ')</div><div class="grid">' + q.map(card).join("") + "</div>";
  });
  $("gp").innerHTML = gp;

  /* ── informații echipă + data actualizării ── */
  var t = D.team || {}, info = [];
  if (t.colors) info.push("<b>Culorile echipei:</b> " + esc(t.colors));
  if (t.coach) info.push("<b>Antrenor:</b> " + esc(t.coach));
  if (t.delegates && t.delegates.length) info.push("<b>Delegați:</b> " + esc(t.delegates.join(", ")));
  $("ti").innerHTML = info.join("<br>");
  if (D.updated) {
    var u = new Date(D.updated);
    $("upd").textContent = " · Date actualizate: " + u.toLocaleString("ro-RO", { day: "2-digit", month: "2-digit", year: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  /* ── galerie ── */
  var GAL = D.gallery || [];
  $("gl").innerHTML = GAL.map(function (s, i) {
    return '<button class="gi" data-g="' + i + '"><img src="' + esc(s) + '" alt="Fotografie FC Basarabia" loading="lazy"></button>';
  }).join("");
  var lb = $("lb"), gx = 0;
  function showG(i) { gx = (i + GAL.length) % GAL.length; $("lbi").src = GAL[gx]; }

  /* ── fereastra jucătorului ── */
  var mo = $("mo");
  document.addEventListener("click", function (e) {
    var g = e.target.closest(".gi");
    if (g) { showG(+g.dataset.g); lb.classList.add("show"); return; }
    if (e.target.id === "lbp") showG(gx - 1);
    else if (e.target.id === "lbn") showG(gx + 1);
    else if (e.target === lb || e.target.id === "lbx") lb.classList.remove("show");
    var c = e.target.closest(".pl");
    if (c) {
      var p = PL[+c.dataset.i];
      $("mn").textContent = p.name;
      $("mph").innerHTML = ph(p);
      $("mp").textContent = POS[p.pos] || "Jucător";
      $("mg").textContent = p.goals;
      mo.classList.add("show");
      $("mc").focus();
      return;
    }
    if (e.target === mo || e.target.id === "mc") mo.classList.remove("show");
  });
  addEventListener("keydown", function (e) {
    if (e.key === "Escape") { mo.classList.remove("show"); lb.classList.remove("show"); }
    if (lb.classList.contains("show")) {
      if (e.key === "ArrowLeft") showG(gx - 1);
      if (e.key === "ArrowRight") showG(gx + 1);
    }
  });

  /* ── pagini (Acasă, Echipa, Meciuri…) ── */
  var P = { home: "Acasă", echipa: "Echipa", meciuri: "Meciuri", clasament: "Clasament", galerie: "Galerie", contact: "Contact" };
  function route() {
    var p = location.hash.replace("#/", "") || "home";
    if (!P[p]) p = "home";
    document.querySelectorAll("[data-p]").forEach(function (el) {
      el.classList.toggle("show", el.dataset.p.split(" ").indexOf(p) > -1);
    });
    document.querySelectorAll("nav a").forEach(function (a) { a.classList.toggle("on", a.dataset.n === p); });
    $("pn").textContent = P[p];
    document.title = "FC Basarabia — " + P[p];
    window.scrollTo(0, 0);
  }
  addEventListener("hashchange", route);
  route();
})();
