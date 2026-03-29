import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { useRequests } from "../context/RequestContext";
import toast from "react-hot-toast";

export default function NewRequest() {
  const navigate = useNavigate();
  const { addRequest } = useRequests();

  const [title, setTitle] = useState("");
  const [quantity, setQuantity] = useState("");
  const [budget, setBudget] = useState("");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim() || !quantity) {
      toast.error("Please fill all required fields");
      return;
    }

    setLoading(true);

    try {
      await addRequest({
        title,
        quantity,
        budget,
        category,
      });

      toast.success("Request submitted 🚀");
      setTitle("");
      setQuantity("");
      setBudget("");
      setCategory("");

      setTimeout(() => navigate("/dashboard"), 800);
    } catch (err) {
      toast.error(err.message || "Failed to submit request");
    } finally {
      setLoading(false);
    }
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


        <motion.form
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          onSubmit={handleSubmit}
          className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl max-w-2xl space-y-4"
        >


          <div>
            <label className="text-sm text-gray-400">
              Product Specifications *
            </label>
            <textarea
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. 500 steel bolts, size M8, corrosion resistant..."
              className="w-full p-4 mt-2 mb-4 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
              rows="4"
            />
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="text-sm text-gray-400">
                Quantity *
              </label>
              <input
                type="number"
                value={quantity}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="Enter quantity"
                className="w-full p-3 mt-2 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
              />
            </div>

            <div>
              <label className="text-sm text-gray-400">
                Budget (Optional)
              </label>
              <input
                type="number"
                value={budget}
                onChange={(e) => setBudget(e.target.value)}
                placeholder="Enter budget"
                className="w-full p-3 mt-2 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-blue-500 text-white placeholder-gray-500"
              />
            </div>
          </div>


          <div>
            <label className="text-sm text-gray-400">
              Category (Optional)
            </label>
            <input
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. Electronics, Supplies, etc."
              className="w-full p-3 mt-2 bg-black/40 rounded-xl outline-none focus:ring-2 focus:ring-purple-500 text-white placeholder-gray-500"
            />
          </div>


          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            type="submit"
            disabled={loading}
            className="w-full mt-6 bg-gradient-to-r from-blue-500 to-purple-500 py-3 rounded-xl font-semibold shadow-lg hover:shadow-blue-500/30 transition disabled:opacity-50"
          >
            {loading ? "Processing..." : "Submit Request"}
          </motion.button>

        </motion.form>
      </div>
    </DashboardLayout>
  );
}