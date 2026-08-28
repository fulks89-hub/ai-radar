# AI Radar React dashboard

Responsive React/Vite presentation layer for AI Radar reports. Ranking, corroboration, and trust decisions remain in the Python pipeline. The self-hosted server can optionally stage a selected topic for review in Observatory.

## Local development

From `dashboard/`:

```sh
npm install
npm run check
npm test
npm start
```

`npm run build` copies the latest available `../reports/*.json` into `public/data/` and emits a portable static build under `dist/` with Vite `base: './'`. `npm start` serves it on `127.0.0.1:4174`.

Set `AI_RADAR_OBSERVATORY_ROOT` to an absolute Observatory repository path to enable card-level Atlas staging. The older `AI_RADAR_BRAIN_ROOT` name remains a compatibility alias. The destination must contain `.brain/policies.yaml` and `staging/README.md`; candidates are created only under `staging/ai-radar/`. Use `npm run start:share` for a read-only session.

## CI artifact

Every AIRadar workflow run uploads `ai-radar-dashboard`. The built dashboard includes the report data produced by that exact workflow run, so a dashboard artifact and its data share one validation boundary.

The dashboard is mobile-first but expands to a two-column laptop layout. It includes:

- Today / 7-day views;
- separate signal-strength and estimated-usefulness scores;
- `act`, `evaluate`, `watch`, and explicit `skip` bands;
- per-card maps from signal to every matched project, matching Observatory core ideas, and the next action;
- corroboration/verification badges;
- search and verification filters;
- expandable source evidence;
- configurable watch-target visibility;
- owner Share Sheet priority;
- official X bookmark status and weekly budget estimate;
- an always-on AI Daily Brief source panel;
- the external-content trust boundary.

The only write action is an explicit staging operation. It accepts an opaque trend ID, re-resolves the trend from the server-side report, and never promotes content into Observatory's canonical directories.
