import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { useState } from "react";
import DashboardLayout from "../components/DashboardLayout";
import { useRequest } from "../context/RequestContext";
import toast from "react-hot-toast";

export default function NewRequest() {
  const navigate = useNavigate();
  const { addRequest } = useRequest();

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
      addRequest({
        title: specs,
        quantity,
        extra,
      });

      toast.success("Request submitted 🚀");
      navigate("/dashboard");
    }, 1500);
  };

  return (
    <DashboardLayout>
      <div className="min-h-screen text-white p-10">

        <h1 className="text-3xl font-bold mb-6">AI-Powered Quote Search</h1>

        {error && <p className="text-red-400 mb-4">{error}</p>}

        <textarea
          value={specs}
          onChange={(e) => setSpecs(e.target.value)}
          placeholder="Product specs"
          className="w-full p-4 mb-4 bg-black/40 rounded-xl"
        />

        <input
          type="number"
          value={quantity}
          onChange={(e) => setQuantity(e.target.value)}
          placeholder="Quantity"
          className="w-full p-3 mb-4 bg-black/40 rounded-xl"
        />

        <textarea
          value={extra}
          onChange={(e) => setExtra(e.target.value)}
          placeholder="Extra details"
          className="w-full p-4 mb-6 bg-black/40 rounded-xl"
        />

        <button
          onClick={handleSubmit}
          className="bg-blue-500 px-6 py-3 rounded-lg"
        >
          {loading ? "Processing..." : "Submit"}
        </button>

      </div>
    </DashboardLayout>
  );
}