import Sidebar from "./Sidebar";

export default function DashboardLayout({ children }) {
  return (
    <div className="flex bg-black text-white min-h-screen">

     
      <Sidebar />

      <div className="ml-64 md:ml-64 w-full p-8 transition-all duration-300">
        {children}
      </div>

    </div>
  );
}