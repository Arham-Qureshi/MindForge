export default function Footer() {
  return (
    <footer className="mt-auto border-t-2 border-ink-black bg-chalk-blue">
      <div className="mx-auto flex max-w-[1200px] flex-col justify-between gap-8 px-6 py-12 md:flex-row md:items-center md:gap-4 text-ink-black">
        <div className="flex flex-col gap-2">
          <span className="font-haas-grot-disp text-xl font-bold tracking-tight">MindForge</span>
          <p className="font-haas-grot-text text-body-sm text-ink-black/80">
            Study locally. No accounts. Zero cloud retention.
          </p>
        </div>
        
        <div className="flex flex-wrap gap-6 font-martian-mono text-sm font-bold uppercase tracking-widest">
          <a href="#" className="hover:text-electric-iris transition-colors">Privacy</a>
          <a href="#" className="hover:text-electric-iris transition-colors">Terms</a>
          <a href="#" className="hover:text-electric-iris transition-colors">Support</a>
          <a href="#" className="hover:text-electric-iris transition-colors">GitHub</a>
        </div>
        
        <div className="font-martian-mono text-xs text-ink-black/60">
          © {new Date().getFullYear()} MindForge AI.
        </div>
      </div>
    </footer>
  );
}
