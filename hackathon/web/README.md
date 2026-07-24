# o2c-dashboard-web

React + TypeScript + Tailwind + Recharts frontend for the KPC order-to-cash
leakage dashboard. See the [repo root README](../README.md) for the full
project (pipeline, API, deployment).

## Development

```bash
npm install
npm run dev      # http://localhost:5173, proxies /api -> http://localhost:8010
```

Requires the API running separately: `make api-dev` from the repo root.

## Commands

- `npm run dev` — Vite dev server with HMR
- `npm run build` — type-check (`tsc -b`) + production build to `dist/`
- `npm run lint` — oxlint
- `npm run preview` — serve the production build locally
