import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./App.css";
import { analyzeResume, type AnalysisResponse, type SkillAssessment } from "./services/api";
import CardDeck, { type DeckTab } from "./components/CardDeck";
import LoadingStages from "./components/LoadingStages";

const STATUS_LABEL: Record<string, string> = {
  matched: "Matched",
  partial: "Partial",
  missing: "No evidence",
};

const capitalize = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);

/* ------------------------------------------------------------------ */
/* Score gauge — an arc, not a shout.                                  */
/* ------------------------------------------------------------------ */
function ScoreGauge({ score, verdict }: { score: number; verdict: string }) {
  const tone = score >= 70 ? "good" : score >= 45 ? "warn" : "bad";
  const arcLen = Math.PI * 52; // r = 52
  const filled = arcLen * (Math.max(0, Math.min(100, score)) / 100);
  return (
    <div className={`gauge gauge-${tone}`}>
      <svg viewBox="0 0 120 70" role="img" aria-label={`Match score ${score} out of 100`}>
        <path className="gauge-track" d="M 8 62 A 52 52 0 0 1 112 62" pathLength={arcLen} />
        <path
          className="gauge-value"
          d="M 8 62 A 52 52 0 0 1 112 62"
          pathLength={arcLen}
          strokeDasharray={`${filled} ${arcLen}`}
        />
      </svg>
      <div className="gauge-readout">
        <span className="gauge-number">{score}</span>
        <span className="gauge-of">/ 100</span>
      </div>
      <p className="gauge-verdict">{verdict}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Dimension bars                                                       */
/* ------------------------------------------------------------------ */
function DimensionBars({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <div className="dimension-list">
      {analysis.dimensions.map((d) => (
        <div className="dimension" key={d.name}>
          <div className="dimension-head">
            <span className="dimension-name">{d.name}</span>
            <span className="dimension-score">
              {d.score === null ? "n/a" : Math.round(d.score)}
              <em> · wt {Math.round(d.weight)}%</em>
            </span>
          </div>
          <div className="dimension-track">
            <div className="dimension-fill" style={{ width: `${d.score ?? 0}%` }} />
          </div>
          <p className="dimension-detail">{d.detail}</p>
        </div>
      ))}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Skill evidence row (expandable)                                      */
/* ------------------------------------------------------------------ */
function SkillRow({ skill }: { skill: SkillAssessment }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`skill-row skill-${skill.status}`}>
      <button type="button" className="skill-row-button" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span className="skill-dot" aria-hidden="true" />
        <span className="skill-name">{capitalize(skill.skill)}</span>
        <span className="skill-status">{STATUS_LABEL[skill.status]}</span>
        <span className="skill-caret" aria-hidden="true">{open ? "–" : "+"}</span>
      </button>
      {open && (
        <div className="skill-evidence">
          {skill.evidence
            ? <blockquote>“{skill.evidence}”</blockquote>
            : <p className="no-evidence">No direct evidence found in the resume text.</p>}
          <small>{skill.note}</small>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* App                                                                  */
/* ------------------------------------------------------------------ */
function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "analyzing" | "done" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const [recTab, setRecTab] = useState("all");
  const [mapTab, setMapTab] = useState("all");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);

  const acceptFile = useCallback((file: File | undefined) => {
    setFileError("");
    if (!file) return;
    const name = file.name.toLowerCase();
    if (!name.endsWith(".pdf") && !name.endsWith(".docx")) {
      setFileError("Please upload a PDF or DOCX file.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setFileError("File too large. Maximum size is 5 MB.");
      return;
    }
    setResumeFile(file);
  }, []);

  const onDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setDragging(false);
    acceptFile(event.dataTransfer.files?.[0]);
  }, [acceptFile]);

  const analyze = useCallback(async () => {
    if (!resumeFile || jobDescription.trim().length < 80 || status === "analyzing") return;
    setStatus("analyzing");
    setErrorMessage("");
    try {
      const result = await analyzeResume(resumeFile, jobDescription);
      setAnalysis(result);
      setStatus("done");
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : "Something went wrong. Please try again.");
      setStatus("error");
    }
  }, [resumeFile, jobDescription, status]);

  const reset = useCallback(() => {
    setAnalysis(null);
    setStatus("idle");
    setResumeFile(null);
    setJobDescription("");
    if (fileInputRef.current) fileInputRef.current.value = "";
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  useEffect(() => {
    if (status === "done") resultsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
  }, [status]);

  const canAnalyze = resumeFile !== null && jobDescription.trim().length >= 80 && status !== "analyzing";

  const required = analysis?.skills.filter((s) => s.requirement === "required") ?? [];
  const preferred = analysis?.skills.filter((s) => s.requirement === "preferred") ?? [];
  const stats = useMemo(() => {
    if (!analysis) return null;
    const all = analysis.skills;
    return {
      matched: all.filter((s) => s.status === "matched").length,
      partial: all.filter((s) => s.status === "partial").length,
      missing: all.filter((s) => s.status === "missing").length,
    };
  }, [analysis]);

  /* --- recommendation deck cards, filtered by tab --- */
  const recTabs: DeckTab[] = useMemo(() => {
    if (!analysis) return [];
    const recs = analysis.recommendations;
    const count = (pred: (r: (typeof recs)[number]) => boolean) => recs.filter(pred).length;
    return [
      { id: "all", label: "All actions", count: recs.length },
      { id: "learn", label: "Close gaps", count: count((r) => r.type === "learn") },
      { id: "rewrite", label: "Rewrite", count: count((r) => r.type === "rewrite") },
    ];
  }, [analysis]);

  const recCards = useMemo(() => {
    if (!analysis) return [];
    const filtered = analysis.recommendations.filter(
      (r) => recTab === "all" || r.type === recTab
    );
    return filtered.map((rec, i) => (
      <article className="action-card" key={`${recTab}-${i}`}>
        <div className="action-card-head">
          <span className={`action-tag tag-${rec.type}`}>
            {rec.type === "learn" ? "CLOSE THE GAP" : rec.type === "rewrite" ? "REWRITE" : rec.type.toUpperCase()}
          </span>
          <span className="action-index">{String(i + 1).padStart(2, "0")}</span>
        </div>
        <h4 className="action-title">{rec.title}</h4>
        <p className="action-detail">{rec.detail}</p>
        {rec.evidence
          ? <blockquote className="action-evidence">“{rec.evidence}”</blockquote>
          : <p className="action-note">No evidence line exists yet — that’s the point of this card.</p>}
      </article>
    ));
  }, [analysis, recTab]);

  /* --- interview map deck cards, filtered by tab --- */
  const mapTabs: DeckTab[] = useMemo(() => {
    if (!analysis) return [];
    const probes = analysis.interview_map;
    const count = (r: string) => probes.filter((p) => p.readiness === r).length;
    return [
      { id: "all", label: "All probes", count: probes.length },
      { id: "exposed", label: "Exposed", count: count("exposed") },
      { id: "thin", label: "Thin", count: count("thin") },
      { id: "strong", label: "Ready", count: count("strong") },
    ];
  }, [analysis]);

  const mapCards = useMemo(() => {
    if (!analysis) return [];
    const filtered = analysis.interview_map.filter(
      (p) => mapTab === "all" || p.readiness === mapTab
    );
    return filtered.map((probe, i) => (
      <article className={`probe-card probe-${probe.readiness}`} key={`${mapTab}-${i}`}>
        <div className="probe-card-head">
          <span className="probe-badge">{probe.readiness}</span>
          <span className="probe-target">{probe.targets}</span>
        </div>
        <p className="probe-question">{probe.question}</p>
        {probe.grounded_in && <blockquote className="probe-grounded">“{probe.grounded_in}”</blockquote>}
        <p className="probe-why">{probe.why}</p>
      </article>
    ));
  }, [analysis, mapTab]);

  return (
    <div className="app">
      {/* ======================= NAV ======================= */}
      <nav className="navbar">
        <div className="nav-inner">
          <a className="logo" href="/" aria-label="ResumeIQ home">
            <span className="logo-mark" aria-hidden="true">✦</span>
            <span className="logo-word">ResumeIQ</span>
            <span className="logo-sub">Evidence-grounded analysis</span>
          </a>
          <div className="nav-right">
            <span className="nav-pill" title="Resume text is processed in memory and discarded — never stored, never logged.">
              <span className="nav-pill-dot" />Local-first · nothing stored
            </span>
            <a className="nav-link" href="#method">Method</a>
          </div>
        </div>
      </nav>

      {/* ======================= HERO ======================= */}
      <header className="hero">
        <div className="hero-inner">
          <div className="hero-copy">
            <p className="eyebrow"><span className="eyebrow-rule" />CAREER LENS — EVIDENCE OVER ADJECTIVES</p>
            <h1 className="hero-title">See the resume<br />the way an <em>interviewer</em> reads it.</h1>
            <p className="hero-sub">
              ResumeIQ scores your resume against a specific job description — then shows the evidence behind
              every claim, the gaps you can fix tonight, and the questions you’ll be asked on Monday.
            </p>
            <ul className="hero-points">
              <li><b>Quoted, not vibes.</b> Every match cites your resume, verbatim.</li>
              <li><b>Deterministic scoring.</b> Same resume + same JD → same result, always.</li>
              <li><b>The interview map.</b> The probes this score will trigger, and where you’re exposed.</li>
            </ul>
          </div>

          <aside className="hero-ticket" aria-hidden="true">
            <p className="ticket-kicker">SAMPLE VERDICT</p>
            <div className="ticket-score"><span>72</span><small>/100 · Moderate to strong alignment</small></div>
            <div className="ticket-rows">
              <div><span>Required skills</span><i><b style={{ width: "66%" }} /></i></div>
              <div><span>Experience</span><i><b style={{ width: "100%" }} /></i></div>
              <div><span>Responsibilities</span><i><b style={{ width: "44%" }} /></i></div>
            </div>
            <div className="ticket-foot">
              <span className="ticket-chip ok">5 matched</span>
              <span className="ticket-chip warn">2 thin</span>
              <span className="ticket-chip bad">3 exposed</span>
            </div>
            <p className="ticket-note">Illustrative — your report is generated from your own files, on your machine.</p>
          </aside>
        </div>
      </header>

      {/* ======================= WORKSPACE ======================= */}
      <main className="workspace" id="method">
        <section className="work-card">
          <div className="work-head">
            <div>
              <h2 className="work-title">Analyze your resume</h2>
              <p className="work-sub">Two inputs. One honest answer.</p>
            </div>
            <span className="work-step">{status === "done" ? "RESULT" : status === "analyzing" ? "WORKING…" : "STEP 01 / 01"}</span>
          </div>

          {status !== "done" && (
            <div className="work-body">
              {status === "analyzing" ? (
                <LoadingStages />
              ) : (
                <>
                  <div className="form-grid">
                    <div className="field">
                      <div className="field-label-row">
                        <label htmlFor="jd">JOB DESCRIPTION</label>
                        <span className="field-count">{jobDescription.trim().length} chars {jobDescription.trim().length < 80 && "· min 80"}</span>
                      </div>
                      <textarea
                        id="jd"
                        value={jobDescription}
                        onChange={(e) => setJobDescription(e.target.value)}
                        placeholder="Paste the exact JD you’re targeting — the messier and more specific, the better the verdict…"
                        rows={9}
                      />
                    </div>

                    <div className="field">
                      <span className="field-label">YOUR RESUME</span>
                      <div
                        className={`dropzone${dragging ? " dragging" : ""}${resumeFile ? " has-file" : ""}`}
                        role="button"
                        tabIndex={0}
                        aria-label="Upload resume"
                        onClick={() => fileInputRef.current?.click()}
                        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && fileInputRef.current?.click()}
                        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
                        onDragLeave={() => setDragging(false)}
                        onDrop={onDrop}
                      >
                        <input
                          id="resume"
                          ref={fileInputRef}
                          type="file"
                          accept=".pdf,.docx"
                          hidden
                          onChange={(e) => acceptFile(e.target.files?.[0])}
                        />
                        {resumeFile ? (
                          <>
                            <div className="dz-icon dz-ok">✓</div>
                            <p className="dz-title">{resumeFile.name}</p>
                            <p className="dz-sub">{(resumeFile.size / 1024).toFixed(0)} KB · click to replace</p>
                          </>
                        ) : (
                          <>
                            <div className="dz-icon">↑</div>
                            <p className="dz-title">Drop your resume here, or <span>browse</span></p>
                            <p className="dz-sub">PDF or DOCX · max 5 MB · scans are auto-OCR’d</p>
                          </>
                        )}
                      </div>
                      {fileError && <p className="field-error">{fileError}</p>}
                      <p className="field-foot">Scanned resume? Fine — we OCR it locally.<br />Your file is read in memory and never stored.</p>
                    </div>
                  </div>

                  <button className="cta" disabled={!canAnalyze} onClick={analyze}>
                    Analyze my resume <span aria-hidden="true">→</span>
                  </button>
                  {status === "error" && <p className="field-error centered">{errorMessage}</p>}
                  <p className="cta-note">Deterministic rubric · local or free-tier LLM · PII never leaves the machine in local mode</p>
                </>
              )}
            </div>
          )}

          {/* ======================= RESULTS ======================= */}
          {status === "done" && analysis && (
            <div className="results" ref={resultsRef}>
              {/* Verdict strip */}
              <div className="verdict-strip">
                <ScoreGauge score={analysis.overall_score} verdict={analysis.verdict} />
                <div className="verdict-meta">
                  <p className="verdict-role">{analysis.jd_profile.job_title || "Target role"}{analysis.jd_profile.seniority ? ` · ${analysis.jd_profile.seniority}` : ""}</p>
                  <div className="verdict-chips">
                    {stats && (
                      <>
                        <span className="vchip vchip-ok">{stats.matched} matched</span>
                        <span className="vchip vchip-warn">{stats.partial} partial</span>
                        <span className="vchip vchip-bad">{stats.missing} no evidence</span>
                      </>
                    )}
                  </div>
                  <p className="verdict-disclaimer">{analysis.disclaimer}</p>
                </div>
                <button className="ghost-button" onClick={reset}>Analyze another ↺</button>
              </div>

              {/* Skills + dimensions grid */}
              <div className="results-grid">
                <section className="panel">
                  <div className="panel-head">
                    <h3 className="panel-title">Skills vs the JD</h3>
                    <span className="panel-hint">click a row to see the evidence</span>
                  </div>
                  <div className="skill-legend">
                    <span><i className="dot dot-ok" />Matched — shown in context</span>
                    <span><i className="dot dot-warn" />Partial — listed only</span>
                    <span><i className="dot dot-bad" />No evidence found</span>
                  </div>
                  <div className="skill-columns">
                    <div>
                      <p className="skill-group">REQUIRED <span>{required.length}</span></p>
                      <div className="skill-rows">{required.map((s) => <SkillRow key={`r-${s.skill}`} skill={s} />)}</div>
                    </div>
                    <div>
                      <p className="skill-group">PREFERRED <span>{preferred.length}</span></p>
                      <div className="skill-rows">{preferred.map((s) => <SkillRow key={`p-${s.skill}`} skill={s} />)}</div>
                    </div>
                  </div>
                </section>

                <section className="panel">
                  <div className="panel-head">
                    <h3 className="panel-title">How the score breaks down</h3>
                    <span className="panel-hint">deterministic · configurable</span>
                  </div>
                  <DimensionBars analysis={analysis} />
                  <p className="panel-foot">Weights renormalise when a dimension can’t be assessed (e.g. no experience signal found). The model never computes this — Python does, every time.</p>
                </section>
              </div>

              {/* Swipe decks — the two sections that used to make you scroll forever */}
              <div className="decks-grid">
                <CardDeck
                  title="What to do about it"
                  subtitle="Swipe → — one action at a time"
                  icon="✦"
                  cards={recCards}
                  tabs={recTabs}
                  activeTab={recTab}
                  onTabChange={setRecTab}
                  emptyNote="No actions in this bucket — nice signal."
                />
                <CardDeck
                  title="Interview evidence map"
                  subtitle="The probes this score will trigger"
                  icon="◎"
                  cards={mapCards}
                  tabs={mapTabs}
                  activeTab={mapTab}
                  onTabChange={setMapTab}
                  emptyNote="No probes in this readiness band."
                />
              </div>

              {/* Meta */}
              <details className="meta">
                <summary>How this was computed — request {analysis.meta.request_id}</summary>
                <div className="meta-grid">
                  <div><span>JD extraction</span><b>{analysis.meta.extraction_mode}{analysis.meta.model ? ` · ${analysis.meta.model}` : ""}</b></div>
                  <div><span>Latency</span><b>{analysis.meta.latency_ms.toLocaleString()} ms{analysis.meta.latency_ms < 1500 && " · cache hit"}</b></div>
                  <div><span>Scoring</span><b>Deterministic weighted rubric</b></div>
                  <div><span>Evidence</span><b>Verbatim from your file</b></div>
                </div>
                <p className="meta-copy">
                  Scores are computed by a deterministic, configurable rubric. The model (when used) only locates and
                  phrases the JD’s requirements — it does not invent skills, evidence or the score. Identical resume + JD
                  inputs produce identical output (JD extraction is cached by content hash, temperature 0).
                </p>
              </details>
            </div>
          )}
        </section>

        {/* ======================= METHOD STRIP ======================= */}
        <section className="method-strip">
          <div className="method-cell"><span className="method-num">01</span><b>Parse</b><p>PDF · DOCX · scanned — columns, tables and OCR handled locally.</p></div>
          <div className="method-cell"><span className="method-num">02</span><b>Evidence</b><p>Every requirement matched to a verbatim line — or honestly reported absent.</p></div>
          <div className="method-cell"><span className="method-num">03</span><b>Score</b><p>A deterministic rubric you can audit — same input, same number.</p></div>
          <div className="method-cell"><span className="method-num">04</span><b>Rehearse</b><p>The interview map: what’ll be asked, and where you’re exposed.</p></div>
        </section>

        <footer className="footer">
          <p><b>ResumeIQ</b> — decision support, not a hiring probability. Never use it to make an automated hiring decision.</p>
          <p className="footer-sub">Local-first · evidence-grounded · open rubric · nothing stored</p>
        </footer>
      </main>
    </div>
  );
}

export default App;
