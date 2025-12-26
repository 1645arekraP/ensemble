import { Navbar } from "@/components/navbar";
import GuestAuthWrapper from "./guestAuthWrapper";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  // This layout will be applied to all pages inside the (app) group
  return (
    <GuestAuthWrapper>
      <div className='mx-auto max-w-7xl px-4 sm:px-6 lg:px-8'>
        <Navbar />
        <main>
          {children}
        </main>
      </div>
    </GuestAuthWrapper>
    
  );
}