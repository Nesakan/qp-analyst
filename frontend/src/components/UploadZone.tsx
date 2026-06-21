"use client";

import { useCallback, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { uploadPaper, ApiError } from "@/lib/api";

type UploadState =
  | { status: "idle" }
  | { status: "reading"; filename: string }
  | { status: "error"; message: string };

export default function UploadZone() {
  const router = useRouter();
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setState({
          status: "error",
          message: "Only PDF files are accepted. Pick a .pdf question paper.",
        });
        return;
      }

      setState({ status: "reading", filename: file.name });

      try {
        const result = await uploadPaper(file);
        router.push(`/papers/${result.paper_id}`);
      } catch (err) {
        const message =
          err instanceof ApiError
            ? err.message
            : "Couldn't reach the server. Is the backend running?";
        setState({ status: "error", message });
      }
    },
    [router]
  );

  const onDrop = useCallback(
    (e: React.DragEvent<HTMLDivElement>) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files?.[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const isReading = state.status === "reading";

  return (
    <div className="w-full max-w-2xl">
      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => !isReading && inputRef.current?.click()}
        className={`relative flex flex-col items-center justify-center gap-4 rounded-sm border-2 border-dashed px-8 py-16 text-center transition-colors cursor-pointer
          ${isDragging ? "border-red-pen bg-red-pen-dim/20" : "border-ink-line hover:border-graphite"}
          ${isReading ? "pointer-events-none opacity-70" : ""}`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) handleFile(file);
          }}
        />

        {isReading ? (
          <>
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-graphite border-t-red-pen" />
            <p className="font-mono text-sm text-graphite">
              Reading {state.filename}…
            </p>
            <p className="text-xs text-graphite/70 max-w-xs">
              Gemini is transcribing the paper and classifying each question.
              This usually takes 10–20 seconds.
            </p>
          </>
        ) : (
          <>
            <svg
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              className="text-graphite"
            >
              <path
                d="M12 16V4M12 4L7 9M12 4l5 5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M4 16v2a2 2 0 002 2h12a2 2 0 002-2v-2"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <p className="font-serif text-lg text-paper">
              Drop a question paper here
            </p>
            <p className="text-sm text-graphite">
              or click to choose a PDF — scanned or typed, both work
            </p>
          </>
        )}
      </div>

      {state.status === "error" && (
        <p className="mt-3 flex items-start gap-2 text-sm text-red-pen">
          <span className="font-mono">✕</span>
          {state.message}
        </p>
      )}
    </div>
  );
}
