// Mirrors backend/models.py — keep these in sync manually.
// At this project's scale, two files staying in sync by hand is simpler
// than adding a codegen step; revisit if the schema grows significantly.

export type ExamType =
  | "CIA-1"
  | "CIA-2"
  | "CIA-3"
  | "End Semester"
  | "Model Exam";

export type QuestionType =
  | "Theory"
  | "Numerical"
  | "Diagram"
  | "Derivation"
  | "Programming";

export interface Paper {
  id: string;
  filename: string;
  subject_name: string;
  exam_type: ExamType;
  department: string | null;
  year: number | null;
  uploaded_at: string;
  question_count: number;
}

export interface ExtractedQuestion {
  id: string;
  paper_id: string;
  question_number: string;
  question_text: string;
  unit: number;
  topic: string;
  marks: number;
  question_type: QuestionType;
  has_diagram: boolean;
  diagram_url: string | null;
}

export interface PaperDetail {
  paper: {
    id: string;
    filename: string;
    subject_name: string;
    exam_type: ExamType;
    department: string | null;
    year: number | null;
    uploaded_at: string;
    raw_text: string;
  };
  questions: ExtractedQuestion[];
}

export interface PaperSummary {
  paper_id: string;
  unit_distribution: Record<string, number>;
  marks_by_unit: Record<string, number>;
  question_type_distribution: Record<string, number>;
  total_marks: number;
  total_questions: number;
}

export interface UploadResponse {
  paper_id: string;
  question_count: number;
}