"""
All database read/write operations, isolated in one place.

Why isolate this: if we ever swap Supabase for plain Postgres + SQLAlchemy
(common once a project outgrows the free tier), only this file changes —
nothing in main.py or claude_engine.py needs to know how storage works.
"""

import os
from supabase import create_client, Client
from models import PaperExtractionResult, PaperSummary

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"],
)


def save_paper_extraction(filename: str, raw_text: str, extraction: PaperExtractionResult) -> tuple[str, dict[str, str]]:
    """
    Saves a paper + all its classified questions in one transaction-like flow.
    Returns (paper_id, question_number -> question_id map) — the map is needed
    so a later diagram-extraction pass can attach diagram_url to the right row.
    """
    paper_row = (
        supabase.table("papers")
        .insert({
            "filename": filename,
            "subject_name": extraction.metadata.subject_name,
            "exam_type": extraction.metadata.exam_type,
            "department": extraction.metadata.department,
            "year": extraction.metadata.year,
            "raw_text": raw_text,
        })
        .execute()
    )
    paper_id = paper_row.data[0]["id"]

    question_rows = [
        {
            "paper_id": paper_id,
            "question_number": q.question_number,
            "question_text": q.question_text,
            "unit": q.unit,
            "topic": q.topic,
            "marks": q.marks,
            "question_type": q.question_type,
            "has_diagram": q.has_diagram,
        }
        for q in extraction.questions
    ]

    question_id_by_number: dict[str, str] = {}
    if question_rows:
        inserted = supabase.table("questions").insert(question_rows).execute()
        for row in inserted.data:
            question_id_by_number[row["question_number"]] = row["id"]

    return paper_id, question_id_by_number


def attach_diagram_url(question_id: str, diagram_url: str) -> None:
    """Saves a cropped diagram's storage URL onto its question row."""
    supabase.table("questions").update({"diagram_url": diagram_url}).eq("id", question_id).execute()


def upload_diagram_image(paper_id: str, question_number: str, image_bytes: bytes) -> str:
    """
    Uploads a cropped diagram PNG to the 'diagrams' Storage bucket and
    returns its public URL. Bucket must already exist (see schema.sql).
    """
    # sanitize question_number for use in a file path (e.g. "17a" stays as-is, safe already)
    path = f"{paper_id}/{question_number}.png"

    supabase.storage.from_("diagrams").upload(
        path,
        image_bytes,
        file_options={"content-type": "image/png", "upsert": "true"},
    )

    return supabase.storage.from_("diagrams").get_public_url(path)


def get_paper(paper_id: str) -> dict:
    paper = supabase.table("papers").select("*").eq("id", paper_id).single().execute()
    questions = supabase.table("questions").select("*").eq("paper_id", paper_id).execute()
    return {"paper": paper.data, "questions": questions.data}


def list_papers() -> list[dict]:
    """Returns all papers with their question count, newest first."""
    papers = supabase.table("papers").select("*").order("uploaded_at", desc=True).execute()

    result = []
    for p in papers.data:
        count = (
            supabase.table("questions")
            .select("id", count="exact")
            .eq("paper_id", p["id"])
            .execute()
        )
        result.append({**p, "question_count": count.count or 0})

    return result


def get_paper_summary(paper_id: str) -> PaperSummary:
    questions = supabase.table("questions").select("*").eq("paper_id", paper_id).execute().data

    unit_distribution: dict[int, int] = {}
    marks_by_unit: dict[int, int] = {}
    question_type_distribution: dict[str, int] = {}
    total_marks = 0

    for q in questions:
        unit = q["unit"]
        marks = q["marks"]
        qtype = q["question_type"]

        unit_distribution[unit] = unit_distribution.get(unit, 0) + 1
        marks_by_unit[unit] = marks_by_unit.get(unit, 0) + marks
        question_type_distribution[qtype] = question_type_distribution.get(qtype, 0) + 1
        total_marks += marks

    return PaperSummary(
        paper_id=paper_id,
        unit_distribution=unit_distribution,
        marks_by_unit=marks_by_unit,
        question_type_distribution=question_type_distribution,
        total_marks=total_marks,
        total_questions=len(questions),
    )


def get_paper_raw_text(paper_id: str) -> str:
    paper = supabase.table("papers").select("raw_text").eq("id", paper_id).single().execute()
    return paper.data["raw_text"]
