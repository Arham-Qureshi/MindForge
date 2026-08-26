import type { SyllabusPayload } from '../../types/api.types';

const COGNITIVE_COLORS: Record<string, string> = {
  Remember: 'border-l-frost-blue',
  Understand: 'border-l-electric-iris',
  Apply: 'border-l-hi-yellow',
  Analyze: 'border-l-marker-green',
  Evaluate: 'border-l-marker-red',
  Create: 'border-l-ink-black',
};

type SyllabusRoadmapProps = {
  payload: SyllabusPayload;
};

export default function SyllabusRoadmap({ payload }: SyllabusRoadmapProps) {
  const prioritySet = new Set(payload.priority_topics.map((p) => p.topic));

  return (
    <div className="mx-auto max-w-2xl">
      <h3 className="mb-1 font-haas-grot-disp text-xl font-bold text-ink-black">
        {payload.course_title}
      </h3>
      <p className="mb-6 font-martian-mono text-sm text-ink-black/60">
        {payload.total_units} units · {payload.learning_path.reduce((s, u) => s + u.estimated_hours, 0)}h estimated
      </p>

      <div className="relative ml-4 border-l-2 border-ink-black/20">
        {payload.learning_path.map((unit) => (
          <div key={unit.unit_number} className="relative mb-6 pl-8">
            <div className="absolute -left-[1.15rem] top-1 h-4 w-4 rounded-full border-2 border-ink-black bg-electric-iris" />
            <div className={`rounded-lg border-2 border-ink-black bg-paper-white p-4 shadow-hard-sm border-l-4 ${COGNITIVE_COLORS[unit.cognitive_level] || 'border-l-ink-black'}`}>
              <div className="mb-2 flex items-center justify-between">
                <h4 className="font-haas-grot-disp text-base font-bold text-ink-black">
                  Unit {unit.unit_number}: {unit.title}
                </h4>
                <div className="flex items-center gap-2">
                  <span className="rounded-full bg-frost-blue px-2 py-0.5 font-martian-mono text-xs font-bold text-ink-black">
                    {unit.estimated_hours}h
                  </span>
                  <span className="rounded-full bg-electric-iris/10 px-2 py-0.5 font-martian-mono text-xs font-bold text-electric-iris">
                    {unit.cognitive_level}
                  </span>
                </div>
              </div>
              <ul className="space-y-1">
                {unit.topics.map((topic) => (
                  <li key={topic} className="flex items-center gap-2 font-haas-grot-text text-sm text-ink-black/80">
                    <span className="h-1 w-1 flex-shrink-0 rounded-full bg-ink-black/40" />
                    {topic}
                    {prioritySet.has(topic) && <span className="text-hi-yellow">★</span>}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
