import type { PYQAnalysisPayload } from "../../types/api.types";

export default function PYQView({ payload }: { payload: PYQAnalysisPayload }) {
  return (
    <div className="flex flex-col gap-8 py-8">
      <div className="grid gap-6 md:grid-cols-2">
        <div className="flex flex-col gap-4">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">Topic Frequency</h3>
          <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md flex flex-col gap-6">
            {payload.topic_frequency.map((tf, i) => (
              <div key={i} className="flex flex-col gap-2">
                <div className="flex justify-between font-haas-grot-text text-sm font-bold">
                  <span>{tf.topic} ({tf.question_count} Qs)</span>
                  <span>{tf.percentage}%</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-ink-black/10">
                  <div 
                    className="h-full bg-electric-iris" 
                    style={{ width: `${tf.percentage}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">HOT Questions</h3>
          <div className="flex flex-col gap-4">
            {payload.predicted_questions.map((q, i) => (
              <div key={i} className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md">
                <div className="mb-4 flex gap-2">
                  <span className="rounded-full bg-marker-red px-3 py-1 font-martian-mono text-xs font-bold uppercase text-paper-white">
                    {q.probability_score}% Match
                  </span>
                  <span className="rounded-full border-2 border-ink-black/20 bg-frost-blue px-3 py-1 font-martian-mono text-xs font-bold uppercase text-ink-black">
                    {q.bloom_level}
                  </span>
                </div>
                <p className="font-haas-grot-text text-lg text-ink-black mb-4">
                  {q.question}
                </p>
                <div className="font-martian-mono text-sm text-ink-black/60">
                  Expected Marks: {q.expected_marks}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
