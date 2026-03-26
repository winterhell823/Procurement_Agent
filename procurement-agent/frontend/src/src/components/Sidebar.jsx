import { useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { 
  FaTachometerAlt, 
  FaPlus, 
  FaSignOutAlt, 
  FaBars 
} from "react-icons/fa";

export default function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);

  
  const navItem = (label, icon, path) => (
    <button
      onClick={() => navigate(path)}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl w-full text-left transition
        ${location.pathname === path
          ? "bg-blue-500/20 text-blue-400"
          : "text-gray-400 hover:text-white hover:bg-white/10"
        }`}
    >
      {icon}
      {!collapsed && <span>{label}</span>}
    </button>
  );

  return (
    <div
      className={`h-screen fixed top-0 left-0 bg-[#020617] border-r border-white/10 flex flex-col justify-between p-4 transition-all duration-300
        ${collapsed ? "w-20" : "w-64"}
      `}
    >
      
      <div>
        
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="mb-6 text-gray-400 hover:text-white"
        >
          <FaBars />
        </button>

       
        {!collapsed && (
          <h1 className="text-xl font-bold mb-8">ProcureAI</h1>
        )}

        
        <div className="flex flex-col gap-2">
          {navItem("Dashboard", <FaTachometerAlt />, "/dashboard")}
          {navItem("New Request", <FaPlus />, "/new-request")}
        </div>
      </div>

      
      <button
        onClick={() => navigate("/")}
        className="flex items-center gap-3 px-4 py-3 rounded-xl text-gray-400 hover:text-red-400 hover:bg-red-500/10 transition"
      >
        <FaSignOutAlt />
        {!collapsed && "Sign Out"}
      </button>
    </div>
  );
}