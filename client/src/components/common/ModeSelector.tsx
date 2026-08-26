import type { ProcessingMode } from '../../types/api.types';

type ModeSelectorProps = {
  activeMode: ProcessingMode;
  onModeChange: (mode: ProcessingMode) => void;
};

const modes: { key: ProcessingMode; label: string }[] = [
  { key: 'notes', label: 'Summary' },
  { key: 'pyq', label: 'PYQ' },
  { key: 'syllabus', label: 'Syllabus Graph' },
];

export default function ModeSelector({ activeMode, onModeChange }: ModeSelectorProps) {
  return (
    <div className="mx-auto flex w-fit gap-1 rounded-full border-2 border-ink-black bg-paper-white p-1">
      {modes.map(({ key, label }) => {
        const isActive = activeMode === key;
        return (
          <button
            key={key}
            onClick={() => onModeChange(key)}
            className={`rounded-full px-6 py-2 font-haas-grot-text text-sm font-bold transition-colors ${
              isActive
                ? 'bg-electric-iris text-paper-white'
                : 'bg-paper-white text-ink-black hover:bg-frost-blue'
            }`}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
