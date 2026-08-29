import { useEffect, useState } from "react";
import { Agentation } from "agentation";
import MainLayout from "./components/layout/MainLayout";
import Dropzone from "./components/common/Dropzone";
import ModeSelector from "./components/common/ModeSelector";
import ProcessingView from "./components/common/ProcessingView";
import ViewSwitcher from "./components/common/ViewSwitcher";
import { useJobSession } from "./hooks/useJobSession";
import type { JobAccepted, ProcessingMode } from "./types/api.types";

type NotesTab = 'flashcards' | 'exam' | 'summary';

function App() {
  const { phase, startJob, reset, kill, generateMore } = useJobSession();
  const [mode, setMode] = useState<ProcessingMode>("notes");
  const [flashcardCount, setFlashcardCount] = useState(10);
  const [showMismatchToast, setShowMismatchToast] = useState(false);

  const handleAccepted = (job: JobAccepted, file: File) => {
    startJob(job, file);
    if (job.mode_mismatch) {
      setShowMismatchToast(true);
    }
  };

  const handleGenerateNotes = (subtask: NotesTab, count?: number) => {
    generateMore('notes', count ?? flashcardCount, subtask);
  };

  useEffect(() => {
    if (!showMismatchToast) return;
    const timer = setTimeout(() => setShowMismatchToast(false), 4000);
    return () => clearTimeout(timer);
  }, [showMismatchToast]);

  return (
    <>
      <MainLayout phase={phase}>
        {phase.kind === 'idle' && (
          <>
            <ModeSelector activeMode={mode} onModeChange={setMode} />
            <Dropzone
              onAccepted={handleAccepted}
              onReset={reset}
              mode={mode}
              flashcardCount={flashcardCount}
              onFlashcardCountChange={setFlashcardCount}
            />
          </>
        )}

        {phase.kind === 'processing' && (
          <ProcessingView
            chunksTotal={phase.job.chunks_total}
            chunksDone={phase.chunksDone}
            onCancel={kill}
          />
        )}

        {phase.kind === 'ready' && (
          <>
            <div className="mb-6 rounded-lg border-2 border-ink-black bg-frost-blue/20 p-4">
              <p className="mb-3 font-haas-grot-text text-sm font-bold text-ink-black">Generate more from this document:</p>
              <div className="flex gap-2">
                {(['notes', 'pyq', 'syllabus'] as ProcessingMode[]).map((m) => {
                  const isActive = m === phase.data.classification.doc_type.toLowerCase();
                  return (
                    <button
                      key={m}
                      onClick={() => !isActive && generateMore(m, m === 'notes' ? flashcardCount : undefined)}
                      disabled={isActive}
                      className={`rounded-full border-2 px-4 py-1.5 text-xs font-bold transition-all ${
                        isActive
                          ? 'border-electric-iris bg-electric-iris text-paper-white cursor-default'
                          : 'border-ink-black bg-paper-white text-ink-black hover-press shadow-hard-xs'
                      }`}
                    >
                      {m === 'notes' ? 'Summary' : m === 'pyq' ? 'PYQ' : 'Syllabus Graph'}
                    </button>
                  );
                })}
              </div>
            </div>
            <ViewSwitcher data={phase.data} onReset={reset} onGenerateNotes={handleGenerateNotes} />
          </>
        )}

        {phase.kind === 'failed' && (
          <div className="mx-auto flex w-full max-w-2xl flex-col items-center gap-4 py-20">
            <span className="material-symbols-outlined text-5xl text-marker-red">error</span>
            <h3 className="font-haas-grot-disp text-2xl font-bold text-ink-black">Processing Failed</h3>
            <p className="max-w-lg text-center font-haas-grot-text text-ink-black/70">{phase.message}</p>
            <button
              onClick={reset}
              className="mt-4 rounded-full border-2 border-ink-black bg-paper-white px-6 py-2 text-sm font-bold text-ink-black shadow-hard-sm hover-press"
            >
              Try Another Upload
            </button>
          </div>
        )}
      </MainLayout>
      {showMismatchToast && (
        <div className="fixed bottom-8 left-1/2 -translate-x-1/2 rounded-full border-2 border-ink-black bg-hi-yellow px-6 py-3 font-haas-grot-text text-sm font-bold text-ink-black shadow-hard-md">
          Document classified differently, but we'll process as you requested.
        </div>
      )}
      {import.meta.env.MODE === "development" && <Agentation />}
    </>
  );
}

export default App;
