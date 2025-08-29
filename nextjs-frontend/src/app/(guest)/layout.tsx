import { Navbar } from "@/components/navbar";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  // This layout will be applied to all pages inside the (app) group
  return (
    <div className='mx-auto max-w-7xl px-4 sm:px-6 lg:px-8'>
      <Navbar />
      <main>
        {children}
      </main>
    </div>
  );
}