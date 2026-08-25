import type { SyllabusPayload } from "../../types/api.types";

export default function SyllabusView({ payload }: { payload: SyllabusPayload }) {
  return (
    <div className="flex flex-col gap-8 py-8">
      <div>
        <h2 className="font-haas-grot-disp text-3xl font-bold text-ink-black mb-2">
          {payload.course_title}
        </h2>
        <p className="font-haas-grot-text text-ink-black/70">
          {payload.total_units} Units Total
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <div className="flex flex-col gap-4">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">Learning Path</h3>
          {payload.learning_path.map((unit) => (
            <div key={unit.unit_number} className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md">
              <div className="mb-4 flex items-center justify-between">
                <h4 className="font-haas-grot-disp text-lg font-bold">Unit {unit.unit_number}: {unit.title}</h4>
                <span className="rounded-full bg-electric-iris px-3 py-1 font-martian-mono text-xs font-bold uppercase text-paper-white">
                  {unit.cognitive_level}
                </span>
              </div>
              <p className="mb-4 font-martian-mono text-sm text-ink-black/60">
                {unit.estimated_hours} Hours
              </p>
              <div className="flex flex-wrap gap-2">
                {unit.topics.map((topic, i) => (
                  <span key={i} className="rounded-full border-2 border-ink-black/20 bg-frost-blue px-3 py-1 text-sm text-ink-black">
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="flex flex-col gap-4">
          <h3 className="font-haas-grot-disp text-xl font-bold text-ink-black">Priority Topics</h3>
          <div className="rounded-[24px] border-2 border-ink-black bg-paper-white p-6 shadow-hard-md">
            <div className="flex flex-col gap-4">
              {payload.priority_topics.map((pt, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <div className="flex justify-between font-haas-grot-text text-sm font-bold">
                    <span>{pt.topic}</span>
                    <span>{pt.weightage}%</span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-ink-black/10">
                    <div 
                      className="h-full bg-electric-iris" 
                      style={{ width: `${pt.weightage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
