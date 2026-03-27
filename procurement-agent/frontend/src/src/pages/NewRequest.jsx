import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";

export default function NewRequest() {
  const navigate = useNavigate();

 
  const [specs, setSpecs] = useState("");
  const [quantity, setQuantity] = useState("");
  const [extra, setExtra] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  
  const handleSubmit = () => {
    if (!specs || !quantity) {
      setError("Please fill all required fields");
      return;
    }

    setError("");
    setLoading(true);

    
    setTimeout(() => {
      console.log({
        specs,
        quantity,
        extra,
      });

      navigate("/dashboard");
    }, 2000);
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen text-white p-10">

       
        <div className="mb-8">
          <h1 className="text-3xl font-bold">AI-Powered Quote Search</h1>
          <p className="text-gray-400 mt-2">
            Describe your product requirements and let our AI find the best suppliers for you.
          </p>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/10 border border-white/10 rounded-2xl p-8 backdrop-blur-xl max-w-3xl"
        >
          <h2 className="text-xl font-semibold mb-4">
            New Procurement Request
          </h2>

          
          {error && (
            <p className="text-red-400 mb-4 text-sm">{error}</p>
          )}


          <div className="mb-6">
            <label className="block mb-2 text-gray-300">
              Product Specifications *
            </label>

            <textarea
              value={specs}
              onChange={(e) => setSpecs(e.target.value)}
              placeholder="e.g., 500 units of industrial gloves, size L, nitrile"
              className="w-full p-4 rounded-xl bg-black/40 border border-gray-700 focus:border-blue-500 outline-none"
              rows={4}
            />
          </div>

          
          <div className="mb-6 flex gap-4 items-center">
            <input
              type="number"
              value={quantity}
              onChange={(e) => setQuantity(e.target.value)}
              placeholder="500"
              className="w-32 p-3 rounded-xl bg-black/40 border border-gray-700"
            />
            <span className="text-gray-400">Units *</span>
          </div>

         
          <div className="mb-6">
            <label className="block mb-2 text-gray-300">
              Additional Requirements
            </label>

            <textarea
              value={extra}
              onChange={(e) => setExtra(e.target.value)}
              placeholder="e.g., Need by date, certifications, budget..."
              className="w-full p-4 rounded-xl bg-black/40 border border-gray-700"
              rows={3}
            />
          </div>

          
          <div className="flex justify-end gap-4">

            <button
              onClick={() => navigate("/dashboard")}
              className="px-5 py-2 border border-gray-600 rounded-lg hover:bg-white/10 transition"
            >
              Cancel
            </button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleSubmit}
              disabled={loading}
              className={`px-6 py-3 rounded-lg transition ${
                loading
                  ? "bg-gray-600 cursor-not-allowed"
                  : "bg-gradient-to-r from-blue-500 to-purple-500"
              }`}
            >
              {loading ? " AI is searching..." : "Submit Request"}
            </motion.button>

          </div>
        </motion.div>

      </div>
    </DashboardLayout>
  );
}