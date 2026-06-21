"""
Extracts diagram images from question paper PDFs.

Pipeline:
  PDF -> render each page to PNG (PyMuPDF) -> ask Gemini for bounding boxes
  of diagrams on that page (tied to question numbers) -> crop the region
  out of the page image (Pillow) -> caller uploads crop to storage.

This runs as a SEPARATE pass after the main classify_paper() call, only on
pages that contain a question already classified as question_type="Diagram".
That keeps the (slower, less certain) bounding-box step scoped to where it's
actually needed, instead of running on every page of every paper.
"""

import io
import os
from dataclasses import dataclass

import fitz  # PyMuPDF
from PIL import Image
from google import genai
from google.genai import types
from pydantic import BaseModel

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.5-flash"

RENDER_DPI = 200  # good balance of clarity vs. file size for cropped diagrams


class DiagramBox(BaseModel):
    """One detected diagram on a page, tied back to the question that references it."""
    question_number: str
    # normalized 0-1000 coordinates, Gemini's standard bounding box format
    ymin: int
    xmin: int
    ymax: int
    xmax: int


class PageDiagrams(BaseModel):
    diagrams: list[DiagramBox]


@dataclass
class CroppedDiagram:
    question_number: str
    page_number: int  # 1-indexed
    image_bytes: bytes  # PNG bytes, ready to upload


BBOX_SYSTEM_PROMPT = """You are looking at one page of a college exam question paper. \
Some questions reference a diagram, graph, table-as-figure, or chart that the student \
must read to answer (e.g. "find the shortest path in the graph below", "using the tree \
shown"). Your job is to find ONLY these visual diagrams/figures — not plain text, not \
the question text itself.

For each diagram you find on this page:
- Identify which question_number it belongs to (matching the number printed next to the question, e.g. "16", "17a")
- Return its bounding box in normalized coordinates from 0 to 1000, where (0,0) is the
  top-left corner of the page and (1000,1000) is the bottom-right.

If a page has no diagrams, return an empty list. Do not invent boxes for purely textual content."""


def render_pdf_pages(pdf_bytes: bytes) -> list[bytes]:
    """Renders every page of a PDF to PNG bytes at RENDER_DPI."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=RENDER_DPI)
        pages.append(pix.tobytes("png"))
    doc.close()
    return pages


def detect_diagrams_on_page(page_png: bytes) -> list[DiagramBox]:
    """
    Asks Gemini to find diagram bounding boxes on a single rendered page.
    Returns an empty list if none found — this is the expected case for
    most pages, not an error.
    """
    image_part = types.Part.from_bytes(data=page_png, mime_type="image/png")

    response = client.models.generate_content(
        model=MODEL,
        contents=[image_part, "Find any diagrams/figures on this page."],
        config=types.GenerateContentConfig(
            system_instruction=BBOX_SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=PageDiagrams,
        ),
    )

    if not response.text:
        return []

    result = PageDiagrams.model_validate_json(response.text)
    return result.diagrams


def crop_diagram(page_png: bytes, box: DiagramBox) -> bytes:
    """
    Crops a diagram region out of a full page image using normalized
    0-1000 coordinates, with a small padding margin so we don't clip
    the figure's edge labels.
    """
    img = Image.open(io.BytesIO(page_png))
    width, height = img.size

    # convert normalized (0-1000) coords to pixel coords
    left = int(box.xmin / 1000 * width)
    top = int(box.ymin / 1000 * height)
    right = int(box.xmax / 1000 * width)
    bottom = int(box.ymax / 1000 * height)

    # small padding so edge labels/arrowheads aren't clipped
    pad = 12
    left = max(0, left - pad)
    top = max(0, top - pad)
    right = min(width, right + pad)
    bottom = min(height, bottom + pad)

    cropped = img.crop((left, top, right, bottom))

    buf = io.BytesIO()
    cropped.save(buf, format="PNG")
    return buf.getvalue()


def extract_diagrams(pdf_bytes: bytes, diagram_question_numbers: set[str]) -> list[CroppedDiagram]:
    """
    Full diagram extraction pass. Only worth calling if classify_paper()
    found at least one question_type="Diagram" — pass those question
    numbers in via diagram_question_numbers so we know what to look for.

    Runs bounding-box detection per page (not per question) since one
    Gemini call can find all diagrams on a page at once.
    """
    if not diagram_question_numbers:
        return []

    pages = render_pdf_pages(pdf_bytes)
    results: list[CroppedDiagram] = []

    for page_num, page_png in enumerate(pages, start=1):
        boxes = detect_diagrams_on_page(page_png)

        for box in boxes:
            if box.question_number not in diagram_question_numbers:
                continue  # Gemini found something but it's not one we classified as a diagram question

            cropped_bytes = crop_diagram(page_png, box)
            results.append(
                CroppedDiagram(
                    question_number=box.question_number,
                    page_number=page_num,
                    image_bytes=cropped_bytes,
                )
            )

    return results
