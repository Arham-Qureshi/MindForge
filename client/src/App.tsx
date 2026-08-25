import MainLayout from "./components/layout/MainLayout";
import Dropzone from "./components/common/Dropzone";
import ProcessingView from "./components/common/ProcessingView";
import ViewSwitcher from "./components/common/ViewSwitcher";
import { useJobSession } from "./hooks/useJobSession";

function App() {
  const { phase, startJob, reset, kill } = useJobSession();

  return (
    <MainLayout>
      {phase.kind === 'idle' && (
        <Dropzone onAccepted={startJob} onReset={reset} />
      )}

      {phase.kind === 'processing' && (
        <ProcessingView
          chunksTotal={phase.job.chunks_total}
          chunksDone={phase.chunksDone}
          onCancel={kill}
        />
      )}

      {phase.kind === 'ready' && (
        <ViewSwitcher data={phase.data} onReset={reset} />
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
  );
}

export default App;
