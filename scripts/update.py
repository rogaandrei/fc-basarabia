#!/usr/bin/env python3
"""Actualizează datele site-ului FC Basarabia de pe paginile ligii.

Citește 3 pagini de pe alborzminifotbal.ro (clasament, program, lotul echipei),
le transformă în data.json + data.js (folosit de site) și nu scrie nimic dacă
datele nu s-au schimbat.

Folosire:
    python scripts/update.py                      # citește de pe site-ul ligii
    python scripts/update.py --local tests/fixtures   # citește fișiere HTML locale (test)
"""
import argparse
import datetime as dt
import json
import re
import sys
import time
import unicodedata
from pathlib import Path

from bs4 import BeautifulSoup, NavigableString, Tag

ROOT = Path(__file__).resolve().parent.parent
BASE = "https://www.alborzminifotbal.ro/"
PAGES = {
    "clasament": "clasament-liga-III-B.html",
    "program": "program-liga-III-B.html",
    "lot": "echipe-lot-fc%20basarabia%20.html",
}
TEAM = "FC BASARABIA"
SEASON = "2026/2027"

DATE_RE = re.compile(r"^\d{2}\.\d{2}\.\d{4}$")
ROUND_RE = re.compile(r"Etapa\s*(\d+)\s*[-–]\s*(\d{2}\.\d{2}\.\d{4})", re.I)
SCORE_RE = re.compile(r"^(\d+)\s*[-–:]\s*(\d+)$")
INT_RE = re.compile(r"^\d+$")
HOUR_RE = re.compile(r"^(\d{1,2})(?::(\d{2}))?$")


# ───────────────────────── utilitare ─────────────────────────

def ascii_key(text):
    """'Vacarița Flavius' -> 'vacarita flavius' (pentru potriviri)."""
    t = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", t).strip().lower()


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", ascii_key(text)).strip("-")


def title_case(text):
    return " ".join(w.capitalize() for w in re.sub(r"\s+", " ", text).strip().split(" "))


def fetch(name, local_dir):
    if local_dir:
        path = Path(local_dir) / (name + ".html")
        return BeautifulSoup(path.read_bytes(), "html.parser")
    import requests

    url = BASE + PAGES[name]
    last = None
    for attempt in range(3):
        try:
            r = requests.get(
                url,
                timeout=30,
                headers={"User-Agent": "Mozilla/5.0 (compatible; FCBasarabiaSite/1.0)"},
            )
            r.raise_for_status()
            # lăsăm BeautifulSoup să ghicească codarea (meta charset / UTF-8 / Windows-1250)
            return BeautifulSoup(r.content, "html.parser")
        except Exception as exc:  # noqa: BLE001
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("nu pot citi %s: %s" % (url, last))


def leaf_rows(soup):
    """Rândurile <tr> care nu conțin alte rânduri (tabele imbricate)."""
    return [tr for tr in soup.find_all("tr") if tr.find("tr") is None]


def cells(tr):
    out = []
    for c in tr.find_all(["td", "th"]):
        if c.find(["td", "th"]) is not None:
            continue
        out.append(re.sub(r"\s+", " ", c.get_text(" ", strip=True)))
    return out


def iso(d):
    dd, mm, yy = d.split(".")
    return "%s-%s-%s" % (yy, mm, dd)


# ───────────────────────── clasament ─────────────────────────

def parse_standings(soup):
    rows, seen = [], set()
    for tr in leaf_rows(soup):
        cs = cells(tr)
        if len(cs) < 9 or not INT_RE.match(cs[0]) or not re.search(r"[A-Za-z]", cs[1]):
            continue
        nums = cs[2:9]
        if not all(INT_RE.match(n) for n in nums):
            continue
        team = re.sub(r"\s+", " ", cs[1]).strip().upper()
        if team in seen:
            continue
        seen.add(team)
        m, v, e, i, gm, gp, pct = (int(n) for n in nums)
        rows.append(dict(pos=int(cs[0]), team=team, m=m, v=v, e=e, i=i, gm=gm, gp=gp, pct=pct))
    rows.sort(key=lambda r: r["pos"])
    if len(rows) < 8:
        raise ValueError("clasament: am găsit doar %d echipe" % len(rows))
    if not any(TEAM in r["team"] for r in rows):
        raise ValueError("clasament: nu găsesc echipa %s" % TEAM)
    return rows


# ───────────────────────── program ─────────────────────────

def parse_schedule(soup):
    matches, seen = [], set()
    current = None
    for node in soup.descendants:
        if isinstance(node, NavigableString):
            if node.find_parent("tr") is None:
                mm = ROUND_RE.search(str(node))
                if mm:
                    current = int(mm.group(1))
            continue
        if not isinstance(node, Tag) or node.name != "tr" or node.find("tr") is not None:
            continue
        cs = cells(node)
        joined = " ".join(cs)
        hm = ROUND_RE.search(joined)
        if hm and not any(DATE_RE.match(c) for c in cs):
            current = int(hm.group(1))
            continue
        di = next((k for k, c in enumerate(cs) if DATE_RE.match(c)), None)
        if di is None or di < 3:
            continue
        before = cs[:di]
        score_txt = before[-1]
        sm = SCORE_RE.match(score_txt)
        if not sm and score_txt not in ("-", "–", "—", ""):
            continue
        teams = [c for c in before[:-1] if re.search(r"[A-Za-z]", c)]
        if len(teams) == 1:
            parts = re.split(r"\s+(?:-|–|vs\.?)\s+", teams[0], maxsplit=1)
            teams = parts if len(parts) == 2 else teams
        if len(teams) != 2:
            continue
        home, away = (t.strip().upper() for t in teams)
        hour = None
        if di + 1 < len(cs):
            hh = HOUR_RE.match(cs[di + 1])
            if hh:
                hour = "%02d:%s" % (int(hh.group(1)), hh.group(2) or "00")
        key = (current, home, away)
        if key in seen:
            continue
        seen.add(key)
        matches.append(
            dict(
                round=current,
                date=iso(cs[di]),
                time=hour,
                home=home,
                away=away,
                hs=int(sm.group(1)) if sm else None,
                aw=int(sm.group(2)) if sm else None,
            )
        )
    if not matches:
        raise ValueError("program: nu am găsit meciuri")
    # dacă pagina nu are titluri „Etapa N”, numărăm etapele după data meciurilor
    if any(m["round"] is None for m in matches):
        dates = sorted({m["date"] for m in matches})
        for m in matches:
            if m["round"] is None:
                m["round"] = dates.index(m["date"]) + 1
    matches.sort(key=lambda m: (m["round"], m["date"], m["time"] or ""))
    return matches


# ───────────────────────── lot ─────────────────────────

def parse_roster(soup):
    players, seen = [], set()
    for tr in leaf_rows(soup):
        cs = cells(tr)
        if len(cs) < 5 or not INT_RE.match(cs[0]) or not re.search(r"[A-Za-z]", cs[1]):
            continue
        tail = cs[-3:]
        if not all(INT_RE.match(x) for x in tail):
            continue
        name = title_case(cs[1])
        if name in seen:
            continue
        seen.add(name)
        players.append(dict(name=name, goals=int(tail[0]), yellow=int(tail[1]), red=int(tail[2])))
    if not players:
        raise ValueError("lot: nu am găsit jucători")
    return players


def parse_team_info(soup):
    lines = [l for l in soup.get_text("\n", strip=True).split("\n") if l.strip()]
    stop = re.compile(r"(:|^ANTRENOR|^DELEGA|^CULORI|^Nr\.?$)", re.I)

    def grab(label):
        for i, line in enumerate(lines):
            if re.match(label, line, re.I):
                vals = []
                rest = line.split(":", 1)[1].strip() if ":" in line else ""
                if rest:
                    vals.append(rest)
                for nxt in lines[i + 1 : i + 6]:
                    if stop.search(nxt) or not nxt.isupper():
                        break
                    vals.append(nxt)
                return [title_case(v) for v in vals]
        return []

    return dict(
        colors=" ".join(grab(r"CULORILE\s+ECHIPEI")).lower(),
        coach=", ".join(grab(r"ANTRENORII\s+ECHIPEI")),
        delegates=grab(r"DELEGATII\s+ECHIPEI"),
    )


# ───────────────────────── asamblare ─────────────────────────

def load_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return default


def find_photo(name):
    for ext in ("jpg", "jpeg", "png", "webp"):
        p = ROOT / "img" / "players" / ("%s.%s" % (slug(name), ext))
        if p.exists():
            return "img/players/%s.%s" % (slug(name), ext)
    return None


def list_gallery():
    d = ROOT / "img" / "gallery"
    files = [p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")] if d.exists() else []
    return ["img/gallery/" + p.name for p in sorted(files, key=lambda p: p.name.lower())]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--local", help="folder cu pagini HTML salvate (clasament.html, program.html, lot.html)")
    args = ap.parse_args()

    config = load_json(ROOT / "config.json", {})
    fixes = {ascii_key(k): v for k, v in config.get("diacritice", {}).items()}
    positions = {ascii_key(k): v for k, v in config.get("pozitii", {}).items()}
    old = load_json(ROOT / "data.json", {})
    data = {k: old.get(k) for k in ("team", "standings", "matches", "players")}
    errors = []

    def fix(text):
        return fixes.get(ascii_key(text), text)

    try:
        data["standings"] = parse_standings(fetch("clasament", args.local))
    except Exception as exc:  # noqa: BLE001
        errors.append("clasament: %s" % exc)
    try:
        data["matches"] = parse_schedule(fetch("program", args.local))
    except Exception as exc:  # noqa: BLE001
        errors.append("program: %s" % exc)
    try:
        soup = fetch("lot", args.local)
        players = parse_roster(soup)
        for p in players:
            p["name"] = fix(p["name"])
            p["pos"] = positions.get(ascii_key(p["name"]), "")
        players.sort(key=lambda p: ascii_key(p["name"]))
        data["players"] = players
        info = parse_team_info(soup)
        info["delegates"] = [fix(d) for d in info["delegates"]]
        info["coach"] = fix(info["coach"])
        data["team"] = info
    except Exception as exc:  # noqa: BLE001
        errors.append("lot: %s" % exc)

    for p in data.get("players") or []:
        p["photo"] = find_photo(p["name"])
        p["pos"] = positions.get(ascii_key(p["name"]), p.get("pos", ""))

    data["name"] = "FC Basarabia"
    data["season"] = SEASON
    data["gallery"] = list_gallery()

    previous = {k: v for k, v in old.items() if k != "updated"}
    if data == previous and not errors:
        print("Nicio schimbare în date.")
        return 0
    if data != previous:
        data["updated"] = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        text = json.dumps(data, ensure_ascii=False, indent=1)
        (ROOT / "data.json").write_text(text + "\n", encoding="utf-8")
        (ROOT / "data.js").write_text("window.__DATA__=" + text + ";\n", encoding="utf-8")
        print("Date actualizate: %d echipe, %d meciuri, %d jucători." % (
            len(data.get("standings") or []), len(data.get("matches") or []), len(data.get("players") or [])))
    for e in errors:
        print("EROARE (am păstrat datele vechi pentru această parte) ->", e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
