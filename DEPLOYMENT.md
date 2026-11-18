# ResumeIQ — Free Deployment Guide (€0/month)

**The constraint:** Render's free tier can't run Ollama + a 3B model. So the
*demo* deployment must either call a free cloud LLM or run with no model at all.
This is the central trade-off of the project — here is how to handle it like an
AI PM, not just an engineer:

## The three honest deployment profiles

| Profile | LLM | Privacy | Cost | Best for |
|---|---|---|---|---|
| **A. Local-first (default)** | Ollama qwen2.5:3b on your machine | Nothing leaves the machine | €0 | You, demos recorded on your laptop |
| **B. Hosted + free cloud LLM** | Free tier via API (see below) | Resume/JD text transits a 3rd-party API, in-memory only, never stored | €0 | A public demo URL for interviews |
| **C. Hosted + no model at all** | Deterministic extraction only (`RESUMEIQ_LLM=offline`) | Nothing leaves the server | €0 | Zero-risk public page; skips the caveat entirely |

**Recommended portfolio setup:** Profile B for the live demo (interviewers click and it works) + Profile A video (Loom, 60–90s) showing local privacy mode + Profile C as the always-on fallback if the free API rate-limits at a bad moment. Disclose all three — that disclosure *is* the product thinking.

## Profile B — step by step (Groq free tier, no credit card)

1. Create a free API key at https://console.groq.com → API Keys (free, no card).
2. **Render (backend, free web service):**
   - Push repo to GitHub. New → Web Service → connect repo → Root directory: `.`
   - Build command: `.venv/Scripts/pip install -r requirements.txt` → use `pip install -r requirements.txt` (Render is Linux)
   - Start command: `uvicorn Backend.main:app --host 0.0.0.0 --port $PORT`
   - Free plan. Env vars:
     ```
     RESUMEIQ_LLM=cloud
     OPENAI_BASE_URL=https://api.groq.com/openai/v1
     OPENAI_API_KEY=<your key>
     OPENAI_MODEL=llama-3.3-70b-versatile
     RESUMEIQ_CORS_ORIGINS=https://<your-vercel-app>.vercel.app
     ```
   - Note: free tier sleeps after inactivity — first hit after idle takes ~30–50s (cold start). Mention it on the page or in the demo video.
3. **Vercel (frontend, free):**
   - New Project → `frontend/` directory → framework preset Vite (auto-detected).
   - Env var: `VITE_API_URL=https://<your-render-service>.onrender.com`
   - Deploy. The typed client already reads `VITE_API_URL`.
4. **Smoke test:** open the Vercel URL → upload PDF → paste JD → analyze. Expect a cold-start delay on first request only.

Free alternative LLM providers (any OpenAI-compatible endpoint works — set the three env vars, zero code changes):
- **Groq** (recommended): `llama-3.3-70b-versatile` — free, no card, very fast.
- **Google Gemini**: base `https://generativelanguage.googleapis.com/v1beta/openai/`, model `gemini-2.0-flash` — free quota, generous for a demo.
- **GitHub Models**: base `https://models.inference.ai.azure.com`, model `Llama-3.3-70B-Instruct` — free with your GitHub token.
- **OpenRouter**: free `:free` models — availability varies.

## Profile C — zero-third-party deployment (bulletproof fallback)

Same as Profile B but backend env: `RESUMEIQ_LLM=offline`. No API key, no third party, nothing to leak. The UI badge says “deterministic mode” — be upfront; most visitors just want to see it work, and deterministic mode scores credibly (100% on the labeled dev set).

## The privacy disclosure (use verbatim)

> “This hosted demo sends your resume and job description to *<provider>* for
> analysis and keeps nothing: requests are processed in memory, never stored,
> and no resume content is logged. For zero-data analysis, run ResumeIQ
> locally — extraction runs on your own machine (Ollama or deterministic mode).
> This is decision support for candidates, not an automated hiring system.”

Put it in the README, in the app footer/privacy note, and in your interview answer when asked “what happens to my data?”. Interviewers *probe* this in AI PM interviews; having a rehearsed, honest answer is a feature.

## Recorded demo (do this regardless)

- 60–90s Loom: the seeded flow on Profile A (local, qwen2.5:3b) with your real resume against a real APM JD.
- Show: upload → extraction → score with evidence → interview evidence map.
- Say out loud: “deterministic scoring, local inference, PII never leaves the machine, and here’s what breaks at scale.”
- Link it at the top of the README and in your portfolio. A working video outlives free-tier outages.

## How to talk about local-Ollama vs hosted cloud in interviews

When an interviewer asks "isn't this tied to your laptop? how would it work in prod?":

> "The product logic is provider-agnostic — one env var selects between local
> Ollama (max privacy, my dev environment), a free OpenAI-compatible tier
> (Groq/Gemini — what the public demo uses), or fully deterministic mode with
> no model at all. Local-first was a *privacy architecture decision*, not a
> limitation: resume data never leaves the machine by default, and the hosted
> demo discloses exactly what transits the third party (in-memory only, never
> stored). I priced that trade-off explicitly — $0 tiers, cold starts and rate
> limits documented — because trust is the product."

That's the senior-PM answer: constraint → explicit options → disclosed trade-offs →
chosen profile — not "I couldn't figure out deployment".

## Free-tier realities (say these out loud in interviews)

- Render free: 512MB RAM, ~750h/month, sleeps on idle, shared CPU. Fine for a demo, not a business.
- Groq/Gemini free: rate-limited (order of ~10–100 req/min); a demo link for <50 interviewers/day is comfortably inside it.
- No GPU on any free tier — a 3B local model is the only “on my machine” option, hence Profile A.
- Everything above is €0 forever; the only cost is your time and the honesty of the disclosure.
