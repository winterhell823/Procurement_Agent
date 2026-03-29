import React, { memo, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { FaUserCircle, FaSignOutAlt, FaChevronDown } from "react-icons/fa";

const Navbar = memo(() => {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);

  if (!user) return null;

  // Initial for avatar circle
  const initial = user.full_name ? user.full_name.charAt(0).toUpperCase() : "?";

  return (
    <nav className="fixed top-0 left-0 right-0 h-16 bg-[#0b0f17]/80 backdrop-blur-md border-b border-white/10 z-50 flex items-center justify-between px-8">
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center font-bold text-white">
          P
        </div>
        <span className="text-xl font-bold tracking-tight text-white">ProcureAI</span>
      </div>

      <div className="relative">
        <button
          onClick={() => setDropdownOpen(!dropdownOpen)}
          className="flex items-center gap-3 hover:bg-white/5 px-3 py-1.5 rounded-full transition-all group"
        >
          {/* Avatar Circle */}
          <div className="w-7 h-7 rounded-full bg-white/10 border border-white/20 flex items-center justify-center text-xs font-medium text-white group-hover:border-blue-500/50">
            {initial}
          </div>
          
          <div className="hidden md:block text-left">
            <p className="text-sm font-medium text-gray-200 leading-none">{user.full_name}</p>
            <p className="text-[10px] text-gray-500 mt-1 uppercase tracking-wider">{user.company_name || 'Personal'}</p>
          </div>
          
          <FaChevronDown className={`text-[10px] text-gray-500 transition-transform ${dropdownOpen ? 'rotate-180' : ''}`} />
        </button>

        {dropdownOpen && (
          <>
            <div 
              className="fixed inset-0 z-10" 
              onClick={() => setDropdownOpen(false)} 
            />
            <div className="absolute right-0 mt-2 w-56 bg-[#161b22] border border-white/10 rounded-xl shadow-2xl z-20 overflow-hidden animate-fadeIn">
              <div className="px-4 py-3 border-b border-white/10 bg-white/[0.02]">
                <p className="text-xs text-gray-400">Signed in as</p>
                <p className="text-sm font-medium text-white truncate">{user.email}</p>
              </div>
              
              <div className="p-1">
                <button
                  onClick={logout}
                  className="w-full flex items-center gap-3 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                >
                  <FaSignOutAlt className="text-xs" />
                  Sign out
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </nav>
  );
});

export default Navbar;
