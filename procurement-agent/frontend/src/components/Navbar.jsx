import { useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();

  return (
    <div className="flex justify-between items-center px-10 py-6 border-b border-white/10">
      <h1 className="text-xl font-bold">
        Procure<span className="text-blue-400">AI</span>
      </h1>

      <div className="flex gap-6 text-gray-300">
        <span className="hover:text-white cursor-pointer">Dashboard</span>
        <span className="hover:text-white cursor-pointer">Suppliers</span>
        <span className="hover:text-white cursor-pointer">Quotes</span>
      </div>

      <button
        onClick={() => navigate("/")}
        className="px-4 py-2 border border-gray-600 rounded-lg hover:bg-white/10"
      >
        Logout
      </button>
    </div>
  );
}