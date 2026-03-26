import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import DashboardLayout from "../components/DashboardLayout";

export default function NewRequest() {
  const navigate = useNavigate();

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
          className="bg-white/10 border border-white/10 rounded-2xl p-8 backdrop-blur-xl"
        >

          <h2 className="text-xl font-semibold mb-4">
            New Procurement Request
          </h2>

          
          <div className="mb-6">
            <label className="block mb-2 text-gray-300">
              Product Specifications
            </label>

            <textarea
              placeholder="e.g., 500 units of industrial gloves, size L, nitrile"
              className="w-full p-4 rounded-xl bg-black/40 border border-gray-700 focus:border-blue-500 outline-none"
              rows={4}
            />
          </div>

          
          <div className="mb-6 flex gap-4">
            <input
              type="number"
              placeholder="500"
              className="w-32 p-3 rounded-xl bg-black/40 border border-gray-700"
            />
            <span className="flex items-center text-gray-400">Units</span>
          </div>

          
          <div className="mb-6">
            <textarea
              placeholder="e.g., Need by date, certifications, budget..."
              className="w-full p-4 rounded-xl bg-black/40 border border-gray-700"
              rows={3}
            />
          </div>

         
          <div className="flex justify-end gap-4">

            <button
              onClick={() => navigate("/dashboard")}
              className="px-5 py-2 border border-gray-600 rounded-lg hover:bg-white/10"
            >
              Cancel
            </button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg"
            >
              Submit Request
            </motion.button>

          </div>

        </motion.div>

      </div>

    </DashboardLayout>
  );
}