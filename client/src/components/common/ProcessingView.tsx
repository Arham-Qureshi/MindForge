type ProcessingViewProps = {
  chunksTotal: number;
  chunksDone: number;
  onCancel?: () => void;
};

export default function ProcessingView({ chunksTotal, chunksDone, onCancel }: ProcessingViewProps) {
  return (
    <div className="flex flex-col items-center justify-center py-20">
      <div
        role="status"
        aria-label={`Processing ${chunksDone} of ${chunksTotal} chunks`}
        className="mb-8 flex flex-wrap items-center justify-center gap-2"
        data-testid="chunk-boxes"
      >
        {Array.from({ length: Math.max(chunksTotal, 1) }).map((_, i) => (
          <div
            key={i}
            className={`chunk-box ${i < chunksDone ? 'chunk-done' : 'chunk-pending'}`}
            style={i < chunksDone ? undefined : { animationDelay: `${i * 0.15}s` }}
          />
        ))}
      </div>

      <h3 className="font-haas-grot-disp text-2xl font-bold text-ink-black">
        Cooking your study assets...
      </h3>
      <p className="mt-3 font-martian-mono text-sm uppercase tracking-wider text-ink-black/60" data-testid="chunk-counter">
        {chunksDone}/{chunksTotal} chunks processed
      </p>

      {onCancel && (
        <button
          onClick={onCancel}
          className="mt-10 flex items-center gap-2 rounded-full border-2 border-marker-red bg-paper-white px-6 py-2 text-sm font-bold text-marker-red shadow-hard-sm hover-press transition-all"
          data-testid="kill-job"
        >
          <span className="material-symbols-outlined text-[18px]">cancel</span>
          Stop Processing
        </button>
      )}
    </div>
  );
}
