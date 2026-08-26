import type { SessionPhase } from '../../hooks/useJobSession';

type HeaderProps = {
  phase?: SessionPhase;
};

export default function Header({ phase }: HeaderProps) {
  const docType = phase?.kind === 'ready' ? phase.data.classification.doc_type : null;

  return (
    <header className="sticky top-0 z-50">
      {/* Announcement Ticker */}
      <div className="bg-ink-black text-paper-white font-martian-mono text-caption-mono uppercase tracking-widest overflow-hidden border-b-2 border-ink-black">
        <div className="flex animate-marquee whitespace-nowrap py-2">
          <span className="mx-4">Turn syllabi into structured study plans</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">Generate flashcards from lecture notes</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">Predict exam questions from past papers</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">100% local — your PDFs never leave your machine</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">Turn syllabi into structured study plans</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">Generate flashcards from lecture notes</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">Predict exam questions from past papers</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">100% local — your PDFs never leave your machine</span>
          <span className="mx-4" aria-hidden="true">•</span>
        </div>
      </div>
      
      {/* Main Nav */}
      <nav className="flex h-16 items-center justify-between border-b-2 border-ink-black bg-paper-white px-6 shadow-hard-md">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2 font-haas-grot-disp text-2xl font-bold tracking-tight text-ink-black">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-electric-iris text-paper-white shadow-hard-sm">
              M
            </div>
            MindForge
          </div>
          
          {docType && (
            <div className="hidden gap-6 md:flex pt-1">
              {docType === 'SYLLABUS' && (
                <a href="#" className="border-b-2 border-electric-iris text-electric-iris pb-4 text-body-sm font-bold no-underline">
                  Syllabus
                </a>
              )}
              {docType === 'NOTES' && (
                <a href="#" className="border-b-2 border-electric-iris text-electric-iris pb-4 text-body-sm font-bold no-underline">
                  Flashcards
                </a>
              )}
              {docType === 'PYQ' && (
                <a href="#" className="border-b-2 border-electric-iris text-electric-iris pb-4 text-body-sm font-bold no-underline">
                  HOT Questions
                </a>
              )}
            </div>
          )}
        </div>
        
        <div className="flex items-center gap-4">
          <button className="flex h-10 w-10 items-center justify-center rounded-full hover:bg-frost-blue transition-colors">
            <span className="material-symbols-outlined text-ink-black">search</span>
          </button>
          <a href="#" className="hover-press flex items-center gap-2 rounded-full border-2 border-ink-black bg-paper-white px-5 py-2 text-body-sm font-bold text-ink-black shadow-hard-sm no-underline">
            <span className="material-symbols-outlined text-xl">person</span>
            Profile
          </a>
        </div>
      </nav>
    </header>
  );
}
