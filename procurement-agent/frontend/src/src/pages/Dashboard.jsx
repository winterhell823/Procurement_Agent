import DashboardLayout from "../components/DashboardLayout";
import { motion } from "framer-motion";
import { FaPlus, FaDollarSign, FaClipboardList, FaChartBar } from "react-icons/fa";

////////////////////////////////////////////////////

const stats = [
  { title: "Total Savings", value: "$290.25", icon: <FaDollarSign /> },
  { title: "Active Requests", value: "3", icon: <FaClipboardList /> },
  { title: "Avg Quotes/Request", value: "5.0", icon: <FaChartBar /> },
];

const quotes = [
  { name: "GlobalTex", price: "$4.20", time: "5 days", status: "Best" },
  { name: "SafeHands", price: "$4.85", time: "7 days", status: "Good" },
  { name: "NitriPro", price: "$5.10", time: "3 days", status: "Good" },
  { name: "GloveMfg", price: "$5.45", time: "10 days", status: "Average" },
];

////////////////////////////////////////////////////

export default function Homepage() {
  return (
    <DashboardLayout>
      <div className="px-10 mt-8">

        {/* 🔥 HEADER */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Procurement Homepage</h1>
            <p className="text-gray-400">
              Track and manage all your procurement requests
            </p>
          </div>

          <button className="flex items-center gap-2 bg-blue-500 px-4 py-2 rounded-lg hover:scale-105 transition">
            <FaPlus /> New Request
          </button>
        </div>

        {/* 🔥 STATS */}
        <div className="grid md:grid-cols-3 gap-6 mt-8">
          {stats.map((s, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.2 }}
              viewport={{ once: true }}
              whileHover={{ scale: 1.05 }}
              className="bg-white/5 backdrop-blur-xl border border-white/10 p-6 rounded-2xl flex items-center gap-4"
            >
              <div className="text-blue-400 text-xl">{s.icon}</div>
              <div>
                <p className="text-gray-400 text-sm">{s.title}</p>
                <h2 className="text-xl font-bold">{s.value}</h2>
              </div>
            </motion.div>
          ))}
        </div>

        {/* 🔥 ANALYTICS */}
        <div className="grid md:grid-cols-2 gap-8 mt-12">
          {/* CHART */}
          <motion.div
            initial={{ opacity: 0, x: -60 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7 }}
            viewport={{ once: true }}
            className="bg-white/5 border border-white/10 rounded-2xl p-6"
          >
            <h3 className="mb-6 font-semibold">Price Comparison</h3>
            <div className="flex items-end gap-4 h-40">
              {[60, 70, 80, 90, 75].map((h, i) => (
                <motion.div
                  key={i}
                  initial={{ height: 0 }}
                  whileInView={{ height: `${h}%` }}
                  transition={{ delay: i * 0.2 }}
                  viewport={{ once: true }}
                  className="w-8 bg-gradient-to-t from-blue-500 to-purple-500 rounded-md"
                />
              ))}
            </div>
          </motion.div>

          {/* LIVE QUOTES */}
          <motion.div
            initial={{ opacity: 0, x: 60 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7 }}
            viewport={{ once: true }}
            className="bg-white/5 border border-white/10 rounded-2xl p-6"
          >
            <h3 className="mb-6 font-semibold">Live Quote Tracker</h3>

            {quotes.map((q, i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.15 }}
                viewport={{ once: true }}
                className="flex justify-between text-sm border-b border-white/10 pb-2 mb-3"
              >
                <span>{q.name}</span>
                <span className="text-green-400">{q.price}</span>
                <span className="text-gray-400">{q.time}</span>
                <span
                  className={`px-2 py-1 rounded-full text-xs ${
                    q.status === "Best"
                      ? "bg-green-500/20 text-green-400"
                      : q.status === "Good"
                      ? "bg-blue-500/20 text-blue-400"
                      : "bg-purple-500/20 text-purple-400"
                  }`}
                >
                  {q.status}
                </span>
              </motion.div>
            ))}
          </motion.div>
        </div>

        {/* REQUESTS */}
        <div className="mt-12 space-y-6">
          <RequestCard
            status="completed"
            title="500 units of industrial gloves, size L, nitrile"
            date="Mar 15, 2026 • 10:00 AM"
            supplier="SafeHands Inc."
            price="$374.00"
            unit="$0.75/unit"
          />

          <RequestCard
            status="completed"
            title="1000 safety goggles, anti-fog"
            date="Mar 14, 2026"
            supplier="SafeHands Inc."
            price="$572.00"
            unit="$0.57/unit"
          />

          <ProcessingCard
            title="250 hard hats, Class E"
            date="Mar 17, 2026"
          />
        </div>
      </div>
    </DashboardLayout>
  );
}

////////////////////////////////////////////////////

function RequestCard({ status, title, date, supplier, price, unit }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      viewport={{ once: true }}
      whileHover={{ scale: 1.02 }}
      className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10"
    >
      <span className="text-green-400 text-sm">{status}</span>

      <h3 className="mt-2 font-semibold">{title}</h3>
      <p className="text-gray-500 text-sm">{date}</p>

      <div className="mt-4">
        <p className="text-gray-400 text-sm">Best Quote</p>
        <h4>{supplier}</h4>

        <div className="flex justify-between mt-2">
          <span>{price}</span>
          <span className="text-gray-400">{unit}</span>
        </div>
      </div>

      <button className="mt-4 px-4 py-2 border border-gray-600 rounded-lg hover:bg-white/10">
        View All Quotes
      </button>
    </motion.div>
  );
}

////////////////////////////////////////////////////

function ProcessingCard({ title, date }) {
  return (
    <motion.div
      animate={{ opacity: [0.5, 1, 0.5] }}
      transition={{ repeat: Infinity, duration: 2 }}
      className="bg-white/5 backdrop-blur-xl p-6 rounded-2xl border border-white/10"
    >
      <span className="text-yellow-400 text-sm">processing</span>

      <h3 className="mt-2 font-semibold">{title}</h3>
      <p className="text-gray-500 text-sm">{date}</p>

      <p className="mt-4 text-blue-400">
        🤖 AI is searching suppliers...
      </p>

      <p className="text-gray-500 text-sm">
        This usually takes 2–3 minutes
      </p>
    </motion.div>
  );
}