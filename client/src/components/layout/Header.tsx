export default function Header() {
  return (
    <header className="sticky top-0 z-50">
      {/* Announcement Ticker */}
      <div className="bg-ink-black text-paper-white font-martian-mono text-caption-mono uppercase tracking-widest overflow-hidden border-b-2 border-ink-black">
        <div className="flex animate-marquee whitespace-nowrap py-2">
          <span className="mx-4">New! AI study assets for Database Systems</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">100% Private &amp; Local</span>
          <span className="mx-4" aria-hidden="true">•</span>
          <span className="mx-4">Zero Cloud Retention</span>
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
          
          <div className="hidden gap-6 md:flex pt-1">
            <a href="#" className="border-b-2 border-electric-iris text-electric-iris pb-4 text-body-sm font-bold no-underline">
              Drop Box
            </a>
            <a href="#" className="border-b-2 border-transparent text-ink-black/70 hover:text-ink-black hover:border-ink-black pb-4 text-body-sm font-bold no-underline transition-colors">
              Flashcards
            </a>
            <a href="#" className="border-b-2 border-transparent text-ink-black/70 hover:text-ink-black hover:border-ink-black pb-4 text-body-sm font-bold no-underline transition-colors">
              HOT Questions
            </a>
          </div>
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
