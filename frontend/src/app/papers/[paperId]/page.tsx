import Link from "next/link";
import { getPaper, getPaperSummary } from "@/lib/api";
import UnitChart from "@/components/UnitChart";
import QuestionTypeChart from "@/components/QuestionTypeChart";
import QuestionList from "@/components/QuestionList";
import AskPaper from "@/components/AskPaper";

interface Props {
  params: Promise<{ paperId: string }>;
}

export default async function PaperDashboard({ params }: Props) {
  const { paperId } = await params;

  const [{ paper, questions }, summary] = await Promise.all([
    getPaper(paperId),
    getPaperSummary(paperId),
  ]);

  return (
    <main className="mx-auto w-full max-w-4xl flex-1 px-6 py-12">
      <Link
        href="/"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-graphite transition-colors hover:text-paper"
      >
        ← Upload another paper
      </Link>

      <header className="mb-10">
        <p className="mb-2 font-mono text-xs uppercase tracking-[0.18em] text-red-pen">
          {paper.exam_type}
          {paper.department ? ` · ${paper.department}` : ""}
          {paper.year ? ` · ${paper.year}` : ""}
        </p>
        <h1 className="font-serif text-3xl font-semibold text-paper">
          {paper.subject_name}
        </h1>
        <p className="mt-2 text-sm text-graphite">
          {summary.total_questions} questions · {summary.total_marks} total marks
        </p>
      </header>

      <div className="mb-6 grid gap-6 sm:grid-cols-2">
        <UnitChart
          unitDistribution={summary.unit_distribution}
          marksByUnit={summary.marks_by_unit}
        />
        <QuestionTypeChart
          questionTypeDistribution={summary.question_type_distribution}
        />
      </div>

      <div className="mb-6">
        <AskPaper paperId={paperId} />
      </div>

      <QuestionList questions={questions} />
    </main>
  );
}
