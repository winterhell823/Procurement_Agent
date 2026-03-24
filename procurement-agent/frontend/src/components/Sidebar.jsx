import { Home, Users, FileText, Settings } from "lucide-react";

export default function Sidebar() {
  return (
    <div className="w-64 bg-white/10 backdrop-blur-xl p-6 hidden md:flex flex-col justify-between">
      
      {/* Logo */}
      <h1 className="text-2xl font-bold mb-8">
        Procure<span className="text-blue-400">AI</span>
      </h1>

      {/* Menu */}
      <div className="space-y-4">
        <SidebarItem icon={<Home size={18} />} label="Dashboard" />
        <SidebarItem icon={<Users size={18} />} label="Suppliers" />
        <SidebarItem icon={<FileText size={18} />} label="Quotes" />
        <SidebarItem icon={<Settings size={18} />} label="Settings" />
      </div>

      {/* Bottom */}
      <div className="text-sm text-gray-400">
        © 2026 ProcureAI
      </div>
    </div>
  );
}

function SidebarItem({ icon, label }) {
  return (
    <div className="flex items-center gap-3 p-2 rounded-lg cursor-pointer hover:bg-blue-500/20 transition">
      {icon}
      <span>{label}</span>
    </div>
  );
}