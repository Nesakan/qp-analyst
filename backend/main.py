"""
QP Analyst — FastAPI backend entrypoint.

Flow per upload:
  PDF bytes -> ai_engine (Gemini reads + classifies directly) -> database (saved)
  -> if any question is type="Diagram", run diagram_extractor as a second pass
  -> returned to frontend

Note: there's no separate text-extraction step. Gemini reads the PDF natively
(text-based or scanned) and returns both a transcription and the classified
questions in one call.

The diagram extraction pass is intentionally best-effort: if it fails (bad
bounding box, storage hiccup, etc.) the upload still succeeds with all
questions saved — the paper just won't have diagram images attached. This
keeps the core feature (classification) from being blocked by the newer,
less-certain feature (diagram cropping).
"""

import os
import logging
from dotenv import load_dotenv

load_dotenv()  # must run before importing modules that read os.environ at import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("qp-analyst")

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from ai_engine import classify_paper, answer_question_about_paper
from diagram_extractor import extract_diagrams
import database
from models import Paper, PaperSummary, AskRequest, AskResponse

app = FastAPI(title="QP Analyst API")

origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/papers/upload")
async def upload_paper(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")

    pdf_bytes = await file.read()

    try:
        extraction = classify_paper(pdf_bytes)
    except Exception as e:
        raise HTTPException(502, f"AI extraction failed: {e}")

    paper_id, question_ids = database.save_paper_extraction(
        file.filename, extraction.transcribed_text, extraction
    )

    diagram_question_numbers = {
        q.question_number for q in extraction.questions if q.has_diagram
    }
    diagrams_attached = 0

    if diagram_question_numbers:
        logger.info(
            f"Paper {paper_id}: attempting diagram extraction for questions {diagram_question_numbers}"
        )
        try:
            diagrams = extract_diagrams(pdf_bytes, diagram_question_numbers)
            logger.info(f"Paper {paper_id}: detected {len(diagrams)} diagram(s)")
            for d in diagrams:
                question_id = question_ids.get(d.question_number)
                if not question_id:
                    logger.warning(
                        f"Paper {paper_id}: diagram found for question "
                        f"{d.question_number} but no matching question_id"
                    )
                    continue
                url = database.upload_diagram_image(paper_id, d.question_number, d.image_bytes)
                database.attach_diagram_url(question_id, url)
                diagrams_attached += 1
        except Exception as e:
            # Best-effort: log and continue. The paper is already saved successfully.
            logger.warning(f"Diagram extraction failed for paper {paper_id}: {e}")
    else:
        logger.info(f"Paper {paper_id}: no questions flagged has_diagram, skipping extraction pass")

    return {
        "paper_id": paper_id,
        "question_count": len(extraction.questions),
        "diagrams_attached": diagrams_attached,
    }


@app.get("/papers")
def list_papers() -> list[Paper]:
    rows = database.list_papers()
    return [
        Paper(
            id=r["id"],
            filename=r["filename"],
            subject_name=r["subject_name"],
            exam_type=r["exam_type"],
            department=r.get("department"),
            year=r.get("year"),
            uploaded_at=r["uploaded_at"],
            question_count=r["question_count"],
        )
        for r in rows
    ]


@app.get("/papers/{paper_id}")
def get_paper(paper_id: str):
    data = database.get_paper(paper_id)
    if not data["paper"]:
        raise HTTPException(404, "Paper not found.")
    return data


@app.get("/papers/{paper_id}/summary")
def get_paper_summary(paper_id: str) -> PaperSummary:
    return database.get_paper_summary(paper_id)


@app.post("/papers/{paper_id}/ask")
def ask_about_paper(paper_id: str, body: AskRequest) -> AskResponse:
    raw_text = database.get_paper_raw_text(paper_id)
    if not raw_text:
        raise HTTPException(404, "Paper not found.")

    answer = answer_question_about_paper(raw_text, body.question)
    return AskResponse(answer=answer)


@app.get("/health")
def health():
    return {"status": "ok"}
