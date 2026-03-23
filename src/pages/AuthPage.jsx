import React, { useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const navigate = useNavigate();

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-black text-white overflow-hidden">

      {/* 🌈 MESH GRADIENT BACKGROUND */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(59,130,246,0.3),transparent_40%),radial-gradient(circle_at_80%_70%,rgba(168,85,247,0.3),transparent_40%)]" />

      {/* ✨ Animated Glow Lines */}
      <div className="absolute w-full h-full opacity-20 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.1),transparent)] animate-pulse" />

      {/* 🤖 FLOATING PANELS */}
      <FloatingPanel text="🤖 AI negotiating prices..." top="15%" left="8%" />
      <FloatingPanel text="📊 Best deal found!" top="70%" left="75%" delay={1} />
      <FloatingPanel text="⚡ Real-time supplier match" top="80%" left="20%" delay={2} />

      {/* 🔥 AUTH CARD */}
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 w-full max-w-md p-8 rounded-3xl bg-white/10 backdrop-blur-2xl border border-white/20 shadow-[0_0_40px_rgba(59,130,246,0.2)]"
      >

        {/* 🌟 Glow Border Effect */}
        <div className="absolute inset-0 rounded-3xl border border-white/10 pointer-events-none" />

        <h2 className="text-3xl font-bold text-center mb-2">
          {isLogin ? "Welcome Back" : "Create Account"}
        </h2>

        <p className="text-center text-gray-400 mb-6">
          {isLogin
            ? "Continue your AI procurement journey"
            : "Automate your sourcing with AI"}
        </p>

        <div className="space-y-4">

          {!isLogin && <Input placeholder="Company Name" />}

          <Input placeholder="Email" type="email" />
          <Input placeholder="Password" type="password" />

          {!isLogin && <Input placeholder="Confirm Password" type="password" />}

          {/* OPTIONS */}
          {isLogin && (
            <div className="flex justify-between text-sm text-gray-400">
              <label className="flex items-center gap-2">
                <input type="checkbox" className="accent-blue-500" />
                Remember
              </label>
              <span className="hover:text-blue-400 cursor-pointer">
                Forgot?
              </span>
            </div>
          )}

          {/* BUTTON */}
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate("/home")}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 shadow-lg hover:shadow-blue-500/30 transition"
          >
            {isLogin ? "Sign In" : "Register"}
          </motion.button>

          {/* Divider */}
          <div className="flex items-center gap-3 text-gray-400 text-sm">
            <div className="flex-1 h-px bg-gray-600" />
            OR
            <div className="flex-1 h-px bg-gray-600" />
          </div>

          {/* SOCIAL */}
          <div className="flex gap-4">
            <SocialBtn text="Google" />
            <SocialBtn text="GitHub" />
          </div>
        </div>

        {/* TOGGLE */}
        <p className="text-sm text-center mt-6 text-gray-400">
          {isLogin ? "No account?" : "Already have one?"}
          <span
            onClick={() => setIsLogin(!isLogin)}
            className="text-blue-400 ml-2 cursor-pointer"
          >
            {isLogin ? "Register" : "Login"}
          </span>
        </p>
      </motion.div>
    </div>
  );
}

/* 🔥 Input */
function Input({ placeholder, type = "text" }) {
  return (
    <input
      type={type}
      placeholder={placeholder}
      className="w-full p-3 rounded-xl bg-black/40 border border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 outline-none transition"
    />
  );
}

/* 🔥 Floating Panels */
function FloatingPanel({ text, top, left, delay = 0 }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1, y: [0, -20, 0] }}
      transition={{ delay, repeat: Infinity, duration: 4 }}
      style={{ top, left }}
      className="absolute bg-white/10 backdrop-blur-xl px-4 py-2 rounded-xl text-sm border border-white/10 shadow-lg"
    >
      {text}
    </motion.div>
  );
}

/* 🔥 Social Buttons */
function SocialBtn({ text }) {
  return (
    <button className="flex-1 py-2 border border-gray-600 rounded-lg hover:bg-white/10 transition">
      {text}
    </button>
  );
}