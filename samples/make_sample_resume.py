"""Build samples/sample_resume.pdf, a FICTIONAL resume for testing the crew.

Targets: Technical Program Manager, Public Sector at Scale AI
(https://job-boards.greenhouse.io/scaleai/jobs/4633072005).
Run:  uv run --with reportlab python samples/make_sample_resume.py
"""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

OUT = Path(__file__).resolve().parent / "sample_resume.pdf"
ACCENT = colors.HexColor("#1f3a8a")

name = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=20, leading=24, alignment=TA_CENTER, textColor=ACCENT)
contact = ParagraphStyle("contact", fontName="Helvetica", fontSize=9, leading=12, alignment=TA_CENTER, textColor=colors.HexColor("#444444"))
h2 = ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=11, leading=14, textColor=ACCENT, spaceBefore=9, spaceAfter=2)
body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, leading=12.5)
role = ParagraphStyle("role", fontName="Helvetica-Bold", fontSize=10, leading=13)
meta = ParagraphStyle("meta", fontName="Helvetica-Oblique", fontSize=9, leading=12, textColor=colors.HexColor("#555555"), alignment=2)
bullet = ParagraphStyle("bullet", parent=body, leftIndent=0)

SUMMARY = (
    "Technical Program Manager with 11 years of experience delivering AI/ML and data programs for U.S. defense "
    "and intelligence customers. Former software engineer who has run forward-deployed teams that took computer "
    "vision and generative AI from prototype to accredited production systems. Holds an <b>active TS/SCI clearance "
    "with Full Scope Polygraph</b>. Known for turning ambiguous mission needs into clear plans, using data to align "
    "engineering and operations, and building playbooks that make customer success repeatable."
)

JOBS = [
    ("Senior Technical Program Manager, Defense AI", "Vantage Labs (AI/ML API platform)", "Arlington, VA", "2021 to present", [
        "Lead a 22-person cross-functional team (ML engineering, data operations, solutions) delivering computer vision "
        "object-detection programs for 3 DoD customers, with $38M in total contract value.",
        "Ran the transition of a satellite-imagery detection model from pilot to production on a classified network; "
        "cut analyst triage time by 41% and reached Authority to Operate (ATO) 6 weeks ahead of schedule.",
        "Built the MLOps delivery framework (data labeling QA, model evaluation gates, drift monitoring, retraining "
        "cadence) now used on 9 programs; reduced model release cycle from 10 weeks to 4.",
        "Forward deployed on site about 40% of the time; ran weekly mission reviews with O-6 and GS-15 stakeholders and "
        "kept customer satisfaction at 4.8/5 across 8 quarterly reviews.",
        "Launched a GenAI document-summarization pilot (RAG over 1.2M classified reports) with human-in-the-loop "
        "evaluation; now expanding to 2 additional commands.",
        "Created Python and SQL health dashboards for API usage, labeling throughput and SLA risk. They flagged 3 "
        "at-risk renewals early; all 3 renewed.",
    ]),
    ("Technical Program Manager", "Meridian Federal Systems", "Herndon, VA", "2017 to 2021", [
        "Managed delivery of a video-analytics platform for an intelligence community customer: 5 releases per year, "
        "12 engineers, $14M program.",
        "Introduced data-driven risk tracking (RAID log tied to Jira metrics) that cut late milestones by 35%.",
        "Wrote the customer-onboarding playbook for API integrations, which reduced time-to-first-value for new "
        "government users from 8 weeks to 3.",
        "Partnered with product and engineering on root-cause analysis of model-accuracy regressions in field data.",
    ]),
    ("Software Engineer", "Northgate Analytics", "Reston, VA", "2014 to 2017", [
        "Built Python data pipelines and REST APIs for geospatial analytics used by federal customers.",
        "Containerized services with Docker and set up CI/CD on Jenkins; reduced deployment failures by 60%.",
    ]),
]

SKILLS = [
    ("Program delivery", "Agile/Scrum, SAFe, RAID management, earned value, ATO/RMF process, executive reporting"),
    ("AI / ML", "MLOps lifecycle, computer vision, generative AI and RAG, model evaluation, data labeling QA, human-in-the-loop"),
    ("Technical", "Python, SQL, REST APIs, AWS GovCloud, Docker, Kubernetes, Databricks, Tableau"),
    ("Clearance and travel", "Active TS/SCI with Full Scope Polygraph; willing to travel 50%"),
]

EDU = [
    ("M.S. Computer Science (Machine Learning)", "George Mason University", "2019"),
    ("B.S. Computer Engineering", "Virginia Tech", "2014"),
]
CERTS = "PMP (PMI) | AWS Certified Machine Learning, Specialty | Certified ScrumMaster"


def section(title):
    return [Paragraph(title.upper(), h2), HRFlowable(width="100%", thickness=0.8, color=ACCENT, spaceAfter=4)]


def two_col(left, right, lstyle=role):
    t = Table([[Paragraph(left, lstyle), Paragraph(right, meta)]], colWidths=[4.85 * inch, 1.95 * inch], hAlign="LEFT")
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 0),
                           ("RIGHTPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 1)]))
    return t


story = [
    Paragraph("Jordan Rivera", name),
    Paragraph("Washington, DC | (555) 010-4821 | jordan.rivera@example.com | linkedin.com/in/jordan-rivera-sample", contact),
    Spacer(1, 4),
    *section("Professional Summary"),
    Paragraph(SUMMARY, body),
    *section("Experience"),
]
for title, company, loc, dates, bullets in JOBS:
    story.append(two_col(f"{title}, <font name='Helvetica'>{company}</font>", f"{loc} | {dates}"))
    story.append(ListFlowable([ListItem(Paragraph(b, bullet), leftIndent=10, value="•") for b in bullets],
                              bulletType="bullet", start="•", leftIndent=10, bulletFontSize=8))
    story.append(Spacer(1, 5))
story += section("Skills")
for k, v in SKILLS:
    story.append(Paragraph(f"<b>{k}:</b> {v}", body))
story += section("Education and Certifications")
for degree, school, year in EDU:
    story.append(two_col(f"{degree}, <font name='Helvetica'>{school}</font>", year, body))
story.append(Spacer(1, 3))
story.append(Paragraph(CERTS, body))

SimpleDocTemplate(str(OUT), pagesize=LETTER, leftMargin=0.75 * inch, rightMargin=0.75 * inch,
                  topMargin=0.6 * inch, bottomMargin=0.6 * inch,
                  title="Jordan Rivera - Resume (sample)", author="Fictional sample").build(story)
print(f"Wrote {OUT}")
