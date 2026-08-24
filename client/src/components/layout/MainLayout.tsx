import Header from "./Header";
import Footer from "./Footer";
import DecorativeShapes from "../common/DecorativeShapes";

export default function MainLayout({ children }: { children?: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col bg-chalk-blue font-haas-grot-text text-ink-black selection:bg-hi-yellow selection:text-ink-black relative isolate">
      <DecorativeShapes />
      <Header />
      <main className="mx-auto w-full max-w-[1200px] flex-grow px-4 py-8">
        {children}
      </main>
      <Footer />
    </div>
  );
}
