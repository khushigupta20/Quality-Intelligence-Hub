"""
Generates a 3-page competition PDF for the Quality Intelligence Hub.
Judges have already received Solution Statement + Technical Statement.
This document focuses on: what makes it impressive, the AI pipeline,
the engineering decisions, SDLC impact, and the before/after story.

Run:  python generate_qih_overview.py
Out:  quality_intelligence_hub_overview.pdf
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak
)
from reportlab.graphics.shapes import Drawing, Rect, String, Line, Polygon
import os

# ── IBM Carbon palette ────────────────────────────────────────────────────────
IBM_BLUE       = colors.HexColor("#0f62fe")
IBM_BLUE_DARK  = colors.HexColor("#0043ce")
IBM_BLUE_LIGHT = colors.HexColor("#edf5ff")
IBM_GRAY_100   = colors.HexColor("#161616")
IBM_GRAY_70    = colors.HexColor("#525252")
IBM_GRAY_20    = colors.HexColor("#e0e0e0")
IBM_GRAY_10    = colors.HexColor("#f4f4f4")
IBM_GREEN      = colors.HexColor("#198038")
IBM_GREEN_LIGHT= colors.HexColor("#defbe6")
IBM_RED        = colors.HexColor("#da1e28")
IBM_RED_LIGHT  = colors.HexColor("#fff1f1")
IBM_PURPLE     = colors.HexColor("#6929c4")
IBM_PURPLE_LIGHT=colors.HexColor("#f6f2ff")
IBM_TEAL       = colors.HexColor("#007d79")
IBM_TEAL_LIGHT = colors.HexColor("#d9fbfb")
WHITE          = colors.white

OUTPUT_FILE = "quality_intelligence_hub_overview.pdf"
PAGE_W, PAGE_H = A4
MARGIN    = 16 * mm
CONTENT_W = PAGE_W - 2 * MARGIN


# ── Page header / footer ──────────────────────────────────────────────────────
def page_decorator(cv, doc):
    cv.saveState()
    w, h = A4
    cv.setFillColor(IBM_BLUE_DARK)
    cv.rect(0, h - 12*mm, w, 12*mm, fill=1, stroke=0)
    cv.setFillColor(WHITE)
    cv.setFont("Helvetica-Bold", 8.5)
    cv.drawString(MARGIN, h - 8*mm, "Quality Intelligence Hub")
    cv.setFillColor(IBM_GRAY_10)
    cv.rect(0, 0, w, 9*mm, fill=1, stroke=0)
    cv.setFillColor(IBM_GRAY_70)
    cv.setFont("Helvetica", 7)
    cv.drawString(MARGIN, 3*mm, "© IBM Corporation — Internal use only. Not for external distribution.")
    cv.drawRightString(w - MARGIN, 3*mm, f"Page {doc.page} of 3")
    cv.restoreState()


# ── Style factory ─────────────────────────────────────────────────────────────
def S():
    base = getSampleStyleSheet()
    def ps(name, **kw):
        return ParagraphStyle(name, parent=base["Normal"], **kw)
    return {
        "h1":      ps("h1",  fontSize=11.5, leading=15, textColor=IBM_BLUE_DARK,
                       fontName="Helvetica-Bold", spaceBefore=5, spaceAfter=2),
        "h2":      ps("h2",  fontSize=9.5,  leading=13, textColor=IBM_GRAY_100,
                       fontName="Helvetica-Bold", spaceBefore=3, spaceAfter=1),
        "body":    ps("body", fontSize=8.5, leading=12.5, textColor=IBM_GRAY_100,
                       fontName="Helvetica", alignment=TA_JUSTIFY, spaceAfter=2),
        "body_sm": ps("body_sm", fontSize=7.8, leading=11, textColor=IBM_GRAY_70,
                       fontName="Helvetica", spaceAfter=2),
        "bullet":  ps("bullet", fontSize=8.5, leading=12, textColor=IBM_GRAY_100,
                       fontName="Helvetica", leftIndent=10, spaceAfter=1),
        "th":      ps("th", fontSize=8, leading=10, textColor=WHITE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
        "td":      ps("td", fontSize=8, leading=10.5, textColor=IBM_GRAY_100,
                       fontName="Helvetica"),
        "td_c":    ps("td_c", fontSize=8, leading=10, textColor=IBM_GRAY_100,
                       fontName="Helvetica", alignment=TA_CENTER),
        "lbl":     ps("lbl", fontSize=7.8, leading=10, textColor=IBM_BLUE_DARK,
                       fontName="Helvetica-Bold", spaceAfter=1),
        "lbl_g":   ps("lbl_g", fontSize=7.8, leading=10, textColor=IBM_GREEN,
                       fontName="Helvetica-Bold", spaceAfter=1),
        "lbl_p":   ps("lbl_p", fontSize=7.8, leading=10, textColor=IBM_PURPLE,
                       fontName="Helvetica-Bold", spaceAfter=1),
        "lbl_t":   ps("lbl_t", fontSize=7.8, leading=10, textColor=IBM_TEAL,
                       fontName="Helvetica-Bold", spaceAfter=1),
        "caption": ps("caption", fontSize=7.5, leading=10, textColor=IBM_GRAY_70,
                       fontName="Helvetica-Oblique", alignment=TA_CENTER, spaceAfter=3),
        "callout": ps("callout", fontSize=9.5, leading=14, textColor=WHITE,
                       fontName="Helvetica-BoldOblique", alignment=TA_CENTER),
        "tag":     ps("tag", fontSize=7.5, leading=10, textColor=IBM_BLUE_DARK,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
        "stat_n":  ps("stat_n", fontSize=18, leading=22, textColor=IBM_BLUE,
                       fontName="Helvetica-Bold", alignment=TA_CENTER),
        "stat_l":  ps("stat_l", fontSize=7.5, leading=10, textColor=IBM_GRAY_70,
                       fontName="Helvetica", alignment=TA_CENTER),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────
def rule(color=IBM_BLUE):
    return HRFlowable(width="100%", thickness=1.2, color=color, spaceAfter=4, spaceBefore=0)

def gap(h=2):
    return Spacer(1, h * mm)

def colored_box(content, bg, border, pad=5):
    t = Table([[content]], colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("BOX",           (0,0),(-1,-1), 0.7, border),
        ("TOPPADDING",    (0,0),(-1,-1), pad),
        ("BOTTOMPADDING", (0,0),(-1,-1), pad),
        ("LEFTPADDING",   (0,0),(-1,-1), 8),
        ("RIGHTPADDING",  (0,0),(-1,-1), 8),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    return t

def grid(data, cw, alt=True):
    ts = [
        ("BACKGROUND",    (0,0),(-1,0), IBM_BLUE),
        ("GRID",          (0,0),(-1,-1), 0.4, IBM_GRAY_20),
        ("TOPPADDING",    (0,0),(-1,-1), 3),
        ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 5),
        ("RIGHTPADDING",  (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]
    if alt:
        for i in range(1, len(data)):
            ts.append(("BACKGROUND",(0,i),(-1,i), WHITE if i%2==1 else IBM_GRAY_10))
    t = Table(data, colWidths=cw, spaceBefore=3)
    t.setStyle(TableStyle(ts))
    return t

def pill(text, bg, fg=WHITE):
    """A small coloured tag cell."""
    t = Table([[Paragraph(text, ParagraphStyle("_p", parent=getSampleStyleSheet()["Normal"],
               fontSize=7, leading=9, textColor=fg, fontName="Helvetica-Bold",
               alignment=TA_CENTER))]],
              colWidths=[26*mm])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), bg),
        ("TOPPADDING",    (0,0),(-1,-1), 2),
        ("BOTTOMPADDING", (0,0),(-1,-1), 2),
        ("LEFTPADDING",   (0,0),(-1,-1), 3),
        ("RIGHTPADDING",  (0,0),(-1,-1), 3),
    ]))
    return t


# ── AI pipeline drawing ───────────────────────────────────────────────────────
def ai_pipeline_drawing():
    """5-stage horizontal pipeline: Upload → Parse → Group → AI Enrich → Report"""
    dw = CONTENT_W
    dh = 38 * mm          # extra height for two-line sub-labels
    d  = Drawing(dw, dh)

    stages = [
        ("Upload\nFile",          IBM_BLUE_LIGHT,  IBM_BLUE,      IBM_BLUE_DARK),
        ("Parse &\nNormalise",    IBM_BLUE_LIGHT,  IBM_BLUE,      IBM_BLUE_DARK),
        ("Group &\nCluster",      IBM_PURPLE_LIGHT,IBM_PURPLE,    IBM_PURPLE),
        ("AI Enrich\n(watsonx)",  IBM_TEAL_LIGHT,  IBM_TEAL,      IBM_TEAL),
        ("PDF\nReport",           IBM_GREEN_LIGHT, IBM_GREEN,     IBM_GREEN),
    ]

    n     = len(stages)
    bw    = (dw - 4*mm) / n - 1*mm
    bh    = 12 * mm
    gap_v = 1 * mm
    my    = dh * 0.60     # shift boxes up slightly to leave room for labels below

    for i, (lbl, fill, stroke, tc) in enumerate(stages):
        x = i * (bw + gap_v + 1*mm)
        y = my - bh/2
        d.add(Rect(x, y, bw, bh, fillColor=fill, strokeColor=stroke, strokeWidth=0.8))
        lines = lbl.split("\n")
        for j, ln in enumerate(lines):
            ty = my + (len(lines)/2 - j - 0.3) * 3.8*mm
            d.add(String(x + bw/2, ty, ln,
                         fontName="Helvetica-Bold", fontSize=6.8,
                         fillColor=tc, textAnchor="middle"))
        if i < n-1:
            ax = x + bw + 0.5*mm
            ex = x + bw + gap_v + 0.5*mm
            d.add(Line(ax, my, ex-2, my, strokeColor=IBM_GRAY_70, strokeWidth=0.8))
            d.add(Polygon([ex-2, my-1.5, ex+1, my, ex-2, my+1.5],
                          fillColor=IBM_GRAY_70, strokeColor=IBM_GRAY_70, strokeWidth=0))

    # Sub-labels below boxes — two short lines each, well separated
    lh = 3.2 * mm   # line height between sub-label rows
    base_y = my - bh/2 - 4*mm

    # Group stage (index 2) — two lines
    gx = 2 * (bw + gap_v + 1*mm) + bw/2
    d.add(String(gx, base_y,        "Semantic (watsonx)",
                 fontName="Helvetica-Oblique", fontSize=5.8,
                 fillColor=IBM_GRAY_70, textAnchor="middle"))
    d.add(String(gx, base_y - lh,   "or keyword fallback",
                 fontName="Helvetica-Oblique", fontSize=5.8,
                 fillColor=IBM_GRAY_70, textAnchor="middle"))

    # AI Enrich stage (index 3) — two lines
    ax2 = 3 * (bw + gap_v + 1*mm) + bw/2
    d.add(String(ax2, base_y,       "Granite-3-8B + Slate-125M",
                 fontName="Helvetica-Oblique", fontSize=5.8,
                 fillColor=IBM_GRAY_70, textAnchor="middle"))
    d.add(String(ax2, base_y - lh,  "or static templates",
                 fontName="Helvetica-Oblique", fontSize=5.8,
                 fillColor=IBM_GRAY_70, textAnchor="middle"))
    return d


# ── Before / After drawing ────────────────────────────────────────────────────
def before_after_drawing():
    dw = CONTENT_W
    dh = 28 * mm
    d  = Drawing(dw, dh)
    half = dw / 2 - 3*mm
    my   = dh / 2

    # BEFORE box
    d.add(Rect(0, 2*mm, half, dh-4*mm, fillColor=IBM_RED_LIGHT,
               strokeColor=IBM_RED, strokeWidth=0.8))
    d.add(String(half/2, dh-6*mm, "BEFORE",
                 fontName="Helvetica-Bold", fontSize=7.5,
                 fillColor=IBM_RED, textAnchor="middle"))
    before_lines = [
        "Manual CSV triage — hours per sprint",
        "Inconsistent RCA across analysts",
        "No requirements AI tooling",
        "Separate tools, no shared login",
        "Static, templated reports",
    ]
    for i, ln in enumerate(before_lines):
        d.add(String(6, dh - 10*mm - i*3.8*mm, "x  " + ln,
                     fontName="Helvetica", fontSize=6.2,
                     fillColor=IBM_RED, textAnchor="start"))

    # Arrow
    cx = dw/2
    d.add(Line(cx-1, my, cx+1, my, strokeColor=IBM_GRAY_20, strokeWidth=0.5))
    d.add(String(cx, my+1.5*mm, ">>",
                 fontName="Helvetica-Bold", fontSize=8,
                 fillColor=IBM_BLUE, textAnchor="middle"))

    # AFTER box
    ax = dw/2 + 3*mm
    d.add(Rect(ax, 2*mm, half, dh-4*mm, fillColor=IBM_GREEN_LIGHT,
               strokeColor=IBM_GREEN, strokeWidth=0.8))
    d.add(String(ax + half/2, dh-6*mm, "AFTER",
                 fontName="Helvetica-Bold", fontSize=7.5,
                 fillColor=IBM_GREEN, textAnchor="middle"))
    after_lines = [
        "Sub-60-second automated analysis + PDF",
        "Consistent, AI-enriched RCA every time",
        "5-task IBM ICA Agent requirements review",
        "Unified login, one interface, one server",
        "AI executive summary in every report",
    ]
    for i, ln in enumerate(after_lines):
        d.add(String(ax+6, dh - 10*mm - i*3.8*mm, "v  " + ln,
                     fontName="Helvetica", fontSize=6.2,
                     fillColor=IBM_GREEN, textAnchor="start"))
    return d


# ══════════════════════════════════════════════════════════════════════════════
# BUILD
# ══════════════════════════════════════════════════════════════════════════════
def build():
    doc = SimpleDocTemplate(
        OUTPUT_FILE, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=17*mm, bottomMargin=14*mm,
        title="Quality Intelligence Hub — Competition Submission",
        author="IBM Quality Engineering",
    )
    st   = S()
    flow = []

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 1 — Cover banner + At a Glance + Before/After + What Makes It Unique
    # ══════════════════════════════════════════════════════════════════════════

    # Cover
    cover = Table([[
        Paragraph("Quality Intelligence Hub", ParagraphStyle("ct", parent=getSampleStyleSheet()["Normal"],
                  fontSize=22, leading=27, textColor=WHITE, fontName="Helvetica-Bold", spaceAfter=3)),
        Paragraph("From raw ALM defect files to AI-enriched PDF reports in under 60 seconds —"
                  " combined with IBM ICA-powered requirements intelligence in one secured workspace.",
                  ParagraphStyle("cs", parent=getSampleStyleSheet()["Normal"],
                  fontSize=9.5, leading=14, textColor=colors.HexColor("#a8c8ff"),
                  fontName="Helvetica", spaceAfter=2)),
        Paragraph("Python · Flask · IBM watsonx.ai (Granite-3-8B · Slate-125M) · IBM ICA Agent · IBM Carbon",
                  ParagraphStyle("cm", parent=getSampleStyleSheet()["Normal"],
                  fontSize=8, leading=12, textColor=colors.HexColor("#c6e2ff"), fontName="Helvetica")),
    ]], colWidths=[CONTENT_W])
    cover.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), IBM_BLUE_DARK),
        ("TOPPADDING",    (0,0),(-1,-1), 10), ("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12), ("RIGHTPADDING", (0,0),(-1,-1), 12),
    ]))
    flow += [cover, gap(3)]

    # At a Glance — stat row
    flow += [Paragraph("At a Glance", st["h1"]), rule()]
    stats = [[
        [Paragraph("5", st["stat_n"]),    Paragraph("AI task modes\nfor requirements", st["stat_l"])],
        [Paragraph("<60s", st["stat_n"]), Paragraph("Full RCA cycle\nper defect file", st["stat_l"])],
        [Paragraph("0", st["stat_n"]),    Paragraph("External DBs\nor dependencies", st["stat_l"])],
        [Paragraph("2", st["stat_n"]),    Paragraph("IBM AI engines\n(watsonx + ICA)", st["stat_l"])],
    ]]
    st_t = Table(stats, colWidths=[CONTENT_W/4]*4)
    st_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), IBM_BLUE_LIGHT),
        ("BOX",           (0,0),(0,-1), 0.5, IBM_BLUE),("BOX",(1,0),(1,-1),0.5,IBM_BLUE),
        ("BOX",           (2,0),(2,-1), 0.5, IBM_BLUE),("BOX",(3,0),(3,-1),0.5,IBM_BLUE),
        ("TOPPADDING",    (0,0),(-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 4),("RIGHTPADDING", (0,0),(-1,-1), 4),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
    ]))
    flow += [st_t, gap(3)]

    # Before / After
    flow += [Paragraph("Before vs. After", st["h1"]), rule()]
    flow.append(before_after_drawing())
    flow.append(gap(3))

    # What makes it unique
    flow += [Paragraph("What Makes It Stand Out", st["h1"]), rule()]
    unique = [
        ("<b>Graceful AI degradation by design.</b>  The system has two fully working modes. "
         "With IBM watsonx.ai credentials, it calls Granite-3-8B-Instruct for AI-generated "
         "5-Whys, preventive measures, root cause suggestions, and an executive summary, "
         "and Slate-125M for semantic defect clustering. Without credentials, it falls back "
         "silently to rule-based keyword grouping and static templates — no errors, no crashes, "
         "no user action required. This was an intentional engineering decision: the tool is "
         "always production-ready regardless of which AI services are available."),
        ("<b>End-to-end IBM alignment — no third-party AI.</b>  Every intelligent call routes "
         "exclusively through IBM infrastructure: IBM watsonx.ai handles defect intelligence "
         "(text generation + semantic embeddings) and IBM ICA Agent handles requirements analysis. "
         "No OpenAI, no Anthropic, no HuggingFace. Fully compliant with IBM's AI governance, "
         "data residency, and acceptable-use policies."),
        ("<b>Semantic defect clustering without a vector database.</b>  The Hub uses IBM "
         "Slate-125M embeddings and cosine similarity computed in pure Python (no NumPy, "
         "no FAISS, no Pinecone) to group semantically related defects at runtime. "
         "The clustering result directly shapes which defects are presented as RCA candidates "
         "and which 5-Whys narratives are generated."),
    ]
    for b in unique:
        flow.append(Paragraph(f"• {b}", st["bullet"]))
        flow.append(gap(0.5))

    # Pull pipeline intro + diagram onto page 1 to fill the space
    flow.append(gap(2))
    flow += [Paragraph("The AI Intelligence Pipeline", st["h1"]), rule()]
    flow.append(Paragraph(
        "Every defect analysis run passes through a five-stage pipeline. "
        "Stages 3 and 4 adapt dynamically based on which IBM AI services are configured:",
        st["body"]))
    flow.append(ai_pipeline_drawing())

    flow.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 2 — Pipeline Detail Table + Engineering Decisions + SDLC Impact
    # ══════════════════════════════════════════════════════════════════════════

    flow.append(Paragraph(
        "Figure 1 — The pipeline is identical in both modes; only the intelligence depth changes.",
        st["caption"]))
    flow.append(gap(1))

    # Pipeline stage detail table — col widths must sum to CONTENT_W (178mm)
    # 24 + 90 + 38 + 26 = 178
    pipe_cw = [24*mm, 90*mm, 38*mm, 26*mm]

    def mode_label(text, bg):
        """Inline mode label — plain Paragraph, coloured via TableStyle per-cell."""
        return Paragraph(text, ParagraphStyle("_m", parent=getSampleStyleSheet()["Normal"],
                         fontSize=7.5, leading=10, fontName="Helvetica-Bold",
                         alignment=TA_CENTER, textColor=WHITE))

    pipe_data = [
        [Paragraph("Stage", st["th"]), Paragraph("What Happens", st["th"]),
         Paragraph("Technology", st["th"]), Paragraph("Mode", st["th"])],
        [Paragraph("1  Upload", st["td"]),
         Paragraph("File received, UUID session ID assigned, stored with timestamped name", st["td"]),
         Paragraph("Flask · Werkzeug", st["td"]), mode_label("Always", IBM_BLUE)],
        [Paragraph("2  Parse", st["td"]),
         Paragraph("Multi-encoding CSV detection (UTF-16/8/Latin-1), flexible column mapping, "
                   "severity/status/module/trend metrics computed", st["td"]),
         Paragraph("pandas", st["td"]), mode_label("Always", IBM_BLUE)],
        [Paragraph("3  Group", st["td"]),
         Paragraph("Defects grouped by semantic similarity (cosine on Slate-125M embeddings) "
                   "or keyword fallback. Groups become RCA clusters.", st["td"]),
         Paragraph("watsonx.ai\nor keywords", st["td"]), mode_label("Adaptive", IBM_PURPLE)],
        [Paragraph("4  AI Enrich", st["td"]),
         Paragraph("Per-cluster 5-Whys (Granite-3-8B), preventive measures, per-defect root cause "
                   "suggestion (top 20), AI executive summary for PDF header", st["td"]),
         Paragraph("IBM Granite\n3-8B-Instruct", st["td"]), mode_label("Adaptive", IBM_PURPLE)],
        [Paragraph("5  Report", st["td"]),
         Paragraph("ReportLab PDF rendered with charts, RCA table, measures, and AI summary "
                   "(or static summary if no watsonx credentials)", st["td"]),
         Paragraph("ReportLab 4.2", st["td"]), mode_label("Always", IBM_BLUE)],
    ]
    # Build the grid manually so we can colour the Mode column cells
    pipe_ts = [
        ("BACKGROUND",    (0,0),(-1,0), IBM_BLUE),
        ("GRID",          (0,0),(-1,-1), 0.4, IBM_GRAY_20),
        ("TOPPADDING",    (0,0),(-1,-1), 3), ("BOTTOMPADDING",(0,0),(-1,-1), 3),
        ("LEFTPADDING",   (0,0),(-1,-1), 5), ("RIGHTPADDING", (0,0),(-1,-1), 5),
        ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
        ("ALIGN",         (3,0),(-1,-1), "CENTER"),
        # Mode column colours (rows 1-5: rows 1,2=blue, 3,4=purple, 5=blue)
        ("BACKGROUND",    (3,1),(3,2), IBM_BLUE),
        ("BACKGROUND",    (3,3),(3,4), IBM_PURPLE),
        ("BACKGROUND",    (3,5),(3,5), IBM_BLUE),
        # Alt rows for non-mode columns
        ("BACKGROUND",    (0,1),(2,1), WHITE),
        ("BACKGROUND",    (0,2),(2,2), IBM_GRAY_10),
        ("BACKGROUND",    (0,3),(2,3), WHITE),
        ("BACKGROUND",    (0,4),(2,4), IBM_GRAY_10),
        ("BACKGROUND",    (0,5),(2,5), WHITE),
    ]
    pipe_t = Table(pipe_data, colWidths=pipe_cw, spaceBefore=3)
    pipe_t.setStyle(TableStyle(pipe_ts))
    flow.append(pipe_t)
    flow.append(gap(3))

    # Engineering decisions
    flow += [Paragraph("Key Engineering Decisions", st["h1"]), rule()]

    decisions = [
        [
            [Paragraph("No vector DB required", st["lbl"]),
             Paragraph("Cosine similarity over Slate-125M embeddings computed in pure Python stdlib "
                       "(math.sqrt, zip). Eliminates NumPy, FAISS, and Pinecone as dependencies — "
                       "the Hub installs with a single pip command.", st["body_sm"])],
            [Paragraph("Session-based isolation", st["lbl"]),
             Paragraph("Each analysis uses a UUID-prefixed filename. No shared state between "
                       "concurrent users. No database writes. Results are JSON files on disk — "
                       "trivially auditable and portable.", st["body_sm"])],
        ],
        [
            [Paragraph("API keys never reach the browser", st["lbl"]),
             Paragraph("GET /api/settings returns ica_api_key_set: bool and watsonx_api_key_set: bool "
                       "— never the actual key values. Secrets live only in config.json on the server.", st["body_sm"])],
            [Paragraph("Retry logic mirrors production ICA patterns", st["lbl"]),
             Paragraph("ICA Agent calls retry up to 2x with a 3-second gap on HTTP 502/503/504. "
                       "Timeout is 120s per attempt. Errors are converted to clean user-facing "
                       "messages — raw gateway HTML never reaches the UI.", st["body_sm"])],
        ],
    ]
    cw2 = [CONTENT_W/2 - 1*mm, CONTENT_W/2 - 1*mm]
    for row in decisions:
        dt = Table([row], colWidths=cw2)
        dt.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,-1), IBM_BLUE_LIGHT),
            ("BACKGROUND",    (1,0),(1,-1), IBM_PURPLE_LIGHT),
            ("BOX",           (0,0),(0,-1), 0.5, IBM_BLUE),
            ("BOX",           (1,0),(1,-1), 0.5, IBM_PURPLE),
            ("TOPPADDING",    (0,0),(-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1), 5),
            ("LEFTPADDING",   (0,0),(-1,-1), 7),("RIGHTPADDING", (0,0),(-1,-1), 7),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
        flow += [dt, gap(1.5)]

    flow.append(gap(2))

    # SDLC impact
    flow += [Paragraph("Where It Sits in the SDLC", st["h1"]), rule()]
    flow.append(Paragraph(
        "The Hub intervenes at two critical — and typically underserved — points in the software "
        "delivery lifecycle, shifting quality effort left:",
        st["body"]))

    sdlc_data = [
        [Paragraph("SDLC Phase", st["th"]), Paragraph("What the Hub Does", st["th"]),
         Paragraph("Impact", st["th"])],
        [Paragraph("Requirements\n(Pre-dev)", st["td"]),
         Paragraph("IBM ICA Agent reviews specifications for ambiguity, edge cases, test gaps, "
                   "and cross-consistency before a single line of code is written", st["td"]),
         Paragraph("Defects caught at requirements cost ~1x to fix vs. ~100x in production", st["td"])],
        [Paragraph("Post-sprint\n(Defect triage)", st["td"]),
         Paragraph("ALM export uploaded, analysed, and AI-enriched report generated in <60s "
                   "with clustered RCA candidates and preventive measures", st["td"]),
         Paragraph("Hours of manual triage eliminated per sprint; consistent outputs across teams", st["td"])],
        [Paragraph("Continuous\n(All sprints)", st["td"]),
         Paragraph("PDF reports accumulate as a historical quality record; monthly trend data "
                   "surfaces recurring failure patterns across releases", st["td"]),
         Paragraph("Data-driven retrospectives replace anecdotal quality conversations", st["td"])],
    ]
    flow.append(grid(sdlc_data, [28*mm, 74*mm, CONTENT_W-102*mm]))

    flow.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # PAGE 3 — ICA Agent Router, Security, Scalability & Closing
    # ══════════════════════════════════════════════════════════════════════════

    # ICA Agent router pattern
    flow += [Paragraph("The ICA Agent Router Pattern", st["h1"]), rule()]
    flow.append(Paragraph(
        "A key design insight in the Requirements Analyzer is that a single IBM ICA Agent "
        "endpoint can behave as five different specialists — depending entirely on the system "
        "prompt prepended to the user's input. This is the <b>router pattern</b>:",
        st["body"]))
    flow.append(gap(1))

    router_data = [
        [Paragraph("Task Key", st["th"]), Paragraph("System Prompt Persona", st["th"]),
         Paragraph("User Input", st["th"]), Paragraph("Output", st["th"])],
        [Paragraph("translate", st["td_c"]),
         Paragraph("Requirements Translator — preserves all technical details", st["td"]),
         Paragraph("Requirements in any language", st["td"]),
         Paragraph("Professional English requirements", st["td"])],
        [Paragraph("analyze", st["td_c"]),
         Paragraph("Requirements Analyst — clarity, completeness, ambiguities, improvements", st["td"]),
         Paragraph("Requirements document", st["td"]),
         Paragraph("Structured quality report", st["td"])],
        [Paragraph("edge_cases", st["td_c"]),
         Paragraph("QA Expert — boundary conditions, negative scenarios, systematic coverage", st["td"]),
         Paragraph("Requirements or feature description", st["td"]),
         Paragraph("Edge case catalogue", st["td"])],
        [Paragraph("review_tests", st["td_c"]),
         Paragraph("Test Case Reviewer — gaps, duplicates, edge cases, inconsistencies", st["td"]),
         Paragraph("Requirements + test cases", st["td"]),
         Paragraph("Test coverage gap report", st["td"])],
        [Paragraph("validate", st["td_c"]),
         Paragraph("Validation Expert — uncovered requirements, orphan tests, contradictions", st["td"]),
         Paragraph("Requirements + test cases", st["td"]),
         Paragraph("Consistency validation report", st["td"])],
    ]
    flow.append(grid(router_data, [20*mm, 62*mm, 40*mm, CONTENT_W-122*mm]))
    flow.append(gap(1))
    flow.append(colored_box(
        [Paragraph(
            "<b>Why this matters:</b>  One agent endpoint. Five specialised intelligences. "
            "No fine-tuning, no custom models, no additional infrastructure. "
            "The entire routing logic is 53 lines of Python in <i>ica_agent.py</i>.",
            st["body_sm"])],
        IBM_TEAL_LIGHT, IBM_TEAL, pad=5))
    flow.append(gap(3))

    # Security & deployment
    flow += [Paragraph("Security Model &amp; Deployment Footprint", st["h1"]), rule()]

    sec_data = [[
        [Paragraph("Authentication", st["lbl"]),
         Paragraph("pbkdf2:sha256 hashed passwords (Werkzeug). Flask server-side sessions. "
                   "Role-based access (admin / user). Default admin auto-seeded on first run. "
                   "All routes protected by @login_required decorator.", st["body_sm"])],
        [Paragraph("Secret Management", st["lbl"]),
         Paragraph("API keys stored only in config.json on the server filesystem. "
                   "GET /api/settings returns boolean presence flags — never key values. "
                   "User passwords stored as hashes — never plaintext anywhere.", st["body_sm"])],
        [Paragraph("Deployment Footprint", st["lbl"]),
         Paragraph("Single Python process. No Docker required. No cloud account needed for "
                   "rule-based mode. Runs on any machine with Python 3.8+. "
                   "Start command: python app.py", st["body_sm"])],
    ]]
    cw3 = [CONTENT_W/3]*3
    sec_t = Table(sec_data, colWidths=cw3)
    sec_t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(0,-1), IBM_BLUE_LIGHT),
        ("BACKGROUND",    (1,0),(1,-1), IBM_PURPLE_LIGHT),
        ("BACKGROUND",    (2,0),(2,-1), IBM_TEAL_LIGHT),
        ("BOX",           (0,0),(0,-1), 0.5, IBM_BLUE),
        ("BOX",           (1,0),(1,-1), 0.5, IBM_PURPLE),
        ("BOX",           (2,0),(2,-1), 0.5, IBM_TEAL),
        ("TOPPADDING",    (0,0),(-1,-1), 5),("BOTTOMPADDING",(0,0),(-1,-1), 5),
        ("LEFTPADDING",   (0,0),(-1,-1), 7),("RIGHTPADDING", (0,0),(-1,-1), 7),
        ("VALIGN",        (0,0),(-1,-1), "TOP"),
    ]))
    flow += [sec_t, gap(3)]

    # Future Scope
    flow += [Paragraph("Future Scope", st["h1"]), rule()]
    future = [
        [Paragraph("IBM watsonx Orchestrate Integration", st["lbl"]),
         Paragraph("The Hub currently calls IBM AI services via direct API. "
                   "The next evolution is to expose it as a <b>watsonx Orchestrate skill</b> — "
                   "allowing QA engineers to trigger defect analysis and requirements reviews "
                   "directly from a conversational AI assistant, embedded within their existing "
                   "IBM tools workflow without opening a browser at all.", st["body_sm"])],
        [Paragraph("Cross-Release Trend Intelligence", st["lbl"]),
         Paragraph("Each analysis already produces a timestamped JSON output. "
                   "By connecting these outputs to a lightweight <b>time-series store</b> "
                   "(even a simple SQLite DB), the Hub could surface defect velocity trends, "
                   "recurring root cause patterns across multiple releases, and predictive "
                   "quality risk scores — turning retrospective reports into forward-looking "
                   "quality forecasts.", st["body_sm"])],
    ]
    for item in future:
        r = Table([item], colWidths=[44*mm, CONTENT_W - 48*mm])
        r.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(0,-1), IBM_BLUE_LIGHT),
            ("BACKGROUND",    (1,0),(1,-1), IBM_GRAY_10),
            ("BOX",           (0,0),(0,-1), 0.5, IBM_BLUE),
            ("BOX",           (1,0),(1,-1), 0.5, IBM_GRAY_20),
            ("TOPPADDING",    (0,0),(-1,-1), 6),("BOTTOMPADDING",(0,0),(-1,-1), 6),
            ("LEFTPADDING",   (0,0),(-1,-1), 7),("RIGHTPADDING", (0,0),(-1,-1), 7),
            ("VALIGN",        (0,0),(-1,-1), "TOP"),
        ]))
        flow += [r, gap(1.5)]
    flow.append(gap(2))

    # Closing callout
    t = Table([[Paragraph(
        "Built in IBM. Runs on IBM AI. Designed for IBM delivery teams.\n"
        "The Quality Intelligence Hub is not a proof of concept — it is a "
        "production-ready tool actively used to analyse real ALM defect data.",
        st["callout"])]],
        colWidths=[CONTENT_W])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1), IBM_BLUE_DARK),
        ("TOPPADDING",    (0,0),(-1,-1), 10),("BOTTOMPADDING",(0,0),(-1,-1), 10),
        ("LEFTPADDING",   (0,0),(-1,-1), 12),("RIGHTPADDING", (0,0),(-1,-1), 12),
    ]))
    flow += [t, gap(2)]
    flow.append(Paragraph(
        "Internal IBM tooling — not for external distribution.",
        st["body_sm"]))

    doc.build(flow, onFirstPage=page_decorator, onLaterPages=page_decorator)
    size_kb = os.path.getsize(OUTPUT_FILE) / 1024
    print(f"OK  {OUTPUT_FILE}  --  {size_kb:.1f} KB  ({size_kb/1024:.2f} MB)")


if __name__ == "__main__":
    build()
