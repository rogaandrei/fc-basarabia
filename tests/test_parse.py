#!/usr/bin/env python3
"""Verifică dacă scriptul înțelege încă paginile ligii.

Rulează:  python tests/test_parse.py
Dacă liga schimbă aspectul paginilor și site-ul nu se mai actualizează, salvează paginile
în tests/fixtures/ (clasament.html, program.html, lot.html), rulează acest test și vezi ce se strică.
"""
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import update  # noqa: E402

FIX = Path(__file__).resolve().parent / "fixtures"


def soup(text):
    return BeautifulSoup(text, "html.parser")


def read(name):
    return (FIX / (name + ".html")).read_text(encoding="utf-8")


def test_standings():
    rows = update.parse_standings(soup(read("clasament")))
    assert len(rows) == 16
    me = [r for r in rows if "BASARABIA" in r["team"]][0]
    assert (me["m"], me["v"], me["e"], me["i"], me["gm"], me["gp"], me["pct"]) == (8, 3, 2, 3, 26, 24, 11)


def test_schedule():
    ms = update.parse_schedule(soup(read("program")))
    assert len(ms) == 120
    first = [m for m in ms if m["round"] == 1 and "BASARABIA" in m["home"]][0]
    assert (first["away"], first["hs"], first["aw"], first["time"], first["date"]) == ("LEX TM", 5, 4, "19:00", "2026-08-30")
    pending = [m for m in ms if m["round"] == 7 and "BASARABIA" in m["home"]][0]
    assert pending["hs"] is None and pending["away"] == "PLOPI"


def test_schedule_teams_in_one_cell():
    html = re.sub(r"<td><a href=\"#\">([^<]+)</a></td><td><a href=\"#\">([^<]+)</a></td>", r'<td><a href="#">\1 - \2</a></td>', read("program"))
    ms = update.parse_schedule(soup(html))
    assert len(ms) == 120 and ms[0]["home"] and ms[0]["away"]


def test_schedule_without_round_headers():
    html = re.sub(r"<tr><th colspan=\"7\">Etapa[^<]*</th></tr>", "", read("program"))
    ms = update.parse_schedule(soup(html))
    assert len(ms) == 120 and max(m["round"] for m in ms) == 15


def test_roster():
    s = soup(read("lot"))
    pl = update.parse_roster(s)
    assert len(pl) == 18
    assert [p for p in pl if p["name"] == "Rudei Ghenadii"][0]["red"] == 1
    info = update.parse_team_info(s)
    assert info["colors"] == "gri / albastru" and info["coach"] == "Guma Daniel"
    assert info["delegates"] == ["Guma Daniel", "Cocirlan Stefan"]


def test_bad_page_raises():
    for fn, page in ((update.parse_standings, "<html><body>Pagina in lucru</body></html>"),
                     (update.parse_schedule, "<html><body></body></html>"),
                     (update.parse_roster, "<table><tr><td>x</td></tr></table>")):
        try:
            fn(soup(page))
        except ValueError:
            continue
        raise AssertionError("trebuia să dea eroare: %s" % fn.__name__)


if __name__ == "__main__":
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print("OK     ", name)
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print("EȘUAT  ", name, "->", repr(exc))
    sys.exit(1 if failed else 0)
