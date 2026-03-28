import { useNavigate } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import { motion } from "framer-motion";
import {
  FaPlus,
  FaDollarSign,
  FaClipboardList,
  FaChartBar,
} from "react-icons/fa";
import { useRequests } from "../context/RequestContext";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

export default function Dashboard() {
  const navigate = useNavigate();

  const { requests = [] } = useRequests();

  const stats = [
    {
      title: "Total Requests",
      value: requests.length,
      icon: <FaClipboardList />,
    },
    {
      title: "Processing",
      value: requests.filter((r) => r.status === "processing").length,
      icon: <FaChartBar />,
    },
    {
      title: "Completed",
      value: requests.filter((r) => r.status === "completed").length,
      icon: <FaDollarSign />,
    },
  ];

  const chartData = requests.map((req, index) => ({
    name: `Req ${index + 1}`,
    quantity: Number(req.quantity) || 0,
    price:
      Number(req.price?.replace("$", "")) ||
      Math.floor(Math.random() * 100),
  }));

  return (
    <DashboardLayout>
      <div className="px-10 mt-8 text-white">

        
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Procurement Dashboard</h1>
            <p className="text-gray-400">
              Track and manage all your procurement requests
            </p>
          </div>

          <button
            onClick={() => navigate("/new-request")}
            className="flex items-center gap-2 bg-blue-500 px-4 py-2 rounded-lg hover:scale-105 transition"
          >
            <FaPlus /> New Request
          </button>
        </div>

       
        <div className="grid md:grid-cols-3 gap-6 mt-8">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.2 }}
              className="bg-white/5 p-6 rounded-2xl flex items-center gap-4"
            >
              <div className="text-blue-400 text-xl">{s.icon}</div>
              <div>
                <p className="text-gray-400 text-sm">{s.title}</p>
                <h2 className="text-xl font-bold">{s.value}</h2>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="grid md:grid-cols-2 gap-8 mt-12">

          <div className="bg-white/5 p-6 rounded-2xl">
            <h3 className="mb-6 font-semibold">Request Quantity</h3>

            {chartData.length === 0 ? (
              <p className="text-gray-400">No data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={chartData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="quantity" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>

          <div className="bg-white/5 p-6 rounded-2xl">
            <h3 className="mb-6 font-semibold">Request Trend</h3>

            {chartData.length === 0 ? (
              <p className="text-gray-400">No data yet</p>
            ) : (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={chartData}>
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="quantity" />
                </LineChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

       
        <div className="mt-12 space-y-6">

          {requests.length === 0 && (
            <p className="text-gray-400">No requests yet 🚀</p>
          )}

          {requests.map((req, i) =>
            req.status === "completed" ? (
              <RequestCard key={i} {...req} />
            ) : (
              <ProcessingCard key={i} {...req} />
            )
          )}
        </div>

      </div>
    </DashboardLayout>
  );
}



function RequestCard({ title, quantity, supplier, price }) {
  return (
    <div className="bg-white/5 p-6 rounded-2xl">
      <span className="text-green-400 text-sm">completed</span>

      <h3 className="mt-2 font-semibold">{title}</h3>

      <p className="mt-2">{supplier || "AI Supplier"}</p>

      <div className="flex justify-between mt-2">
        <span>{price || "$--"}</span>
        <span className="text-gray-400">{quantity}</span>
      </div>
    </div>
  );
}



function ProcessingCard({ title, quantity }) {
  return (
    <div className="bg-white/5 p-6 rounded-2xl">
      <span className="text-yellow-400 text-sm">processing</span>

      <h3 className="mt-2 font-semibold">{title}</h3>
      <p className="text-gray-400">{quantity}</p>

      <p className="mt-4 text-blue-400">
        AI is searching suppliers...
      </p>
    </div>
  );
}