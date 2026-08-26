import Header from "./Header";
import Footer from "./Footer";
import DecorativeShapes from "../common/DecorativeShapes";
import type { SessionPhase } from "../../hooks/useJobSession";

type MainLayoutProps = {
  children?: React.ReactNode;
  phase?: SessionPhase;
};

export default function MainLayout({ children, phase }: MainLayoutProps) {
  return (
    <div className="flex min-h-screen flex-col bg-chalk-blue font-haas-grot-text text-ink-black selection:bg-hi-yellow selection:text-ink-black relative isolate">
      <DecorativeShapes />
      <Header phase={phase} />
      <main className="mx-auto w-full max-w-[1200px] flex-grow px-4 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}
