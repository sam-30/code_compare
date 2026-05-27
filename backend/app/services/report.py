"""Generate comparison reports as JSON or PDF (via fpdf2)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.comparison import Comparison


def build_json_report(comparison) -> dict:
    return {
        "id": comparison.id,
        "repo_a_id": comparison.repo_a_id,
        "repo_b_id": comparison.repo_b_id,
        "language": comparison.language,
        "status": comparison.status.value,
        "overall_score": comparison.overall_score,
        "created_at": comparison.created_at.isoformat() if comparison.created_at else None,
        "completed_at": comparison.completed_at.isoformat() if comparison.completed_at else None,
        "error_message": comparison.error_message,
        "method_results": [
            {
                "method_id": r.method_id,
                "score": r.score,
                "weight": r.weight,
                "details": r.details,
                "duration_ms": r.duration_ms,
            }
            for r in comparison.method_results
        ],
        "file_matches": [
            {
                "file_a_path": m.file_a_path,
                "file_b_path": m.file_b_path,
                "similarity_score": m.similarity_score,
                "method_id": m.method_id,
            }
            for m in comparison.file_matches
        ],
    }


def _pct(score: float | None) -> str:
    if score is None:
        return "N/A"
    return f"{round(score * 100)}%"


def _score_rgb(score: float | None) -> tuple[int, int, int]:
    if score is None:
        return (107, 114, 128)
    if score < 0.3:
        return (22, 163, 74)   # green
    if score < 0.7:
        return (217, 119, 6)   # yellow
    return (220, 38, 38)       # red


def build_pdf_bytes(comparison) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    # Title
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 10, f"Code Comparison Report #{comparison.id}", ln=True)
    pdf.ln(2)

    # Meta
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(107, 114, 128)
    completed = (
        comparison.completed_at.strftime("%Y-%m-%d %H:%M UTC")
        if comparison.completed_at
        else "—"
    )
    pdf.cell(0, 6, f"Language: {comparison.language}   |   "
                   f"Repos: {comparison.repo_a_id} vs {comparison.repo_b_id}   |   "
                   f"Completed: {completed}", ln=True)
    pdf.ln(6)

    # Overall score
    score = comparison.overall_score
    r, g, b = _score_rgb(score)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(r, g, b)
    pdf.cell(0, 14, _pct(score), ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, "Overall Similarity Score", ln=True)
    pdf.ln(8)

    # Method breakdown table
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 13)
    pdf.cell(0, 8, "Method Breakdown", ln=True)
    pdf.ln(2)

    col_w = [75, 30, 25, 30]
    headers = ["Method", "Score", "Weight", "Duration"]
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(243, 244, 246)
    pdf.set_text_color(75, 85, 99)
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border="B", fill=True)
    pdf.ln()

    pdf.set_font("Helvetica", "", 9)
    for mr in sorted(comparison.method_results, key=lambda x: -x.score):
        pdf.set_text_color(0, 0, 0)
        pdf.cell(col_w[0], 6, mr.method_id.replace("_", " ").title())
        r2, g2, b2 = _score_rgb(mr.score)
        pdf.set_text_color(r2, g2, b2)
        pdf.cell(col_w[1], 6, _pct(mr.score))
        pdf.set_text_color(0, 0, 0)
        pdf.cell(col_w[2], 6, f"{round(mr.weight * 100)}%")
        pdf.cell(col_w[3], 6, f"{mr.duration_ms} ms", ln=True)

    # File matches (top 30)
    matches = sorted(comparison.file_matches, key=lambda x: -x.similarity_score)[:30]
    if matches:
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 13)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 8, "Top File Matches", ln=True)
        pdf.ln(2)

        fm_col_w = [65, 65, 25, 25]
        fm_headers = ["File A", "File B", "Score", "Method"]
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_text_color(75, 85, 99)
        pdf.set_fill_color(243, 244, 246)
        for i, h in enumerate(fm_headers):
            pdf.cell(fm_col_w[i], 7, h, border="B", fill=True)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for m in matches:
            pdf.set_text_color(0, 0, 0)
            fa = m.file_a_path.split("/")[-1]
            fb = m.file_b_path.split("/")[-1]
            pdf.cell(fm_col_w[0], 5, fa[:30])
            pdf.cell(fm_col_w[1], 5, fb[:30])
            r2, g2, b2 = _score_rgb(m.similarity_score)
            pdf.set_text_color(r2, g2, b2)
            pdf.cell(fm_col_w[2], 5, _pct(m.similarity_score))
            pdf.set_text_color(0, 0, 0)
            pdf.cell(fm_col_w[3], 5, m.method_id[:12], ln=True)

    # Footer
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(156, 163, 175)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    pdf.cell(0, 5, f"Generated by Code Comparison Tool on {now}", ln=True)

    return bytes(pdf.output())
