"""
The core AI engine: sends a question paper PDF directly to Gemini and gets
back structured data — paper metadata, a full text transcription, and every
question tagged with unit, topic, marks, and type.

This is the single most important file in the app. Everything downstream
(dashboard charts, Q&A) depends on this extraction being accurate.

Design choice: we send the raw PDF bytes straight to Gemini instead of
extracting text first with a separate library. Gemini's vision model can
read both text-based AND scanned/image PDFs natively, which means:
  - one code path handles both PDF types (no OCR library needed)
  - no Tesseract/EasyOCR installation, no Rust/C build issues
  - Gemini transcribes the page AND classifies questions in a single call

We use Gemini's native structured output (response_schema) with our
Pydantic model passed directly, so the response is guaranteed to match
PaperExtractionResult without needing prompt-level pleading.

Using gemini-2.5-flash: free tier, no card required, handles multimodal
structured extraction well, and isn't on Google's deprecation list.
"""

import os
from google import genai
from google.genai import types
from models import PaperExtractionResult

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT = """You are an expert at analyzing college engineering question papers \
(SASTRA University format). You will be given a question paper as a PDF — it may be a \
clean text-based PDF or a scanned/photographed image of a printed paper. Read it carefully \
regardless of format.

Your job:
1. Transcribe the full paper text as accurately as possible into transcribed_text — this \
preserves the complete content for later reference, even if formatting is imperfect.
2. Identify paper metadata: subject name, exam type (CIA-1/CIA-2/CIA-3/End Semester/Model \
Exam), department if mentioned, and year if mentioned.
3. Extract EVERY individual question on the paper, even sub-parts (e.g. 1a, 1b, 2).
4. For each question, classify:
   - unit: which syllabus unit (1-5) it most likely belongs to, based on topic content
   - topic: a short, specific topic name (e.g. "Normalization", "MVT", "Tomasulo's Algorithm")
   - marks: the mark value assigned to that question
   - question_type: Theory, Numerical, Diagram, Derivation, or Programming — pick whichever
     best describes the FORMAT of the expected answer
   - has_diagram: true if a student needs to look at a printed figure, graph, tree, table-as-
     image, or chart ON THE PAPER to answer this question. This is independent of
     question_type — for example, "find the shortest path in the graph below" is
     question_type="Numerical" AND has_diagram=true at the same time, because it requires
     numeric computation but also requires reading a graph image. Set has_diagram=true any
     time the question references "the graph below", "the figure shown", "the tree given",
     or similar, OR when a diagram/graph/chart appears near that question in the paper.

If unit number isn't explicitly stated on the paper, infer it from the question's subject \
matter and typical syllabus ordering. Be decisive — always provide a best-guess unit and \
topic rather than leaving them vague. If the scan is partially unclear, transcribe your best \
reading rather than skipping content."""


def classify_paper(pdf_bytes: bytes) -> PaperExtractionResult:
    """
    Sends a PDF (text-based or scanned) directly to Gemini and returns
    validated, structured extraction — transcription + metadata + questions
    all in one call. Gemini's response_schema guarantees the JSON shape;
    Pydantic re-validates on parse as a second safety net.
    """
    pdf_part = types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")

    response = client.models.generate_content(
        model=MODEL,
        contents=[pdf_part, "Analyze this question paper."],
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=PaperExtractionResult,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini did not return a structured extraction.")

    return PaperExtractionResult.model_validate_json(response.text)


def answer_question_about_paper(raw_text: str, question: str) -> str:
    """
    Scoped Q&A: answers a student's question using ONLY this paper's
    transcribed text as context. Single document, full text fits in
    context, no retrieval step needed.
    """
    response = client.models.generate_content(
        model=MODEL,
        contents=f"PAPER TEXT:\n{raw_text}\n\nQUESTION: {question}",
        config=types.GenerateContentConfig(
            system_instruction=(
                "You answer questions about a single uploaded question paper. "
                "Only use the paper text provided below as your source. "
                "If the answer isn't in the paper, say so clearly instead of guessing."
            ),
        ),
    )

    return response.text or "No answer generated."
