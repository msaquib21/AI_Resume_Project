import { useEffect, useState } from "react";

const STEPS = [
  { label: "Reading your resume", detail: "Extracting text, tables and columns — OCR kicks in automatically for scans" },
  { label: "Understanding the job description", detail: "Separating must-haves from nice-to-haves, seniority and degrees" },
  { label: "Matching evidence", detail: "Every requirement checked against verbatim lines in your resume" },
  { label: "Scoring the rubric", detail: "Deterministic weights — never sampled from a model's mood" },
  { label: "Building your interview map", detail: "The exact probes this score will trigger — anchored to your own lines" },
];

const TIPS = [
  "Same resume + same JD = same result, every time. Scoring is deterministic; identical inputs are served from cache.",
  "Green never means “hired”. It means the evidence exists — quoted word for word.",
  "No evidence does not mean missing skill — it means nothing in writing proves it yet.",
  "The interview map is built from the same evidence the score uses — no separate guesswork.",
  "Your resume never leaves memory here: nothing is stored, logged or sent anywhere else.",
];

/** Staged, honest-looking progress while the (single) backend call runs. */
export default function LoadingStages() {
  const [step, setStep] = useState(0);
  const [tip, setTip] = useState(0);
  const [seconds, setSeconds] = useState(0);

  useEffect(() => {
    const timings = [700, 1500, 3200, 5200, 7500]; // last step holds until the response lands
    const timers = timings.map((t, i) => window.setTimeout(() => setStep(() => Math.min(i + 1, STEPS.length - 1)), t));
    const tipTimer = window.setInterval(() => setTip((v) => (v + 1) % TIPS.length), 4200);
    const clock = window.setInterval(() => setSeconds((s) => s + 1), 1000);
    return () => {
      timers.forEach(window.clearTimeout);
      window.clearInterval(tipTimer);
      window.clearInterval(clock);
    };
  }, []);

  const progress = Math.min(94, ((step + 0.72) / STEPS.length) * 100);

  return (
    <div className="loading" role="status" aria-live="polite">
      <div className="loading-orbit" aria-hidden="true">
        <span className="orbit-ring" />
        <span className="orbit-core">✦</span>
      </div>

      <div className="loading-body">
        <div className="loading-topline">
          <span className="loading-kicker">ANALYZING</span>
          <span className="loading-clock">{seconds.toFixed(0)}s elapsed</span>
        </div>

        <ol className="loading-steps">
          {STEPS.map((s, i) => {
            const state = i < step ? "done" : i === step ? "current" : "pending";
            return (
              <li key={i} className={`loading-step ${state}`}>
                <span className="ls-icon" aria-hidden="true">
                  {state === "done" ? "✓" : state === "current" ? <span className="ls-pulse" /> : "·"}
                </span>
                <span className="ls-text">
                  <span className="ls-label">{s.label}</span>
                  {state === "current" && <span className="ls-detail">{s.detail}</span>}
                </span>
              </li>
            );
          })}
        </ol>

        <div className="loading-bar" aria-hidden="true">
          <span style={{ width: `${progress}%` }} />
        </div>

        <p className="loading-tip" key={tip}><span>✦</span>{TIPS[tip]}</p>
      </div>
    </div>
  );
}
