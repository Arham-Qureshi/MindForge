import Header from "./Header";
import Footer from "./Footer";

export default function MainLayout() {
  return (
    <div className="min-h-screen bg-chalk-blue">
      <Header />
      <main className="mx-auto w-full max-w-[1200px] px-4">{/* content renders here */}</main>
      <Footer />
    </div>
  );
}
