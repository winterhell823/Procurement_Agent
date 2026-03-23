import Navbar from "../components/Navbar";
import { motion } from "framer-motion";
import { FaPlus, FaDollarSign, FaClipboardList, FaChartBar } from "react-icons/fa";

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-black text-white">

      <Navbar />

      <div className="px-10 mt-8">

        {/* 🔥 HEADER */}
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-3xl font-bold">Procurement Dashboard</h1>
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
          <StatCard icon={<FaDollarSign />} title="Total Savings" value="$290.25" />
          <StatCard icon={<FaClipboardList />} title="Active Requests" value="3" />
          <StatCard icon={<FaChartBar />} title="Avg Quotes/Request" value="5.0" />
        </div>

        {/* 🔥 TABS */}
        <div className="flex gap-6 mt-10 text-gray-400 border-b border-white/10 pb-3">
          <span className="text-white border-b-2 border-blue-500 pb-1 cursor-pointer">
            All Requests (3)
          </span>
          <span className="cursor-pointer">Completed (2)</span>
          <span className="cursor-pointer">Processing (1)</span>
        </div>

        {/* 🔥 REQUEST LIST */}
        <div className="space-y-6 mt-6">

          {/* ✅ COMPLETED CARD */}
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
            title="1000 safety goggles, anti-fog, ANSI Z87.1"
            date="Mar 14, 2026 • 2:30 PM"
            supplier="SafeHands Inc."
            price="$572.00"
            unit="$0.57/unit"
          />

          {/* 🔄 PROCESSING */}
          <ProcessingCard
            title="250 hard hats, Class E, yellow"
            date="Mar 17, 2026 • 9:15 AM"
          />

        </div>
      </div>
    </div>
  );
}

////////////////////////////////////////////////////

function StatCard({ icon, title, value }) {
  return (
    <motion.div
      whileHover={{ scale: 1.05 }}
      className="bg-white/10 p-6 rounded-2xl border border-white/10 flex items-center gap-4"
    >
      <div className="text-blue-400 text-xl">{icon}</div>
      <div>
        <p className="text-gray-400 text-sm">{title}</p>
        <h2 className="text-xl font-bold">{value}</h2>
      </div>
    </motion.div>
  );
}

////////////////////////////////////////////////////

function RequestCard({ status, title, date, supplier, price, unit }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white/10 p-6 rounded-2xl border border-white/10"
    >
      <span className="text-green-400 text-sm">{status}</span>

      <h3 className="mt-2 font-semibold">{title}</h3>
      <p className="text-gray-500 text-sm">{date}</p>

      <div className="mt-4">
        <p className="text-gray-400 text-sm">Best Quote</p>
        <h4 className="font-medium">{supplier}</h4>

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
      animate={{ opacity: [0.6, 1, 0.6] }}
      transition={{ repeat: Infinity, duration: 2 }}
      className="bg-white/10 p-6 rounded-2xl border border-white/10"
    >
      <span className="text-yellow-400 text-sm">processing</span>

      <h3 className="mt-2 font-semibold">{title}</h3>
      <p className="text-gray-500 text-sm">{date}</p>

      <p className="mt-4 text-blue-400">
        🤖 AI is searching suppliers...
      </p>

      <p className="text-gray-500 text-sm">
        This usually takes 2-3 minutes
      </p>
    </motion.div>
  );
}