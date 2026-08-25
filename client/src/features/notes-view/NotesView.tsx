import { useState } from 'react';
import type { NotesPayload } from "../../types/api.types";
import FlashcardDeck from "./components/FlashcardDeck";

type NotesTab = 'flashcards' | 'exam' | 'summary';

export default function NotesView({ payload }: { payload: NotesPayload }) {
  const [activeTab, setActiveTab] = useState<NotesTab>('flashcards');

  return (
    <div className="flex flex-col py-8">
      {/* Sub-tabs */}
      <div className="mb-8 flex flex-wrap justify-center gap-4">
        <button 
          onClick={() => setActiveTab('flashcards')}
          className={`rounded-full border-2 px-6 py-2 font-haas-grot-text font-bold transition-all ${
            activeTab === 'flashcards' 
              ? 'border-ink-black bg-electric-iris text-paper-white shadow-hard-sm' 
              : 'border-transparent text-ink-black/60 hover:text-ink-black'
          }`}
        >
          Flashcards
        </button>
        <button 
          onClick={() => setActiveTab('exam')}
          className={`rounded-full border-2 px-6 py-2 font-haas-grot-text font-bold transition-all ${
            activeTab === 'exam' 
              ? 'border-ink-black bg-electric-iris text-paper-white shadow-hard-sm' 
              : 'border-transparent text-ink-black/60 hover:text-ink-black'
          }`}
        >
          Practice Exam
        </button>
        <button 
          onClick={() => setActiveTab('summary')}
          className={`rounded-full border-2 px-6 py-2 font-haas-grot-text font-bold transition-all ${
            activeTab === 'summary' 
              ? 'border-ink-black bg-electric-iris text-paper-white shadow-hard-sm' 
              : 'border-transparent text-ink-black/60 hover:text-ink-black'
          }`}
        >
          Summary
        </button>
      </div>

      {/* Tab Content */}
      <div className="w-full">
        {activeTab === 'flashcards' && (
          <FlashcardDeck flashcards={payload.flashcards} />
        )}
        
        {activeTab === 'exam' && (
          <div className="flex flex-col gap-6 w-full max-w-3xl mx-auto">
            {payload.practice_exam.map((q, i) => (
              <div key={i} className="rounded-[24px] border-2 border-ink-black bg-paper-white p-8 shadow-hard-md">
                <h3 className="font-haas-grot-text text-xl font-bold mb-6 text-ink-black">
                  {i + 1}. {q.question}
                </h3>
                <div className="flex flex-col gap-3">
                  {q.options.map((opt, j) => (
                    <div key={j} className="flex items-center gap-3 p-3 rounded-xl border-2 border-ink-black/10 hover:border-electric-iris hover:bg-frost-blue transition-colors cursor-pointer">
                      <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 border-ink-black font-martian-mono text-xs font-bold">
                        {String.fromCharCode(65 + j)}
                      </div>
                      <span className="font-haas-grot-text text-ink-black">{opt}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
        
        {activeTab === 'summary' && (
          <div className="w-full max-w-3xl mx-auto rounded-[24px] border-2 border-ink-black bg-paper-white p-8 shadow-hard-md">
            <h3 className="font-haas-grot-disp text-2xl font-bold mb-6 border-b-2 border-ink-black pb-4">Document Summary</h3>
            <p className="font-haas-grot-text text-lg leading-relaxed text-ink-black whitespace-pre-wrap">
              {payload.document_summary}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
