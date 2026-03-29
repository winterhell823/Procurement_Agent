import Sidebar from "./Sidebar";
import Navbar from "./Navbar";

export default function DashboardLayout({ children }) {
  return (
    <div className="flex bg-black text-white min-h-screen">
      
      <Navbar />
      <Sidebar />

      <div className="ml-64 flex-1 pt-16 transition-all duration-300">
        {children}
      </div>

    </div>
  );
}