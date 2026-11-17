# Streaming Schweiz – Anleitung

Man wählt einen oder mehrere Streaminganbieter; die App zeigt die Filme und Serien, die in den **letzten 7 Tagen in der
Schweiz neu aufgeschaltet** wurden (auch ältere Filme, die neu ins Abo kommen, und neue Staffeln).

## Wie es funktioniert

| Datei | Aufgabe |
|-------|---------|
| `index.html` | Die App (Anbieter-Auswahl, gemeinsame Liste, Detailansicht) |
| `data.js` | Die Daten – wird **automatisch erzeugt**, nicht von Hand bearbeiten |
| `update.py` | Holt die Daten bei JustWatch und schreibt `data.js` |
| `.github/workflows/update.yml` | Lässt `update.py` auf GitHub 2× täglich laufen |

Kein API-Schlüssel nötig. Quelle ist die inoffizielle Schnittstelle von JustWatch
(`apis.justwatch.com/graphql`). Ändert JustWatch diese, muss `update.py` angepasst werden.

Der Browser darf JustWatch nicht direkt abfragen – deshalb holt GitHub die Daten und legt sie
als `data.js` neben die App.

## Anbieter

Netflix, Amazon Prime Video, Disney+, Apple TV+, Paramount+, Sky Show, MUBI, Play Suisse.
(oneplus, blue+, Sky Sport, Zattoo und Joyn sind nicht enthalten – JustWatch hat für sie keine Schweizer Daten.)

## Bedienung

- **Übersicht** (Schweizerkreuz oben links): Anbieter antippen = auswählen/abwählen (Häkchen),
  „Alle wählen“ / „Keine“, dann „… Anbieter anzeigen“.
- Die Liste zeigt die Titel **aller gewählten Anbieter zusammen**; läuft ein Titel bei mehreren,
  stehen alle Anbieter-Abzeichen auf derselben Karte.
- Unter dem Titel stehen die gewählten Anbieter: **✕** entfernt einen, **+ Anbieter** öffnet die
  Übersicht, um wieder welche hinzuzufügen. Die Auswahl bleibt auf dem Gerät gespeichert.

## Lokal testen (Mac)

Im Terminal im Ordner `streaming-ch`:

```bash
python3 update.py
```

Danach `index.html` per Doppelklick öffnen.

## Online stellen

Schritt-für-Schritt-Anleitung: **[ONLINE-STELLEN.md](ONLINE-STELLEN.md)**

Nach einer Änderung an `index.html` genügt es, die Datei im Repository erneut hochzuladen
(**Add file → Upload files**) – GitHub veröffentlicht die neue Version automatisch.

## Anbieter hinzufügen oder entfernen

1. In `index.html` die Liste `PROVIDERS` bearbeiten (eine Zeile pro Anbieter).
2. In `update.py` bei `PACKAGES` eine Zeile mit demselben `key` und dem JustWatch-Kürzel
   ergänzen bzw. löschen (z. B. `"hbomax": ["mxx"],` für HBO Max).
3. Die Kürzel aller Schweizer Anbieter zeigt dieser Befehl:

```bash
curl -s https://apis.justwatch.com/graphql -H 'content-type: application/json' -d '{"query":"{ packages(country: CH, platform: WEB) { shortName clearName } }"}'
```
