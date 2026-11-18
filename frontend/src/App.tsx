import { useCallback, useRef, useState } from "react";
import "./App.css";
import { analyzeResume, type AnalysisResponse, type SkillAssessment } from "./services/api";

const STATUS_LABEL: Record<string, string> = {
  matched: "Matched",
  partial: "Partial",
  missing: "No evidence",
};

function ScoreDial({ score, verdict }: { score: number; verdict: string }) {
  const hue = score >= 70 ? "#34d399" : score >= 45 ? "#fbbf24" : "#f87171";
  return (
    <div className="score-dial">
      <div className="score-number" style={{ color: hue }}>{score}</div>
      <div className="score-outof">/ 100</div>
      <div className="score-verdict">{verdict}</div>
    </div>
  );
}

function DimensionBars({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <div className="dimension-list">
      {analysis.dimensions.map((d) => (
        <div className="dimension" key={d.name}>
          <div className="dimension-head">
            <span>{d.name}</span>
            <span className="dimension-meta">
              {d.score === null ? "n/a" : `${Math.round(d.score)}`}
              <em> · weight {Math.round(d.weight)}%</em>
            </span>
          </div>
          <div className="dimension-track">
            <div
              className="dimension-fill"
              style={{ width: `${d.score ?? 0}%` }}
            />
          </div>
          <p className="dimension-detail">{d.detail}</p>
        </div>
      ))}
    </div>
  );
}

function SkillChip({ skill }: { skill: SkillAssessment }) {
  const [open, setOpen] = useState(false);
  return (
    <div className={`skill-chip skill-${skill.status}`}>
      <button type="button" onClick={() => setOpen((v) => !v)} aria-expanded={open}>
        <span className="skill-dot" />
        {skill.skill}
        <span className="skill-status">{STATUS_LABEL[skill.status]}</span>
        <span className="skill-caret">{open ? "▴" : "▾"}</span>
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

function InterviewMap({ analysis }: { analysis: AnalysisResponse }) {
  const probes = analysis.interview_map;
  if (probes.length === 0) return null;
  const count = (r: string) => probes.filter((p) => p.readiness === r).length;
  return (
    <>
      <h3 className="results-h3">Interview evidence map</h3>
      <p className="map-summary">
        <span className="map-stat map-strong">{count("strong")} ready</span>
        <span className="map-stat map-thin">{count("thin")} thin</span>
        <span className="map-stat map-exposed">{count("exposed")} exposed</span>
        <span className="map-hint">What an interviewer will likely probe, and what they can’t touch.</span>
      </p>
      <ol className="probe-list">
        {probes.map((probe, i) => (
          <li className={`probe probe-${probe.readiness}`} key={i}>
            <div className="probe-head">
              <span className="probe-badge">{probe.readiness}</span>
              <span className="probe-target">{probe.targets}</span>
            </div>
            <p className="probe-question">{probe.question}</p>
            {probe.grounded_in && <blockquote>“{probe.grounded_in}”</blockquote>}
            <p className="probe-why">{probe.why}</p>
          </li>
        ))}
      </ol>
    </>
  );
}

function App() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState("");
  const [dragging, setDragging] = useState(false);
  const [status, setStatus] = useState<"idle" | "analyzing" | "done" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [analysis, setAnalysis] = useState<AnalysisResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    if (fileInputRef.current) fileInputRef.current.value = "";
  }, []);

  const canAnalyze = resumeFile !== null && jobDescription.trim().length >= 80 && status !== "analyzing";

  return (
    <div className="app">
      <nav className="navbar">
        <div className="logo"><span className="logo-icon">✦</span>ResumeIQ</div>
        <span className="nav-label">AI Career Intelligence</span>
      </nav>

      <main className="container">
        <section className="hero">
          <div className="badge">✦ EVIDENCE-GROUNDED AI</div>
          <h1>Your next role starts<br />with <span>better insights.</span></h1>
          <p>Understand how your experience aligns with a specific role.<br />Every claim in your report is tied to evidence in your resume.</p>
        </section>

        <section className="analyzer-card">
          <div className="card-header">
            <div>
              <h2>Analyze your resume</h2>
              <p>Two inputs. Clearer career insights.</p>
            </div>
            <span className="step-label">{status === "done" ? "RESULT" : "STEP 01 / 02"}</span>
          </div>

          {status !== "done" && (
            <>
              <div className="input-section">
                <label htmlFor="jd">JOB DESCRIPTION</label>
                <textarea
                  id="jd"
                  value={jobDescription}
                  onChange={(e) => setJobDescription(e.target.value)}
                  placeholder="Paste the job description you're targeting..."
                  rows={7}
                />
                <div className="input-footer">
                  <span>Minimum 80 characters · include requirements</span>
                  <span>{jobDescription.length} characters</span>
                </div>
              </div>

              <div className="upload-section">
                <label htmlFor="resume">YOUR RESUME</label>
                <div
                  className={`upload-box${dragging ? " dragging" : ""}${resumeFile ? " has-file" : ""}`}
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
                      <div className="upload-icon">✓</div>
                      <p><strong>{resumeFile.name}</strong></p>
                      <small>{(resumeFile.size / 1024).toFixed(0)} KB · click to replace</small>
                    </>
                  ) : (
                    <>
                      <div className="upload-icon">↑</div>
                      <p>Drop your resume here or <span>browse files</span></p>
                      <small>PDF or DOCX · Maximum 5 MB</small>
                    </>
                  )}
                </div>
                {fileError && <p className="field-error">{fileError}</p>}
              </div>

              <button className="analyze-button" disabled={!canAnalyze} onClick={analyze}>
                {status === "analyzing" ? "Analyzing your resume…" : "Analyze my resume"} <span>→</span>
              </button>

              {status === "analyzing" && (
                <p className="analyzing-note">Extracting evidence and scoring against the JD…<br />First run may take up to a minute with a local model.</p>
              )}
              {status === "error" && <p className="field-error">{errorMessage}</p>}

              <p className="privacy-note">🔒 Your resume is processed in memory and never stored.</p>
            </>
          )}

          {status === "done" && analysis && (
            <div className="results">
              <div className="results-top">
                <ScoreDial score={analysis.overall_score} verdict={analysis.verdict} />
                <div className="results-side">
                  <p className="jd-title">{analysis.jd_profile.job_title || "Target role"} · {analysis.jd_profile.seniority}</p>
                  <DimensionBars analysis={analysis} />
                </div>
              </div>

              <div className="disclaimer">ℹ️ {analysis.disclaimer}</div>

              <h3 className="results-h3">Skills vs requirements</h3>
              <div className="skill-legend">
                <span><i className="dot-matched" />Matched — demonstrated in context</span>
                <span><i className="dot-partial" />Partial — listed, not shown</span>
                <span><i className="dot-missing" />No evidence found</span>
              </div>
              <div className="skill-groups">
                <div>
                  <p className="skill-group-label">REQUIRED</p>
                  <div className="skill-chips">
                    {analysis.skills.filter((s) => s.requirement === "required").map((s) => <SkillChip key={`r-${s.skill}`} skill={s} />)}
                  </div>
                </div>
                <div>
                  <p className="skill-group-label">PREFERRED</p>
                  <div className="skill-chips">
                    {analysis.skills.filter((s) => s.requirement === "preferred").map((s) => <SkillChip key={`p-${s.skill}`} skill={s} />)}
                  </div>
                </div>
              </div>

              <h3 className="results-h3">What to do about it</h3>
              <ul className="recommendations">
                {analysis.recommendations.map((rec, i) => (
                  <li key={i} className={`rec rec-${rec.type}`}>
                    <div className="rec-head"><span className="rec-tag">{rec.type}</span>{rec.title}</div>
                    <p>{rec.detail}</p>
                    {rec.evidence && <blockquote>“{rec.evidence}”</blockquote>}
                  </li>
                ))}
                {analysis.recommendations.length === 0 && <p className="muted">No gaps detected by the current rubric.</p>}
              </ul>

              <InterviewMap analysis={analysis} />

              <details className="meta">
                <summary>How this was computed</summary>
                <p>
                  JD extraction mode: <strong>{analysis.meta.extraction_mode}</strong>{analysis.meta.model ? ` (${analysis.meta.model})` : ""} ·
                  {" "}Latency: {analysis.meta.latency_ms} ms · Request: {analysis.meta.request_id}<br />
                  Evidence is quoted verbatim from your uploaded file. Scores are computed by a
                  deterministic, configurable rubric — the model (when used) only locates and phrases
                  requirements; it does not invent the score.
                </p>
              </details>

              <button className="analyze-button secondary" onClick={reset}>Analyze another resume <span>↺</span></button>
            </div>
          )}
        </section>

        <footer>
          ResumeIQ <span>Built to make career decisions clearer.</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
