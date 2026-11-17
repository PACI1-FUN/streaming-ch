#!/usr/bin/env python3
"""Holt die in den letzten 7 Tagen neu aufgeschalteten Filme und Serien der
Schweizer Streaminganbieter von JustWatch und schreibt sie in data.js.

Aufruf:  python3 update.py
Läuft auf GitHub automatisch (siehe .github/workflows/update.yml).
Benötigt nur Python 3 – keine Zusatzpakete, kein API-Schlüssel.
"""
import datetime as dt
import json
import os
import sys
import time
import urllib.request

COUNTRY = "CH"
LANG = "de"
DAYS = 7  # heute + 7 Tage zurück

# JustWatch-Kurzname je Anbieter (muss zu PROVIDERS in index.html passen).
PACKAGES = {
    "netflix":   ["nfx"],
    "prime":     ["prv"],
    "disney":    ["dnp"],
    "apple":     ["atp"],
    "paramount": ["pmp"],
    "skyshow":   ["ssv"],
    "mubi":      ["mbi"],
    "playsuisse": ["pys"],
}

API = "https://apis.justwatch.com/graphql"
IMG = "https://images.justwatch.com"

CONTENT = """
  title originalTitle originalReleaseYear runtime fullPath shortDescription posterUrl
  backdrops { backdropUrl }
  genres { shortName }
  externalIds { imdbId tmdbId }
  clips { externalId provider }
  scoring { imdbScore imdbVotes tmdbScore tomatoMeter }
"""

QUERY = """
query NewTitles($c: Country!, $d: Date!, $f: TitleFilter, $after: String) {
  newTitles(country: $c, date: $d, first: 100, after: $after, filter: $f, priceDrops: false) {
    pageInfo { hasNextPage endCursor }
    edges {
      newOffer(platform: WEB) { monetizationType standardWebURL package { shortName } }
      node {
        id objectType
        ... on MovieOrShow { content(country: $c, language: "%(lang)s") { %(content)s } }
        ... on Season {
          content(country: $c, language: "%(lang)s") { title seasonNumber posterUrl }
          show { id objectType content(country: $c, language: "%(lang)s") { %(content)s } }
        }
      }
    }
  }
}
""" % {"lang": LANG, "content": CONTENT}


def gql(variables):
    body = json.dumps({"query": QUERY, "variables": variables}).encode()
    req = urllib.request.Request(API, data=body, headers={
        "content-type": "application/json",
        "user-agent": "Mozilla/5.0 (streaming-ch update script)",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                data = json.load(r)
            if data.get("errors"):
                raise RuntimeError(data["errors"][0].get("message"))
            return data["data"]
        except Exception as e:  # noqa: BLE001
            if attempt == 3:
                raise
            print(f"  Fehler ({e}), neuer Versuch …", file=sys.stderr)
            time.sleep(2 * (attempt + 1))


def img(path, profile):
    if not path:
        return None
    return IMG + path.replace("{profile}", profile).replace("{format}", "jpg")


def build_item(edge, date):
    node, offer = edge["node"], edge.get("newOffer") or {}
    if offer.get("monetizationType") in ("BUY", "RENT"):
        return None
    otype = node["objectType"]
    if otype == "SHOW_SEASON":
        show = node.get("show") or {}
        c = show.get("content") or {}
        season = node.get("content") or {}
        key = show.get("id") or node["id"]
        kind, season_no = "tv", season.get("seasonNumber")
        poster = season.get("posterUrl") or c.get("posterUrl")
    else:
        c = node.get("content") or {}
        key = node["id"]
        kind, season_no = ("movie" if otype == "MOVIE" else "tv"), None
        poster = c.get("posterUrl")
    if not c.get("title"):
        return None
    sc = c.get("scoring") or {}
    trailer = next((x["externalId"] for x in c.get("clips") or [] if x.get("provider") == "YOUTUBE"), None)
    backdrops = c.get("backdrops") or []
    return {
        "id": key,
        "type": kind,
        "title": c.get("title"),
        "original": c.get("originalTitle"),
        "year": c.get("originalReleaseYear"),
        "season": season_no,
        "date": date,
        "runtime": c.get("runtime"),
        "overview": c.get("shortDescription") or "",
        "genres": [g["shortName"] for g in c.get("genres") or []],
        "poster": img(poster, "s332"),
        "backdrop": img(backdrops[0]["backdropUrl"], "s1440") if backdrops else None,
        "imdbId": (c.get("externalIds") or {}).get("imdbId"),
        "imdb": sc.get("imdbScore"),
        "imdbVotes": sc.get("imdbVotes"),
        "tmdb": sc.get("tmdbScore"),
        "rt": sc.get("tomatoMeter"),
        "trailer": trailer,
        "watch": offer.get("standardWebURL"),
        "jw": ("https://www.justwatch.com" + c["fullPath"]) if c.get("fullPath") else None,
    }


def fetch_provider(packages, dates):
    items = {}
    for date in dates:
        after = None
        while True:
            data = gql({"c": COUNTRY, "d": date, "after": after, "f": {"packages": packages}})
            nt = data["newTitles"]
            for edge in nt["edges"]:
                it = build_item(edge, date)
                if not it:
                    continue
                k = f'{it["id"]}|{it["season"] or ""}'
                if k not in items or it["date"] > items[k]["date"]:
                    items[k] = it
            if not nt["pageInfo"]["hasNextPage"]:
                break
            after = nt["pageInfo"]["endCursor"]
        time.sleep(0.3)
    return sorted(items.values(), key=lambda x: x["date"], reverse=True)


def main():
    today = dt.date.today()
    dates = [(today - dt.timedelta(days=i)).isoformat() for i in range(DAYS + 1)]
    out = {"generated": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "from": dates[-1], "to": dates[0], "providers": {}}
    for key, packages in PACKAGES.items():
        print(f"{key}: lade {len(dates)} Tage …")
        out["providers"][key] = fetch_provider(packages, dates)
        print(f"  {len(out['providers'][key])} Titel")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data.js")
    with open(path, "w", encoding="utf-8") as f:
        f.write("// Automatisch erzeugt von update.py – nicht von Hand bearbeiten.\n")
        f.write("window.STREAM_DATA = ")
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
        f.write(";\n")
    print(f"Gespeichert: {path}")


if __name__ == "__main__":
    main()
