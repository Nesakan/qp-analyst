"use client";

import { useState } from "react";
import { askAboutPaper, ApiError } from "@/lib/api";

interface Props {
  paperId: string;
}

interface Exchange {
  question: string;
  answer: string;
}

export default function AskPaper({ paperId }: Props) {
  const [question, setQuestion] = useState("");
  const [exchanges, setExchanges] = useState<Exchange[]>([]);
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleAsk(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || isAsking) return;

    setIsAsking(true);
    setError(null);
    setQuestion("");

    try {
      const { answer } = await askAboutPaper(paperId, q);
      setExchanges((prev) => [...prev, { question: q, answer }]);
    } catch (err) {
      setError(
        err instanceof ApiError ? err.message : "Couldn't reach the server."
      );
    } finally {
      setIsAsking(false);
    }
  }

  return (
    <div className="rounded-sm border border-ink-line bg-ink-raised">
      <div className="border-b border-ink-line px-6 py-4">
        <h3 className="font-serif text-base text-paper">Ask this paper</h3>
        <p className="text-xs text-graphite">
          Questions are answered using only the text of this paper
        </p>
      </div>

      {exchanges.length > 0 && (
        <div className="flex flex-col gap-4 px-6 py-4 max-h-80 overflow-y-auto">
          {exchanges.map((ex, i) => (
            <div key={i} className="flex flex-col gap-2">
              <p className="text-sm text-paper">
                <span className="font-mono text-red-pen">Q.</span> {ex.question}
              </p>
              <p className="text-sm text-graphite">{ex.answer}</p>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleAsk} className="flex gap-2 px-6 py-4">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="e.g. Were there any questions on normalization?"
          disabled={isAsking}
          className="flex-1 rounded-sm border border-ink-line bg-ink px-3 py-2 text-sm text-paper placeholder:text-graphite/60 outline-none focus:border-red-pen disabled:opacity-60"
        />
        <button
          type="submit"
          disabled={isAsking || !question.trim()}
          className="shrink-0 rounded-sm bg-red-pen px-4 py-2 text-sm font-medium text-ink transition-opacity hover:opacity-90 disabled:opacity-40"
        >
          {isAsking ? "Asking…" : "Ask"}
        </button>
      </form>

      {error && (
        <p className="px-6 pb-4 text-sm text-red-pen">{error}</p>
      )}
    </div>
  );
}
