import { useState } from "react";
import type { PYQAnalysisPayload } from "../../types/api.types";

type PYQTab = 'frequency' | 'hot' | 'blueprint' | 'paper';

export default function PYQView({ payload }: { payload: PYQAnalysisPayload }) {
  const hasBlueprint = !!payload.blueprint && payload.blueprint.rows.length > 0;
  const hasPaper = !!payload.exam_paper && payload.exam_paper.sections.length > 0;
  const [activeTab, setActiveTab] = useState<PYQTab>('frequency');

  const tabs: { key: PYQTab; label: string; show: boolean }[] = [
    { key: 'frequency', label: 'Frequency', show: true },
    { key: 'hot', label: 'HOT', show: true },
    { key: 'blueprint', label: 'Blueprint', show: hasBlueprint },
    { key: 'paper', label: 'Paper', show: hasPaper },
  ];

  return (
    <div className="flex flex-col py-8">
      <div className="mb-6 flex flex-wrap justify-center gap-3">
        {tabs.filter(t => t.show).map(t => (
          <button
            key={t.key}
            onClick={() => setActiveTab(t.key)}
            className={`rounded-full border-2 px-5 py-2 font-haas-grot-text text-sm font-bold transition-all ${activeTab === t.key ? 'border-ink-black bg-electric-iris text-paper-white shadow-hard-sm' : 'border-transparent text-ink-black/60 hover:text-ink-black'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {activeTab === 'frequency' && (
        <div className="flex flex-col gap-4 max-w-3xl mx-auto w-full">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">Topic Frequency</h3>
          {(payload.topic_frequency ?? []).length === 0 ? (
            <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-8 shadow-hard-md text-center">
              <p className="font-haas-grot-text font-bold text-ink-black">No topics found in these PDFs</p>
              <p className="font-martian-mono text-xs text-ink-black/60 mt-2">Try adding another PYQ with different years — then re-analyze.</p>
            </div>
          ) : (
            <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md flex flex-col gap-6">
              {(payload.topic_frequency ?? []).map((tf, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <div className="flex justify-between font-haas-grot-text text-sm font-bold">
                    <span>{tf.topic} ({tf.question_count} Qs)</span>
                    <span>{(tf.percentage * 100).toFixed(1)}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-ink-black/10">
                    <div className="h-full bg-electric-iris" style={{ width: `${tf.percentage * 100}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'hot' && (
        <div className="flex flex-col gap-4 max-w-3xl mx-auto w-full">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">HOT Questions</h3>
          {(payload.predicted_questions ?? []).length === 0 ? (
            <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-8 shadow-hard-md text-center">
              <p className="font-haas-grot-text font-bold text-ink-black">No HOT questions yet</p>
              <p className="font-martian-mono text-xs text-ink-black/60 mt-2">Upload more PYQs to generate predictions.</p>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {(payload.predicted_questions ?? []).map((q, i) => (
                <div key={i} className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md">
                  <div className="mb-4 flex gap-2">
                    <span className="rounded-full bg-marker-red px-3 py-1 font-martian-mono text-xs font-bold uppercase text-paper-white">
                      {(q.probability_score * 100).toFixed(0)}% Match
                    </span>
                    <span className="rounded-full border-2 border-ink-black/20 bg-frost-blue px-3 py-1 font-martian-mono text-xs font-bold uppercase text-ink-black">
                      {q.bloom_level}
                    </span>
                  </div>
                  <p className="font-haas-grot-text text-lg text-ink-black mb-4">{q.question}</p>
                  <div className="font-martian-mono text-sm text-ink-black/60">Expected Marks: {q.expected_marks}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'blueprint' && hasBlueprint && (
        <div className="flex flex-col gap-4 max-w-4xl mx-auto w-full">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">Blueprint — {payload.blueprint!.total_marks} Marks</h3>
          <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="font-martian-mono text-xs uppercase text-ink-black/60 border-b-2 border-ink-black/10">
                  <th className="text-left py-2">Topic</th>
                  <th className="text-center">%</th>
                  <th className="text-center">Qs</th>
                  <th className="text-center">Marks</th>
                </tr>
              </thead>
              <tbody>
                {payload.blueprint!.rows.map((r, i) => (
                  <tr key={i} className="border-b border-ink-black/5 font-haas-grot-text font-bold">
                    <td className="py-3">{r.topic}</td>
                    <td className="text-center">{(r.percentage * 100).toFixed(1)}%</td>
                    <td className="text-center">{r.question_count}</td>
                    <td className="text-center">{r.marks}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'paper' && hasPaper && (
        <div className="flex flex-col gap-6 max-w-4xl mx-auto w-full">
          <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-8 shadow-hard-md">
            <h3 className="font-haas-grot-disp text-2xl font-bold text-ink-black text-center">{payload.exam_paper!.title}</h3>
            <p className="text-center font-martian-mono text-sm text-ink-black/60 mt-1">{payload.exam_paper!.time} • Max Marks: {payload.exam_paper!.max_marks}</p>
            <p className="text-center font-haas-grot-text text-sm mt-3 p-3 bg-frost-blue rounded-xl border border-ink-black/10">{payload.exam_paper!.instructions}</p>
            {payload.exam_paper!.sections.map((sec, si) => (
              <div key={si} className="mt-8">
                <h4 className="font-haas-grot-disp text-lg font-bold border-b-2 border-ink-black pb-2">{sec.name} — {sec.instructions}</h4>
                <div className="mt-4 flex flex-col gap-4">
                  {sec.questions.map((q) => (
                    <div key={q.q_no} className="rounded-xl border-2 border-ink-black/10 p-4">
                      <div className="flex gap-2 mb-2">
                        <span className="font-martian-mono text-xs font-bold">Q{q.q_no}.</span>
                        <span className="rounded-full bg-frost-blue px-2 py-0.5 font-martian-mono text-xs">{q.bloom_level}</span>
                        <span className="font-martian-mono text-xs text-ink-black/60">{q.expected_marks}M • {(q.probability_score*100).toFixed(0)}%</span>
                        <span className="font-martian-mono text-xs text-ink-black/60">• {q.topic}</span>
                      </div>
                      <p className="font-haas-grot-text">{q.question}</p>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* fallback: show both when no tabs */}
      {!hasBlueprint && !hasPaper && (
        <div className="grid gap-6 md:grid-cols-2 mt-6">
          <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md flex flex-col gap-6">
            {payload.topic_frequency.slice(0,3).map((tf,i)=> (
              <div key={i} className="flex justify-between text-sm font-bold"><span>{tf.topic}</span><span>{(tf.percentage*100).toFixed(1)}%</span></div>
            ))}
          </div>
          <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md">
            <p className="font-haas-grot-text">Upload more PYQs to generate blueprint and predicted paper.</p>
          </div>
        </div>
      )}
    </div>
  );
}
