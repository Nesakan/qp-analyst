import UploadZone from "@/components/UploadZone";

export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-6 py-20">
      <div className="mb-12 max-w-2xl text-center">
        <p className="mb-3 font-mono text-xs uppercase tracking-[0.18em] text-red-pen">
          SASTRA Question Paper Analyst
        </p>
        <h1 className="font-serif text-4xl font-semibold leading-tight text-paper sm:text-5xl">
          See what actually gets tested,
          <br />
          before the exam does.
        </h1>
        <p className="mx-auto mt-5 max-w-md text-base text-graphite">
          Upload a past paper. We read every question, tag it by unit and
          topic, and show you where the marks really go.
        </p>
      </div>

      <UploadZone />
    </main>
  );
}
