const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type SkillStatus = "matched" | "partial" | "missing";
export type Requirement = "required" | "preferred";

export interface SkillAssessment {
  skill: string;
  requirement: Requirement;
  status: SkillStatus;
  evidence: string;
  note: string;
}

export interface DimensionScore {
  name: string;
  score: number | null;
  weight: number;
  detail: string;
}

export interface Recommendation {
  type: "surface" | "rewrite" | "learn" | "clarify";
  title: string;
  detail: string;
  evidence: string;
}

export interface JDProfile {
  job_title: string;
  seniority: string;
  required_skills: string[];
  preferred_skills: string[];
  responsibilities: string[];
  qualifications: string[];
}

export interface AnalysisMeta {
  request_id: string;
  extraction_mode: "llm" | "deterministic";
  model: string | null;
  latency_ms: number;
}

export interface AnalysisResponse {
  filename: string;
  overall_score: number;
  verdict: string;
  disclaimer: string;
  dimensions: DimensionScore[];
  skills: SkillAssessment[];
  jd_profile: JDProfile;
  gaps: { critical: string[]; important: string[]; optional: string[]; presentation: string[] };
  recommendations: Recommendation[];
  meta: AnalysisMeta;
}

export async function analyzeResume(resume: File, jdText: string): Promise<AnalysisResponse> {
  const form = new FormData();
  form.append("file", resume);
  form.append("jd_text", jdText);

  const response = await fetch(`${API_BASE}/api/analyze`, { method: "POST", body: form });
  if (!response.ok) {
    let message = `Analysis failed (HTTP ${response.status}).`;
    try {
      const body = await response.json();
      if (body?.detail) message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      /* keep default message */
    }
    throw new Error(message);
  }
  return (await response.json()) as AnalysisResponse;
}
