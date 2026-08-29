import { useState } from 'react';
import type { NotesPayload } from "../../types/api.types";
import FlashcardDeck from "./components/FlashcardDeck";

type NotesTab = 'flashcards' | 'exam' | 'summary';

type NotesViewProps = {
  payload: NotesPayload;
  onGenerateMore?: (subtask: NotesTab) => void;
};

export default function NotesView({ payload, onGenerateMore }: NotesViewProps) {
  const [activeTab, setActiveTab] = useState<NotesTab>(() => {
    if (payload.flashcards.length > 0) return 'flashcards';
    if (payload.practice_exam.length > 0) return 'exam';
    return 'summary';
  });

  const tabs: { key: NotesTab; label: string; hasData: boolean }[] = [
    { key: 'flashcards', label: 'Flashcards', hasData: payload.flashcards.length > 0 },
    { key: 'exam', label: 'Practice Exam', hasData: payload.practice_exam.length > 0 },
    { key: 'summary', label: 'Summary', hasData: !!payload.document_summary },
  ];

  const visibleTabs = tabs.filter(t => t.hasData);

  if (visibleTabs.length === 0) {
    return <div className="text-center py-12 font-haas-grot-text text-ink-black/60">No content generated.</div>;
  }

  return (
    <div className="flex flex-col py-8">
      {/* Sub-tabs */}
      {visibleTabs.length > 1 && (
        <div className="mb-8 flex flex-wrap justify-center gap-4">
          {visibleTabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`rounded-full border-2 px-6 py-2 font-haas-grot-text font-bold transition-all ${
                activeTab === tab.key
                  ? 'border-ink-black bg-electric-iris text-paper-white shadow-hard-sm'
                  : 'border-transparent text-ink-black/60 hover:text-ink-black'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Tab Content */}
      <div className="w-full">
        {activeTab === 'flashcards' && (
          <FlashcardDeck
            flashcards={payload.flashcards}
            onGenerateMore={onGenerateMore ? () => onGenerateMore('flashcards') : undefined}
          />
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
            {onGenerateMore && (
              <div className="flex justify-center pt-4">
                <button
                  onClick={() => onGenerateMore('exam')}
                  className="hover-press rounded-full border-2 border-ink-black bg-electric-iris px-6 py-2 font-haas-grot-text text-sm font-bold text-paper-white shadow-hard-sm"
                >
                  Generate More Questions
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'summary' && (
          <div className="w-full max-w-3xl mx-auto rounded-[24px] border-2 border-ink-black bg-paper-white p-8 shadow-hard-md">
            <h3 className="font-haas-grot-disp text-2xl font-bold mb-6 border-b-2 border-ink-black pb-4">Document Summary</h3>
            <p className="font-haas-grot-text text-lg leading-relaxed text-ink-black whitespace-pre-wrap">
              {payload.document_summary}
            </p>
            {onGenerateMore && (
              <div className="flex justify-center pt-6">
                <button
                  onClick={() => onGenerateMore('summary')}
                  className="hover-press rounded-full border-2 border-ink-black bg-electric-iris px-6 py-2 font-haas-grot-text text-sm font-bold text-paper-white shadow-hard-sm"
                >
                  Generate More Summary
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
