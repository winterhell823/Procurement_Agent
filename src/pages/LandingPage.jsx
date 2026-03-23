import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";

export default function LandingPage() {
  const navigate = useNavigate();

  return (
    <div className="bg-black text-white min-h-screen overflow-x-hidden">

      {/* 🔥 NAVBAR */}
      <div className="flex justify-between items-center px-10 py-6">
        <h1 className="text-xl font-bold">
          Procure<span className="text-blue-400">AI</span>
        </h1>

        <button
          onClick={() => navigate("/auth")}
          className="px-5 py-2 border border-gray-600 rounded-lg hover:bg-white/10 transition"
        >
          Sign In
        </button>
      </div>

      {/* 🚀 HERO */}
      <div className="grid md:grid-cols-2 px-10 mt-20 items-center">

        {/* LEFT TEXT */}
        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          <p className="text-blue-400 text-sm mb-3 tracking-widest">
            AUTONOMOUS PROCUREMENT
          </p>

          <h1 className="text-5xl md:text-6xl font-bold leading-tight">
            AI Agents that
            <span className="text-blue-400"> negotiate</span>
            <br />
            your supply chain.
          </h1>

          <p className="text-gray-400 mt-6 max-w-lg text-lg">
            Automate sourcing, compare suppliers, and close deals faster
            with intelligent AI agents.
          </p>

          <div className="flex gap-4 mt-8">
            <button
              onClick={() => navigate("/auth")}
              className="px-6 py-3 bg-white text-black rounded-lg font-medium hover:opacity-90 transition"
            >
              Get Started
            </button>

            <button className="px-6 py-3 border border-gray-600 rounded-lg hover:bg-white/10 transition">
              Book Demo
            </button>
          </div>
        </motion.div>

        {/* RIGHT VISUAL */}
        <motion.div
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.6 }}
          className="relative flex justify-center mt-10 md:mt-0"
        >
          {/* Glow */}
          <div className="absolute w-[350px] h-[350px] bg-blue-500 opacity-20 blur-3xl rounded-full" />

          {/* Main Card */}
          <div className="bg-white/10 backdrop-blur-xl border border-white/10 p-6 w-[320px] rounded-2xl shadow-xl">
            <h3 className="mb-3 font-semibold">AI Workflow</h3>

            <Step text="🔍 Finding suppliers" />
            <Step text="📊 Comparing quotes" delay={0.2} />
            <Step text="🤖 Negotiating price" delay={0.4} />
            <Step text="✅ Finalizing deal" delay={0.6} />
          </div>
        </motion.div>
      </div>

      {/* 👇 SCROLL SPACE (IMPORTANT for animations) */}
      <div className="h-[150px]" />

      {/* 🔥 FEATURES (SCROLL ANIMATED) */}
      <motion.div
        initial="hidden"
        whileInView="show"
        viewport={{ once: true }}
        variants={container}
        className="grid md:grid-cols-3 gap-6 px-10 mb-20"
      >
        <Feature title="Find Suppliers" desc="AI scans global vendors instantly" />
        <Feature title="Compare Quotes" desc="Real-time price analysis" />
        <Feature title="Negotiate Deals" desc="AI agents optimize pricing" />
      </motion.div>
    </div>
  );
}

/* 🔥 Animation Variants */
const container = {
  hidden: {},
  show: {
    transition: {
      staggerChildren: 0.2,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 80 },
  show: { opacity: 1, y: 0 },
};

/* 🔥 Step Component */
function Step({ text, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay }}
      className="bg-white/10 p-3 rounded-lg mb-2 text-sm"
    >
      {text}
    </motion.div>
  );
}

/* 🔥 Feature Card */
function Feature({ title, desc }) {
  return (
    <motion.div
      variants={item}
      className="bg-white/10 backdrop-blur-xl border border-white/10 p-6 rounded-2xl hover:scale-105 transition"
    >
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{desc}</p>
    </motion.div>
  );
}