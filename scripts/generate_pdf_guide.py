import os
import sys
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)

ROOT = Path(__file__).resolve().parent
PDF_PATH = ROOT / "PROJECT_EXPLANATION_GUIDE.pdf"


def build_pdf():
    doc = SimpleDocTemplate(
        str(PDF_PATH),
        pagesize=letter,
        rightMargin=45,
        leftMargin=45,
        topMargin=45,
        bottomMargin=45,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#1e293b"),
        alignment=1,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#475569"),
        alignment=1,
    )

    h1_style = ParagraphStyle(
        "SectionHeading1",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=14,
        spaceAfter=6,
    )

    h2_style = ParagraphStyle(
        "SectionHeading2",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0284c7"),
        spaceBefore=10,
        spaceAfter=4,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        spaceAfter=5,
    )

    bullet_style = ParagraphStyle(
        "BulletText",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    speech_style = ParagraphStyle(
        "SpeechQuote",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b"),
        leftIndent=15,
        rightIndent=15,
        spaceBefore=4,
        spaceAfter=6,
    )

    badge_a = ParagraphStyle(
        "BadgeA",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#0284c7"),
    )

    badge_b = ParagraphStyle(
        "BadgeB",
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#16a34a"),
    )

    story = []

    # Title & Header
    story.append(Paragraph("AI-Driven AWS Cloud Architecture Recommender", title_style))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "<b>Comprehensive Project Explanation & Presentation Guide</b><br/>"
            "Cloud Architecture Design (VIT) | Guide: Dr. Sunija A P<br/>"
            "<b>Person A:</b> Sudipta Majumder (24BCE2882) &nbsp;|&nbsp; <b>Person B:</b> P. Giphy Bershan (24BCE2201)",
            subtitle_style,
        )
    )
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#cbd5e1"), spaceAfter=10))

    # SECTION 1: WHAT THE ENTIRE PROJECT IS DOING
    story.append(Paragraph("1. High-Level Overview: What the System Does", h1_style))
    story.append(
        Paragraph(
            "The <b>AI-Driven AWS Cloud Architecture Design & Recommendation System</b> is an intelligent, "
            "recommendation-only decision-support tool. It takes an open-ended, plain English description of an "
            "application (e.g. <i>'A highly available e-commerce platform for ~100k users'</i>) and automatically transforms it into an "
            "end-to-end, production-grade cloud recommendation.",
            body_style,
        )
    )
    story.append(Spacer(1, 4))

    # Core Pipeline Table
    pipeline_data = [
        [
            Paragraph("<b>Stage</b>", body_style),
            Paragraph("<b>Component</b>", body_style),
            Paragraph("<b>Technology</b>", body_style),
            Paragraph("<b>Nature</b>", body_style),
        ],
        [
            Paragraph("<b>1. Requirement Parsing</b>", body_style),
            Paragraph("Extracts technical attributes (traffic, availability, budget)", body_style),
            Paragraph("Amazon Bedrock (LLM)", body_style),
            Paragraph("Probabilistic (AI)", body_style),
        ],
        [
            Paragraph("<b>2. Architecture Reasoning</b>", body_style),
            Paragraph("Selects reference pattern and catalogue-bounded services", body_style),
            Paragraph("Amazon Bedrock (LLM)", body_style),
            Paragraph("Probabilistic (AI)", body_style),
        ],
        [
            Paragraph("<b>3. Graph Validation</b>", body_style),
            Paragraph("Audits allow-lists, connection rules & detects orphans", body_style),
            Paragraph("jsonschema + Python", body_style),
            Paragraph("Deterministic (Code)", body_style),
        ],
        [
            Paragraph("<b>4. Diagram Rendering</b>", body_style),
            Paragraph("Renders visual architecture diagram with official AWS icons", body_style),
            Paragraph("Python diagrams.aws + DOT", body_style),
            Paragraph("Deterministic (Code)", body_style),
        ],
        [
            Paragraph("<b>5. Cost Estimation</b>", body_style),
            Paragraph("Calculates monthly low/high cost in ap-south-1", body_style),
            Paragraph("Catalogue Pricing Model", body_style),
            Paragraph("Deterministic (Code)", body_style),
        ],
        [
            Paragraph("<b>6. Security Review</b>", body_style),
            Paragraph("Audits 15 rules across Well-Architected Framework pillars", body_style),
            Paragraph("Rule-based Audit Engine", body_style),
            Paragraph("Deterministic (Code)", body_style),
        ],
    ]

    t_pipe = Table(pipeline_data, colWidths=[120, 185, 120, 95])
    t_pipe.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(t_pipe)
    story.append(Spacer(1, 6))

    story.append(
        Paragraph(
            "<b>Key Engineering Principle:</b> <i>'LLMs for language understanding; deterministic code for math, security, and graphics.'</i> "
            "Crucially, the system is <b>recommendation-only</b>: it never executes AWS CLI commands or deploys live infrastructure, ensuring 100% "
            "safety against accidental infrastructure charges or misconfigurations.",
            body_style,
        )
    )
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

    # SECTION 2: PERSON A RESPONSIBILITIES
    story.append(Paragraph("2. Person A Guide: Sudipta Majumder (AI Core & Pipeline)", h1_style))
    story.append(
        Paragraph(
            "Person A owns the <b>intelligence layer, schemas, prompts, guardrails, and evaluation</b>. "
            "Files owned: <code>parser.py</code>, <code>reasoner.py</code>, <code>llm.py</code>, <code>validator.py</code>, "
            "<code>schemas/</code>, <code>catalogue/</code>, <code>prompts/</code>, <code>eval/</code>.",
            body_style,
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>A. Exactly What Sudipta Built:</b>", h2_style))
    story.append(
        Paragraph(
            "• <b>Bedrock LLM Wrapper (<code>llm.py</code>):</b> Dynamic configuration reading <code>BEDROCK_MODEL_ID</code> and "
            "<code>AWS_REGION</code> from <code>.env</code>. Actionable exception handling for AccessDenied, throttling, and timeouts. "
            "Model-keyed on-disk cache (<code>.cache/</code>) and real-time token tracking to display exact prompt token metrics on slides.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Prompt Engineering & Few-Shot Injection (<code>parser.py</code>, <code>reasoner.py</code>):</b> "
            "Loaded 4 comprehensive few-shot examples (3-tier web, serverless REST, static CDN, batch pipeline). "
            "Prompt injection defense wrapping user inputs in <code>&lt;user_requirement&gt;</code> tags. Automated 2-step schema repair-and-retry.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Offline Demo Safety Net (<code>examples/</code>, <code>run.py</code>):</b> 3 complete cached offline test cases "
            "(<code>ecommerce</code>, <code>serverless_api</code>, <code>static_site</code>) allowing full demo execution without AWS/Internet.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Evaluation Benchmark Harness (<code>eval/run_eval.py</code>):</b> Quantitative metric calculation: Service Selection Accuracy "
            "(100%), Precision (100%), Pattern Match % (100%), and Architecture Validity (100%) against ground-truth blueprints.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Scenario Syntax Checker (<code>eval/check_scenarios.py</code>):</b> Shared checker validating ground-truth scenarios.",
            bullet_style,
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>B. Sudipta's Presentation Speech (What to say during presentation):</b>", h2_style))
    story.append(
        Paragraph(
            "<i>\"Good morning. I am Sudipta Majumder, and I developed the AI Core and validation pipeline. "
            "When designing with LLMs, the primary hazard is hallucination—models invent fake AWS services or wire invalid networks. "
            "To solve this, I designed a two-stage pipeline strictly constrained by JSON Schema contracts. First, my Requirement Parser extracts structured attributes "
            "while treating user text inside &lt;user_requirement&gt; tags as untrusted data to neutralize prompt injection attacks. "
            "Second, my Reasoning Engine maps requirements strictly to our curated catalogue.yaml. If an LLM attempts to connect an ALB directly to S3 or invent a database, "
            "our validator intercepts and rejects it immediately. Finally, I built an automated evaluation harness in eval/run_eval.py that measures 100% service recall "
            "and 100% precision against official AWS reference blueprints.\"</i>",
            speech_style,
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>C. Questions Examiners May Ask Sudipta:</b>", h2_style))
    story.append(
        Paragraph(
            "<b>Q: Why two separate LLM calls instead of one single prompt?</b><br/>"
            "<i>Answer: Single-prompt generation suffers from task overload. Splitting into parsing and reasoning enforces modularity, schema-bound boundaries, and higher accuracy.</i>",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Q: How do you prevent prompt injection?</b><br/>"
            "<i>Answer: User text is quarantined in XML delimiters and explicitly instructed as passive untrusted data, verified by automated security injection tests.</i>",
            bullet_style,
        )
    )
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=10))

    # SECTION 3: PERSON B RESPONSIBILITIES
    story.append(Paragraph("3. Person B Guide: P. Giphy Bershan (Downstream, Infra & UI)", h1_style))
    story.append(
        Paragraph(
            "Person B owns the <b>deterministic analysis, pricing, diagramming, deployment architecture, and UI</b>. "
            "Files owned: <code>diagram.py</code>, <code>cost.py</code>, <code>security.py</code>, <code>app/</code>, "
            "<code>scripts/</code>, deployment guides.",
            body_style,
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>A. Exactly What Giphy Built:</b>", h2_style))
    story.append(
        Paragraph(
            "• <b>Deterministic Diagram Renderer (<code>diagram.py</code>):</b> Generates production architecture diagrams using "
            "<code>diagrams.aws.*</code> iconography, clustered logically by category (Compute, Network, Storage, Database), with automated Graphviz DOT fallback.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Well-Architected Security Auditor (<code>security.py</code>):</b> Evaluates 15 deterministic checks across Security, "
            "Reliability, Cost Optimization, and Operational Excellence (flagging public S3, missing TLS, missing Multi-AZ, etc.).",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Regional Cost Estimator (<code>cost.py</code>):</b> Computes monthly low/high cost ranges based on ap-south-1 prices and explicit usage assumptions.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>System Deployment Architecture:</b> Designed the serverless hosting stack for our own application: S3 + CloudFront (SPA), "
            "API Gateway HTTP API, Lambda, Bedrock API, and DynamoDB ($0 idle operational cost in Free Tier).",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "• <b>Streamlit Interactive Interface (<code>app/streamlit_app.py</code>):</b> Web application featuring Services, Diagram PNG, "
            "Cost breakdown, Security checks tabs, and an offline Demo Mode toggle.",
            bullet_style,
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>B. Giphy's Presentation Speech (What to say during presentation):</b>", h2_style))
    story.append(
        Paragraph(
            "<i>\"Good morning. I am P. Giphy Bershan, and I developed the downstream analysis, cloud deployment architecture, and user interface. "
            "Once Sudipta's AI core produces a validated Architecture JSON, my downstream modules execute deterministically with zero additional LLM costs. "
            "My diagram module parses the JSON graph into clusters and maps official AWS icons via the Python diagrams library. "
            "My security module audits the design against 15 Well-Architected rules, flagging issues like unencrypted storage or missing multi-AZ redundancy. "
            "Finally, our system's own deployment uses a completely serverless stack—S3, CloudFront, API Gateway, and Lambda—which costs literally zero dollars at idle "
            "within the AWS Free Tier, with Bedrock token charges totaling under $10 a month.\"</i>",
            speech_style,
        )
    )
    story.append(Spacer(1, 4))

    story.append(Paragraph("<b>C. Questions Examiners May Ask Giphy:</b>", h2_style))
    story.append(
        Paragraph(
            "<b>Q: Why not let the LLM draw the diagram in Mermaid or SVG?</b><br/>"
            "<i>Answer: Published benchmarks (DiagramAI 2025) prove LLMs suffer high syntax and alignment error rates when drawing directly. Using deterministic code on structured JSON guarantees 100% syntactically valid diagrams.</i>",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Q: Why is the system strictly recommendation-only?</b><br/>"
            "<i>Answer: Autonomous deployment introduces severe financial and operational hazards. An LLM mistake could provision expensive GPU clusters or create open security holes. Cloud governance mandates human review.</i>",
            bullet_style,
        )
    )

    doc.build(story)
    print(f"PDF successfully generated at: {PDF_PATH}")


if __name__ == "__main__":
    build_pdf()
