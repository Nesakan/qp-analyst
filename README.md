# QP Analyst

An AI-powered tool that reads University question papers (scanned or typed PDFs) and automatically breaks them down by unit, topic, marks, and question type — turning a raw PDF into a structured, searchable study dashboard.

## The problem

Before an exam, students flip through years of old question papers trying to spot patterns: which units come up most, what kind of questions repeat, where the marks are concentrated. It's manual, slow, and easy to miss patterns that span multiple papers.

## What it does

1. **Upload** a question paper PDF — scanned or typed, doesn't matter
2. **Gemini reads it natively** as a multimodal input (no separate OCR pipeline) and classifies every question: unit, topic, marks, question type, and whether it includes a diagram
3. **Diagrams get extracted automatically** — for any question with a graph, tree, or figure, the relevant page region is detected, cropped, and stored separately, then shown inline next to that question
4. **Dashboard** renders the breakdown as charts (unit distribution, question type spread) plus a full question list, viewable in either original paper order or grouped by unit
5. **Ask the paper** — a scoped Q&A box lets you ask questions about that specific paper's content, answered only from what's actually in it

## Architecture

```
PDF upload
  → Gemini reads + classifies (unit / topic / marks / type / has_diagram)
  → saved to Supabase (papers + questions tables)
  → if any question has_diagram = true:
      render PDF page to image (PyMuPDF)
      → ask Gemini for bounding box coordinates
      → crop with Pillow
      → upload to Supabase Storage
      → attach diagram_url to that question
  → frontend dashboard renders charts, question list with inline diagrams,
    and a scoped Q&A interface
```

## Tech stack

| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router, TypeScript, Tailwind), Recharts |
| Backend | FastAPI (Python) |
| AI | Google Gemini 2.5 Flash — multimodal PDF reading, classification, bounding-box detection, scoped Q&A |
| Database + Storage | Supabase (PostgreSQL + Storage) |
| Image processing | PyMuPDF (page rendering), Pillow (cropping) |

Built entirely on free tiers — no paid infrastructure required to run it.

## A few technical details worth noting

- **No OCR library.** Gemini 2.5 Flash reads PDFs — including scanned ones — directly as multimodal input, which removed an entire pipeline stage (and its failure modes) that a more traditional OCR-then-classify approach would need.
- **Diagram extraction is a two-pass AI step.** The first Gemini pass classifies questions and flags `has_diagram`. Only flagged questions trigger a second pass: render the source page as an image, ask Gemini for bounding box coordinates on that specific figure, then crop and store just that region — rather than processing every page as an image up front.
- **Two view modes for the question list**, since "paper order" and "grouped by unit" serve different use cases — reading through a paper the way a student would in the exam vs. studying by topic across the whole paper.

## Status

Core pipeline is fully working end-to-end: upload, classification, storage, dashboard analytics, diagram extraction and inline rendering, and scoped Q&A have all been tested against real SASTRA papers.

**Planned next:**
- Test classification against a wider variety of subjects and exam types to validate generalization
- Public deployment (Vercel + Render)

## Why this project

Built as a hands-on way to work through the practical parts of building with LLM APIs — multimodal input handling, structured output extraction, and scoping a Q&A feature to a specific document — rather than model training, which isn't the focus of this project.
