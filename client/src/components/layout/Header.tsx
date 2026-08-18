import { Search } from "lucide-react";

export default function Header() {
  return (
    <header>
      <div className="bg-ink-black text-paper-white font-martian-mono text-xs uppercase tracking-tight">
        <div className="mx-auto flex max-w-[1200px] items-center gap-2 px-4 py-2">
          <span>New! AI study assets for Database Systems</span>
          <span aria-hidden="true">•</span>
          <span>100% Private &amp; Local</span>
        </div>
      </div>
      <nav className="flex h-16 items-center justify-between border-b border-frost-blue bg-paper-white px-4">
        <div className="flex items-center gap-6">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-electric-iris text-paper-white" aria-label="MindForge logo">
            M
          </div>
          <div className="hidden gap-6 md:flex">
            <a href="#" className="text-body-sm text-ink-black no-underline">Catalog</a>
            <a href="#" className="text-body-sm text-ink-black no-underline">About</a>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <Search className="h-5 w-5 text-ink-black" aria-label="Search" />
          <a href="#" className="rounded-full bg-ink-black px-6 py-3 text-body-sm text-paper-white no-underline">Sign in</a>
        </div>
      </nav>
    </header>
  );
}
