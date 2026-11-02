# Dig Out

Browser-Umsetzung des Gefängnisausbruch-Brettspiels *Dig Your Way Out* (eigene Karten, eigene Grafiken).
Website: [dig-out.marxai.de](https://dig-out.marxai.de).
Gesamtplan: [project.md](project.md) · Spielregeln: [docs/rules.md](docs/rules.md)

| Ordner | Inhalt |
|---|---|
| `game-data/` | Regeln als Daten: Spielplan, Karten, Gangs, Hintergründe, Regelwerte (YAML) |
| `backend/` | Python: Spiel-Engine (`digout.engine`), Bots & Simulation (`digout.sim`) |
| `art/` | Blender-Pipeline: Build-Skripte, Renders, Postprocessing |
| `frontend/public/assets/` | generierte Web-Assets (WebP) |
| `docs/` | Regeln, später ADRs |

## Backend

```bash
cd backend
uv sync                                    # Python 3.13 + Abhängigkeiten
uv run pytest                              # Regel-, Determinismus- und Property-Tests
uv run ruff check src tests && uv run mypy src
uv run python -m digout.sim.run_sim --games 100 --players 4 --bot heuristic
```

Auf einem Windows-Laufwerk unter WSL: `export UV_LINK_MODE=copy`.

## Lokal spielen (Phase 3, ohne AWS)

```bash
cd backend && uv run uvicorn digout.devserver:app --reload --port 8100   # Terminal 1
cd frontend && npm install && npm run dev                                # Terminal 2 → http://localhost:5180
```

Mehrere Spieler in einem Browser: Tabs mit `?as=Name` öffnen (z. B. `http://localhost:5180/?as=Anna`, `…/?as=Ben`) –
jeder Tab ist dann ein eigener Spieler (nur im Entwicklungsmodus).
Spiel erstellen → Code oder Link teilen → Figur wählen → bereit → Gastgeber startet.

## Deployment (AWS)

```bash
uv run --project backend python scripts/deploy.py --plan    # erst ansehen
uv run --project backend python scripts/deploy.py           # deployen
```

Details, Voraussetzungen und Betrieb: [docs/deploy.md](docs/deploy.md). Infrastruktur: `infra/` (Terraform).

## Grafik

Das Website-Icon liegt als SVG in `art/brand/app-icon.svg`. `cd art && npm run icons`
erzeugt daraus SVG-Favicon, ICO und PNG-App-Icons; der vollständige Postprocessing-Lauf
verwendet dieselbe Quelle.

```bash
art/scripts/render_all.sh                  # BLENDER=/pfad/zu/blender, ca. 40 min
cd art && npm install && npm run postprocess
```

Große Binärdateien (`*.blend`, `art/vendor`, Roh-Renders) laufen über Git LFS (`git lfs install`).
