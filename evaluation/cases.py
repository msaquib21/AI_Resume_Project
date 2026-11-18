"""
Hand-labeled development cases for ResumeIQ evaluation.

These are synthetic-but-realistic resumes written for this project.
Labels reflect a human reviewer's judgment of what *this* resume shows,
given a strict standard: "listed in a skills section" = partial,
"demonstrated in context" = matched, "no evidence" = missing.

Not ground truth about hiring — only about evidence in the text.
Replace/extend with real (consented, anonymised) samples before any
public accuracy claim. Scores here calibrate, they don't market.
"""

CASES = [
    {
        "id": "apm_moderate",
        "jd": open("evaluation/sample_jd.txt", encoding="utf-8").read(),
        "resume": open("evaluation/sample_resume.txt", encoding="utf-8").read(),
        "expected_required": {
            "sql": "matched",
            "python": "matched",
            "experimentation": "matched",
            "cohort analysis": "matched",
            "user stories": "matched",
            "product discovery": "partial",
            "user research": "partial",
            "a/b testing": "missing",
        },
        "expect_score_range": (30, 75),
    },
    {
        "id": "apm_strong",
        "jd": open("evaluation/sample_jd.txt", encoding="utf-8").read(),
        "resume": """Priya Nair
priya.nair@example.com

EXPERIENCE
- Ran A/B testing programme across onboarding flows; lifted activation by 18% over 4 experiments
- Wrote SQL and Python to model cohort behaviour for 3 product squads
- Led product discovery with 25 user interviews, 6 usability testing sessions
- Defined requirements and wrote user stories for a self-serve analytics launch
- Built roadmapping cadence with engineering; shipped discovery findings in 2 quarters
EXPERIENCE HIGHLIGHTS (years of experience: 2)

EDUCATION: B.Tech, Electrical Engineering
""",
        "expected_required": {
            "sql": "matched",
            "python": "matched",
            "product discovery": "matched",
            "user research": "matched",
            "a/b testing": "matched",
            "roadmapping": "matched",
            "user stories": "matched",
        },
        "expect_score_range": (55, 100),
    },
    {
        "id": "hr_vs_apm",
        "jd": open("evaluation/sample_jd.txt", encoding="utf-8").read(),
        "resume": """Rohit Mehra
rohit.mehra@example.com

EXPERIENCE
- Managed end-to-end recruitment for 120 campus hires
- Ran onboarding and engagement surveys
- Coordinated with hiring managers on JD drafting

SKILLS
HR operations, Interviewing, Excel, Communication
""",
        "expected_required": {
            "sql": "missing",
            "python": "missing",
            "product discovery": "missing",
            "a/b testing": "missing",
            "user research": "missing",
        },
        "expect_score_range": (0, 45),
    },
    {
        "id": "analyst_switcher",
        "jd": open("evaluation/sample_jd.txt", encoding="utf-8").read(),
        "resume": """Divya Krishnan
divya.k@example.com

EXPERIENCE
- Data analyst for telecom pricing; built SQL dashboards for 30+ stakeholders
- Automated retention cohort reporting in Python (pandas), saving 6 hours weekly
- Presented monthly churn reviews to leadership
- Conducted user research synthesis from support tickets to inform pricing pages

SKILLS
SQL, Python, Excel, Tableau

EDUCATION: MBA, Analytics
""",
        "expected_required": {
            "sql": "matched",
            "python": "matched",
            "user research": "matched",
            "a/b testing": "missing",
            "product discovery": "missing",
        },
        "expect_score_range": (25, 70),
    },
]
