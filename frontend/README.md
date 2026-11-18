# ResumeIQ — Frontend

React 19 + TypeScript + Vite. Upload → JD → evidence-grounded report (live API at `http://localhost:8000` by default; override with `VITE_API_URL`).

```powershell
npm install
npm run dev      # dev server on :5173
npm run build    # type-check + production build
```

The API contract lives in `src/services/api.ts` and mirrors `Backend/schemas.py`. See the root `README.md` for the full picture and `docs/PRD.md` for product decisions.
