import type { PYQAnalysisPayload } from '../../types/api.types';

const BLOOM_COLORS: Record<string, string> = {
  Apply: 'bg-hi-yellow text-ink-black',
  Analyze: 'bg-marker-green text-paper-white',
  Evaluate: 'bg-marker-red text-paper-white',
};

type PYQPreviewProps = {
  payload: PYQAnalysisPayload;
};

export default function PYQPreview({ payload }: PYQPreviewProps) {
  return (
    <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
      <div>
        <h4 className="mb-4 font-haas-grot-disp text-lg font-bold text-ink-black">Topic Frequency</h4>
        <div className="space-y-3">
          {payload.topic_frequency.map((tf) => (
            <div key={tf.topic}>
              <div className="mb-1 flex justify-between font-haas-grot-text text-sm">
                <span className="font-bold text-ink-black">{tf.topic}</span>
                <span className="text-ink-black/60">{tf.question_count} questions</span>
              </div>
              <div className="h-3 rounded-full bg-frost-blue/30">
                <div className="h-full rounded-full bg-electric-iris transition-all" style={{ width: `${tf.percentage * 100}%` }} />
              </div>
              <span className="font-martian-mono text-xs text-ink-black/50">{(tf.percentage * 100).toFixed(0)}%</span>
            </div>
          ))}
        </div>
      </div>
      <div>
        <h4 className="mb-4 font-haas-grot-disp text-lg font-bold text-ink-black">Predicted Questions</h4>
        <div className="space-y-3">
          {payload.predicted_questions.map((pq, i) => (
            <div key={i} className="rounded-lg border-2 border-ink-black bg-paper-white p-3 shadow-hard-xs">
              <div className="mb-2 flex items-start justify-between gap-2">
                <span className={`rounded-full px-2 py-0.5 font-martian-mono text-xs font-bold ${BLOOM_COLORS[pq.bloom_level] || 'bg-frost-blue text-ink-black'}`}>
                  {pq.bloom_level}
                </span>
                <span className="font-martian-mono text-xs text-ink-black/50">
                  {pq.expected_marks} marks · {(pq.probability_score * 100).toFixed(0)}%
                </span>
              </div>
              <p className="font-haas-grot-text text-sm text-ink-black">{pq.question}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
