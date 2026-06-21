"use client";

import { useState } from "react";
import type { ExtractedQuestion } from "@/lib/types";

interface Props {
  questions: ExtractedQuestion[];
}

type SortMode = "paper" | "unit";

// Splits "17b" into [17, "b"] and "10" into [10, ""] so numbers compare
// numerically and letter suffixes break ties (11a before 11b).
function parseQuestionNumber(qNum: string): [number, string] {
  const match = qNum.match(/^(\d+)([a-zA-Z]*)$/);
  if (!match) return [0, qNum];
  return [parseInt(match[1], 10), match[2]];
}

function comparePaperOrder(a: ExtractedQuestion, b: ExtractedQuestion): number {
  const [aNum, aSuffix] = parseQuestionNumber(a.question_number);
  const [bNum, bSuffix] = parseQuestionNumber(b.question_number);
  if (aNum !== bNum) return aNum - bNum;
  return aSuffix.localeCompare(bSuffix);
}

function compareUnitOrder(a: ExtractedQuestion, b: ExtractedQuestion): number {
  if (a.unit !== b.unit) return a.unit - b.unit;
  return comparePaperOrder(a, b);
}

export default function QuestionList({ questions }: Props) {
  const [sortMode, setSortMode] = useState<SortMode>("paper");

  const sorted = [...questions].sort(
    sortMode === "paper" ? comparePaperOrder : compareUnitOrder
  );

  return (
    <div className="rounded-sm border border-ink-line bg-ink-raised">
      <div className="flex items-center justify-between border-b border-ink-line px-6 py-4">
        <div>
          <h3 className="font-serif text-base text-paper">All questions</h3>
          <p className="text-xs text-graphite">
            Every question extracted from this paper, with its unit and topic
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-1 rounded-full border border-ink-line bg-ink p-0.5 text-xs">
          <button
            type="button"
            onClick={() => setSortMode("paper")}
            className={`rounded-full px-3 py-1 font-mono transition-colors ${
              sortMode === "paper"
                ? "bg-red-pen text-ink"
                : "text-graphite hover:text-paper"
            }`}
          >
            Paper order
          </button>
          <button
            type="button"
            onClick={() => setSortMode("unit")}
            className={`rounded-full px-3 py-1 font-mono transition-colors ${
              sortMode === "unit"
                ? "bg-red-pen text-ink"
                : "text-graphite hover:text-paper"
            }`}
          >
            Unit order
          </button>
        </div>
      </div>

      <ul className="divide-y divide-ink-line">
        {sorted.map((q) => (
          <li key={q.id} className="flex items-start gap-4 px-6 py-4">
            {/* red-pen marks circle — the signature element */}
            <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border border-red-pen font-mono text-xs text-red-pen">
              {q.marks}
            </span>

            <div className="min-w-0 flex-1">
              <p className="text-sm text-paper">
                <span className="font-mono text-graphite">
                  Q{q.question_number}
                </span>{" "}
                {q.question_text}
              </p>
              <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded-full bg-verified-dim px-2 py-0.5 text-verified">
                  Unit {q.unit}
                </span>
                <span className="rounded-full bg-ink px-2 py-0.5 text-graphite">
                  {q.topic}
                </span>
                <span className="text-graphite/70">{q.question_type}</span>
              </div>
              {q.diagram_url && (
                // eslint-disable-next-line @next/next/no-img-element
                <img
                  src={q.diagram_url}
                  alt={`Diagram for question ${q.question_number}`}
                  className="mt-3 max-w-md rounded-sm border border-ink-line bg-paper"
                />
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
