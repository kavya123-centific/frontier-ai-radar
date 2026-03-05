"""
pdf_generator.py
----------------
Generates branded PDF digest from ranked findings.

Windows-compatible: uses ReportLab (pure Python, zero system dependencies).
WeasyPrint requires GTK/Pango/GObject binaries — painful on Windows.
ReportLab installs cleanly everywhere: pip install reportlab

FIX: Always produces a valid PDF even when findings is empty.
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable, KeepTogether,
)

logger = logging.getLogger(__name__)

# Brand colours
NAVY  = colors.HexColor("#1e3a5f")
BLUE  = colors.HexColor("#3b82f6")
GREEN = colors.HexColor("#059669")
TEAL  = colors.HexColor("#10b981")
LIGHT = colors.HexColor("#f0fdf4")
LBLUE = colors.HexColor("#eff6ff")
GRAY  = colors.HexColor("#6b7280")
LGRAY = colors.HexColor("#f9fafb")
BLACK = colors.HexColor("#1f2937")
WHITE = colors.white

CATEGORY_LABELS = {
    "competitors":     "Competitor Intelligence",
    "model_providers": "Foundation Model Providers",
    "research":        "Research Publications",
    "hf_benchmarks":   "HF Benchmarks & Leaderboards",
}
CATEGORY_ICONS = {
    "competitors":     "[COMP]",
    "model_providers": "[MODEL]",
    "research":        "[RESEARCH]",
    "hf_benchmarks":   "[HF]",
}


def _styles():
    S = {}
    S["Title"] = ParagraphStyle("Title", fontSize=28, textColor=NAVY,
        spaceAfter=6, fontName="Helvetica-Bold", alignment=TA_CENTER)
    S["SubTitle"] = ParagraphStyle("SubTitle", fontSize=13, textColor=GRAY,
        spaceAfter=4, fontName="Helvetica", alignment=TA_CENTER)
    S["SectionH"] = ParagraphStyle("SectionH", fontSize=14, textColor=NAVY,
        spaceBefore=16, spaceAfter=6, fontName="Helvetica-Bold")
    S["FindingTitle"] = ParagraphStyle("FindingTitle", fontSize=11, textColor=BLACK,
        spaceBefore=8, spaceAfter=3, fontName="Helvetica-Bold")
    S["Body"] = ParagraphStyle("Body", fontSize=9.5, textColor=BLACK,
        spaceAfter=4, fontName="Helvetica", leading=14)
    S["Why"] = ParagraphStyle("Why", fontSize=9, textColor=colors.HexColor("#1e40af"),
        spaceAfter=4, fontName="Helvetica-Oblique", leading=13)
    S["Meta"] = ParagraphStyle("Meta", fontSize=8, textColor=GRAY,
        spaceAfter=6, fontName="Helvetica")
    S["ExecTitle"] = ParagraphStyle("ExecTitle", fontSize=10.5,
        textColor=colors.HexColor("#065f46"), fontName="Helvetica-Bold", spaceAfter=2)
    S["ExecBody"] = ParagraphStyle("ExecBody", fontSize=9.5, textColor=BLACK,
        fontName="Helvetica", spaceAfter=2, leading=13)
    S["Footer"] = ParagraphStyle("Footer", fontSize=7.5, textColor=GRAY,
        fontName="Helvetica", alignment=TA_CENTER)
    S["Score"] = ParagraphStyle("Score", fontSize=9.5, textColor=GREEN,
        fontName="Helvetica-Bold")
    S["Empty"] = ParagraphStyle("Empty", fontSize=14, textColor=GRAY,
        fontName="Helvetica", alignment=TA_CENTER, spaceBefore=60)
    return S


def _header_footer(canvas, doc):
    canvas.saveState()
    w, h = A4
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(0.5)
    canvas.line(2*cm, h - 1.5*cm, w - 2*cm, h - 1.5*cm)
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(GRAY)
    canvas.drawCentredString(w/2, h - 1.3*cm, "Frontier AI Radar - Daily Intelligence Digest")
    canvas.line(2*cm, 1.5*cm, w - 2*cm, 1.5*cm)
    canvas.drawString(2*cm, 1.1*cm, "Internal Use Only  |  Frontier AI Radar")
    canvas.drawRightString(w - 2*cm, 1.1*cm, f"Page {doc.page}")
    canvas.restoreState()


def _exec_item(idx, f, S):
    score = f.get("final_score", 0)
    title = f.get("title", "Untitled")
    summ  = f.get("summary", "")[:200]
    url   = f.get("source_url", "")[:80]
    cat   = CATEGORY_LABELS.get(f.get("category", ""), "").upper()

    tbl = Table([[
        Paragraph(f"{idx}. {title}", S["ExecTitle"]),
        Paragraph(f"Score: {score:.1f}", S["Score"]),
    ]], colWidths=["85%", "15%"])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), LIGHT),
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LINEBEFORE",    (0,0), (0,0),   3, TEAL),
    ]))
    return [tbl, Paragraph(summ, S["ExecBody"]),
            Paragraph(f"Source: {url}  |  {cat}", S["Meta"]), Spacer(1, 4)]


def _finding_block(f, S):
    score = f.get("final_score", 0)
    title = f.get("title", "Untitled")
    summ  = f.get("summary", "")
    why   = f.get("why_matters", "")
    url   = f.get("source_url", "")[:90]
    pub   = f.get("publisher", "")
    tags  = f.get("tags", [])
    icon  = CATEGORY_ICONS.get(f.get("category", ""), "")

    hdr = Table([[
        Paragraph(f"{icon} {title}", S["FindingTitle"]),
        Paragraph(f"* {score:.1f}", S["Score"]),
    ]], colWidths=["85%", "15%"])
    hdr.setStyle(TableStyle([
        ("LEFTPADDING",   (0,0), (-1,-1), 8),
        ("RIGHTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("LINEBEFORE",    (0,0), (0,0),   3, BLUE),
        ("BACKGROUND",    (0,0), (-1,-1), LGRAY),
    ]))

    items = [hdr]
    if summ:
        items.append(Paragraph(summ, S["Body"]))
    if why:
        items.append(Paragraph(f"Why it matters: {why}", S["Why"]))

    meta = [f"Source: {url}"]
    if pub and pub != "Unknown":
        meta.append(f"Publisher: {pub}")
    if tags:
        meta.append("Tags: " + ", ".join(tags[:4]))
    items.append(Paragraph("  |  ".join(meta), S["Meta"]))
    items.append(Spacer(1, 6))
    return [KeepTogether(items)]


def generate_pdf(findings: List[Dict[str, Any]], output_path: str = "digest.pdf") -> str:
    """
    Build branded A4 PDF from ranked findings using ReportLab.
    Pure Python — no GTK/Pango system libraries needed (Windows safe).
    Always produces a valid file even when findings is empty.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    S   = _styles()
    now = datetime.now()

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.2*cm, bottomMargin=2.2*cm,
        title="Frontier AI Radar - Daily Digest",
    )
    story = []

    # Cover
    story.append(Spacer(1, 3*cm))
    story.append(Paragraph("Frontier AI Radar", S["Title"]))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(now.strftime("%B %d, %Y"), S["SubTitle"]))
    story.append(Paragraph(
        f"{len(findings)} intelligence signals tracked" if findings
        else "No new signals detected today",
        S["SubTitle"]
    ))
    story.append(Spacer(1, 0.5*cm))

    badge = Table([["DAILY INTELLIGENCE DIGEST"]], colWidths=[12*cm])
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), NAVY),
        ("TEXTCOLOR",     (0,0), (-1,-1), WHITE),
        ("FONTNAME",      (0,0), (-1,-1), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 11),
        ("ALIGN",         (0,0), (-1,-1), "CENTER"),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(badge)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Powered by Claude AI  |  Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}",
        S["Footer"]
    ))
    story.append(PageBreak())

    if not findings:
        story.append(Paragraph("No new intelligence signals detected in this run.", S["Empty"]))
        story.append(Paragraph(
            "All sources returned unchanged content or no relevant AI/ML intelligence.",
            S["SubTitle"]
        ))
        doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
        logger.info(f"PDF (empty) generated: {output_path}")
        return output_path

    # Executive summary
    story.append(Paragraph("Executive Summary - Top Signals Today", S["SectionH"]))
    story.append(HRFlowable(width="100%", thickness=2, color=BLUE, spaceAfter=8))
    for i, f in enumerate(findings[:5], 1):
        story.extend(_exec_item(i, f, S))

    # Deep dives by category
    by_cat: Dict[str, List] = {}
    for f in findings[:30]:
        by_cat.setdefault(f.get("category", "other"), []).append(f)

    for cat, items in by_cat.items():
        story.append(PageBreak())
        label = CATEGORY_LABELS.get(cat, cat.title())
        icon  = CATEGORY_ICONS.get(cat, "")
        story.append(Paragraph(f"{icon} {label}", S["SectionH"]))
        story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=6))
        story.append(Paragraph(f"{len(items)} signal(s) in this category", S["Meta"]))
        story.append(Spacer(1, 6))
        for f in items:
            story.extend(_finding_block(f, S))

    # Appendix table
    story.append(PageBreak())
    story.append(Paragraph("Appendix - All Signals This Run", S["SectionH"]))
    story.append(HRFlowable(width="100%", thickness=1, color=BLUE, spaceAfter=6))

    rows = [["#", "Title", "Category", "Publisher", "Score"]]
    for i, f in enumerate(findings, 1):
        t = f.get("title", "")
        rows.append([
            str(i),
            (t[:55] + "..." if len(t) > 55 else t),
            CATEGORY_LABELS.get(f.get("category", ""), ""),
            f.get("publisher", "-")[:20],
            f"{f.get('final_score', 0):.1f}",
        ])

    tbl = Table(rows, colWidths=[1*cm, 9*cm, 4*cm, 3*cm, 1.5*cm], repeatRows=1)
    tbl.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0),  NAVY),
        ("TEXTCOLOR",     (0,0), (-1,0),  WHITE),
        ("FONTNAME",      (0,0), (-1,0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 8),
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [WHITE, LGRAY]),
        ("GRID",          (0,0), (-1,-1), 0.25, colors.HexColor("#e5e7eb")),
        ("ALIGN",         (4,0), (4,-1),  "CENTER"),
        ("LEFTPADDING",   (0,0), (-1,-1), 4),
        ("RIGHTPADDING",  (0,0), (-1,-1), 4),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph(
        f"Frontier AI Radar v3.0  |  {now.strftime('%B %d, %Y')}  |  "
        "Powered by Claude AI  |  Internal Use Only",
        S["Footer"]
    ))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    size_kb = os.path.getsize(output_path) // 1024
    logger.info(f"PDF generated: {output_path} ({len(findings)} findings, {size_kb} KB)")
    return output_path
