import type { EngineResponse, SyllabusPayload, PYQAnalysisPayload, NotesPayload } from "../../types/api.types";
import type { ExportPayload } from "../../types/export";
import { exportStudyAssets } from "../../services/exportService";
import SyllabusView from "../../features/syllabus-view/SyllabusView";
import PYQView from "../../features/pyq-view/PYQView";
import NotesView from "../../features/notes-view/NotesView";

type NotesTab = 'flashcards' | 'exam' | 'summary';

type ViewSwitcherProps = {
  data: EngineResponse;
  onReset: () => void;
  onGenerateNotes?: (subtask: NotesTab) => void;
};

export default function ViewSwitcher({ data, onReset, onGenerateNotes }: ViewSwitcherProps) {
  const { classification, payload } = data;
  const docType = classification.doc_type;

  return (
    <div className="w-full flex flex-col pt-4 pb-12">
      {/* Header / Classification Badge */}
      <div className="flex flex-col sm:flex-row items-center justify-between mb-8 gap-4 border-b-2 border-ink-black pb-4">
        <div className="flex items-center gap-3">
          <span className="material-symbols-outlined text-electric-iris text-3xl">magic_button</span>
          <h2 className="font-haas-grot-disp text-2xl font-bold text-ink-black">Analysis Complete</h2>
        </div>
        
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 rounded-full bg-electric-iris px-4 py-1.5 shadow-hard-sm">
            <span className="font-martian-mono text-xs font-bold uppercase tracking-wider text-paper-white">
              {docType} Detected
            </span>
            <span className="h-4 w-px bg-paper-white/30" />
            <span className="font-martian-mono text-xs font-bold text-paper-white">
              {(classification.confidence * 100).toFixed(0)}% Match
            </span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => payload && exportStudyAssets(payload as ExportPayload, { format: 'pdf', docType: classification.doc_type })}
              disabled={!payload}
              className="hover-press flex items-center gap-1.5 rounded-full border-2 border-ink-black bg-paper-white px-3 py-1.5 font-haas-grot-text text-xs font-bold text-ink-black shadow-hard-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <span className="material-symbols-outlined text-[16px]">picture_as_pdf</span>
              PDF
            </button>
            {(classification.doc_type === 'NOTES' || classification.doc_type === 'PYQ') && (
              <button
                onClick={() => payload && exportStudyAssets(payload as ExportPayload, { format: 'csv', docType: classification.doc_type })}
                disabled={!payload}
                className="hover-press flex items-center gap-1.5 rounded-full border-2 border-ink-black bg-paper-white px-3 py-1.5 font-haas-grot-text text-xs font-bold text-ink-black shadow-hard-sm disabled:opacity-40 disabled:cursor-not-allowed"
              >
                <span className="material-symbols-outlined text-[16px]">description</span>
                CSV
              </button>
            )}
          </div>
          
          <button 
            onClick={onReset}
            className="flex items-center gap-2 rounded-full border-2 border-ink-black bg-paper-white px-4 py-1.5 font-haas-grot-text text-sm font-bold text-ink-black shadow-hard-sm hover-press transition-all"
          >
            <span className="material-symbols-outlined text-[18px]">upload_file</span>
            Upload Another
          </button>
        </div>
      </div>

      {/* Main Content Area Routing */}
      <div className="w-full animate-in fade-in duration-500">
        {docType === 'SYLLABUS' && (
          <SyllabusView payload={payload as SyllabusPayload} />
        )}
        
        {docType === 'PYQ' && (
          <PYQView payload={payload as PYQAnalysisPayload} />
        )}
        
        {docType === 'NOTES' && (
          <NotesView payload={payload as NotesPayload} onGenerateMore={onGenerateNotes} />
        )}
      </div>
    </div>
  );
}
