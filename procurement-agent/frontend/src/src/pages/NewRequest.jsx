import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { useRequests } from "../context/RequestContext";
import toast from "react-hot-toast";

export default function NewRequest() {
  const navigate = useNavigate();
  const { addRequest } = useRequests();

  const [specs, setSpecs] = useState("");
  const [quantity, setQuantity] = useState("");
  const [extra, setExtra] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = () => {

    if (!specs.trim() || !quantity) {
      toast.error("Please fill all required fields");
      return;
    }

    setLoading(true);

   
    addRequest({
      title: specs,
      quantity,
      extra,
      date: new Date().toLocaleString(),
    });

   
    setTimeout(() => {
      setLoading(false);
      toast.success("Request submitted 🚀");
      navigate("/dashboard");
    }, 800);
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen text-white p-10">

        
        <motion.h1
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-3xl font-bold mb-6"
        >
          AI-Powered Quote Search
        </motion.h1>

        
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl max-w-2xl"
        >

        
          <label className="text-sm text-gray-400">
            Product Specifications *
          </label>
          <textarea
            value={specs}
            onChange={(e) => setSpecs(e.target.value)}
            placeholder="e.g. 500 steel bolts, size M8, corrosion resistant..."
            className="w-full p-4 mt-2 mb-4 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
          />

          <label className="text-sm text-gray-400">
            Quantity *
          </label>
          <input
            type="number"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="Enter quantity"
            className="w-full p-3 mt-2 mb-4 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-blue-500"
          />

          
          <label className="text-sm text-gray-400">
            Additional Details (optional)
          </label>
          <textarea
            value={extra}
            onChange={(e) => setExtra(e.target.value)}
            placeholder="Delivery timeline, preferred supplier, etc."
            className="w-full p-4 mt-2 mb-6 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-purple-500"
          />

         
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            onClick={handleSubmit}
            disabled={loading}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-500 py-3 rounded-xl font-semibold shadow-lg hover:shadow-blue-500/30 transition"
          >
            {loading ? "Processing..." : "Submit Request"}
          </motion.button>

        </motion.div>
      </div>
    </DashboardLayout>
  );
}