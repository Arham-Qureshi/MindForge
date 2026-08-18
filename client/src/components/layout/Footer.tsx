export default function Footer() {
  return (
    <footer className="border-t border-frost-blue bg-chalk-blue">
      <div className="mx-auto flex max-w-[1200px] flex-col gap-2 px-4 py-8 text-body-sm text-ink-black">
        <p>MindForge — study locally. No accounts. Zero cloud retention.</p>
        <p>© {new Date().getFullYear()} MindForge AI. All rights reserved.</p>
      </div>
    </footer>
  );
}
