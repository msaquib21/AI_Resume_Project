"""
Curated skill lexicon used by the deterministic extractor and as a
sanity filter for LLM output.

Deliberately small and reviewable (~200 terms). A missing term does not
break anything — it surfaces as "missing"/no-evidence, never as a crash.
Extend via pull request with evidence from real JDs, not by dumping a
giant keyword list.
"""

SKILL_LEXICON = [
    # Product management & strategy
    "product management", "product strategy", "product discovery", "roadmapping",
    "roadmap", "go-to-market", "product lifecycle", "product requirements",
    "prd", "user stories", "backlog grooming", "prioritisation", "prioritization",
    "requirements gathering", "stakeholder management", "cross-functional",
    "market research", "competitive analysis", "product analytics",
    "product-market fit", "okrs", "kpis", "north star metric",

    # Research & experimentation
    "user research", "user interviews", "usability testing", "a/b testing",
    "ab testing", "experimentation", "hypothesis testing", "surveys",
    "ethnography", "persona", "journey mapping",

    # Data & analytics
    "sql", "python", "r", "excel", "spreadsheets", "tableau", "power bi",
    "looker", "mixpanel", "amplitude", "google analytics", "adobe analytics",
    "data analysis", "data visualization", "a/b test analysis", "statistics",
    "ab testing", "cohort analysis", "funnel analysis", "segmentation",

    # AI / ML
    "machine learning", "deep learning", "generative ai", "llm", "llms",
    "rag", "retrieval augmented generation", "langchain", "langgraph",
    "vector database", "embeddings", "prompt engineering", "fine-tuning",
    "nlp", "natural language processing", "computer vision", "pytorch",
    "tensorflow", "scikit-learn", "model evaluation", "mlops",
    "hugging face", "openai", "ollama", "anthropic", "vector search",

    # Engineering & tools
    "javascript", "typescript", "react", "node", "node.js", "fastapi",
    "django", "flask", "java", "c++", "c#", "go", "golang", "rust",
    "rest api", "apis", "graphql", "git", "github", "docker", "kubernetes",
    "aws", "azure", "gcp", "cloud", "ci/cd", "linux", "agile", "scrum",
    "kanban", "jira", "confluence", "notion", "figma",

    # Business & operations (Indian market context included)
    "program management", "project management", "pmo", "process improvement",
    "operations", "p&l", "budgeting", "vendor management", "procurement",
    "business development", "sales", "crm", "salesforce", "strategy",
    "consulting", "financial modeling", "forecasting", "supply chain",

    # Communication & leadership
    "communication", "presentation", "storytelling", "executive communication",
    "leadership", "mentoring", "team management", "negotiation",
    "cross-functional collaboration", "stakeholder alignment",
]

# Canonical synonyms — merged so the SAME skill never appears twice under
# different surface forms ("node" vs "node.js", "llm" vs "llms").
SKILL_CANONICAL = {
    "node.js": "node",
    "llms": "llm",
    "ab testing": "a/b testing",
    "a/b test": "a/b testing",
    "golang": "go",
    "js": "javascript",
    "ts": "typescript",
    "k8s": "kubernetes",
    "gen ai": "generative ai",
    "genai": "generative ai",
    "large language model": "llm",
    "large language models": "llm",
    "rag systems": "rag",
    "retrieval augmented generation": "rag",
    "rest apis": "apis",
    "rest api": "apis",
    "ci cd": "ci/cd",
    "powerbi": "power bi",
}

# Common ways requirements get phrased — all map to the canonical term.
# Without this, "user interviews" looked like zero evidence of user research.
SKILL_ALIASES = {
    "llm": ["llms", "large language model", "large language models"],
    "user research": ["user interviews", "usability study", "customer interviews", "user testing"],
    "roadmapping": ["roadmap"],
    "a/b testing": ["ab test", "ab testing", "split test"],
    "product discovery": ["discovery"],
    "user stories": ["user story"],
    "machine learning": ["ml"],
    "generative ai": ["gen ai", "genai"],
    "stakeholder management": ["stakeholder alignment"],
    "git": ["github", "gitlab", "version control"],
    "cohort analysis": ["cohort reporting", "cohort behaviour", "cohort behavior"],
    "product requirements": ["defining requirements", "writing requirements", "wrote requirements", "requirements"],
    "apis": ["rest apis", "api design"],
}

# Degree keywords — used for the qualifications dimension.
DEGREE_KEYWORDS = [
    "bachelor", "b.tech", "b.e.", "bsc", "b.com", "bba", "b.a.",
    "master", "mba", "m.tech", "msc", "m.com", "ms",
    "phd", "doctorate", "degree", "diploma",
]
