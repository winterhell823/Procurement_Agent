import React, { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { useNavigate } from "react-router-dom";
import { googleSignIn } from "../services/api";

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [authError, setAuthError] = useState("");
  const [isGoogleLoading, setIsGoogleLoading] = useState(false);
  const googleBtnRef = useRef(null);
  const navigate = useNavigate();
  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const hasValidGoogleClientId =
    typeof googleClientId === "string" &&
    googleClientId.trim().endsWith(".apps.googleusercontent.com");

  useEffect(() => {
    const clientId = googleClientId?.trim();
    if (!clientId || !googleBtnRef.current) return;
    if (!hasValidGoogleClientId) {
      setAuthError(
        "Invalid Google Client ID. Use OAuth Web Client ID ending with .apps.googleusercontent.com"
      );
      return;
    }

    let cancelled = false;

    const loadGoogleScript = () => {
      if (window.google?.accounts?.id) {
        initializeGoogle(clientId);
        return;
      }

      const existing = document.querySelector('script[src="https://accounts.google.com/gsi/client"]');
      if (existing) {
        existing.addEventListener("load", () => initializeGoogle(clientId), { once: true });
        return;
      }

      const script = document.createElement("script");
      script.src = "https://accounts.google.com/gsi/client";
      script.async = true;
      script.defer = true;
      script.onload = () => initializeGoogle(clientId);
      document.body.appendChild(script);
    };

    const initializeGoogle = (cid) => {
      if (cancelled || !window.google?.accounts?.id || !googleBtnRef.current) return;

      window.google.accounts.id.initialize({
        client_id: cid,
        callback: async (response) => {
          try {
            setAuthError("");
            setIsGoogleLoading(true);

            const data = await googleSignIn(response.credential);
            localStorage.setItem("token", data.access_token);
            navigate("/home");
          } catch (err) {
            setAuthError(err.message || "Google sign-in failed");
          } finally {
            setIsGoogleLoading(false);
          }
        },
      });

      googleBtnRef.current.innerHTML = "";
      window.google.accounts.id.renderButton(googleBtnRef.current, {
        theme: "outline",
        size: "large",
        type: "standard",
        width: 320,
      });
    };

    loadGoogleScript();

    return () => {
      cancelled = true;
    };
  }, [googleClientId, hasValidGoogleClientId, navigate]);

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-black text-white overflow-hidden">

      
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_30%,rgba(59,130,246,0.3),transparent_40%),radial-gradient(circle_at_80%_70%,rgba(168,85,247,0.3),transparent_40%)]" />

      
      <div className="absolute w-full h-full opacity-20 bg-[linear-gradient(120deg,transparent,rgba(255,255,255,0.1),transparent)] animate-pulse" />

      
      <FloatingPanel text=" AI negotiating prices..." top="15%" left="8%" />
      <FloatingPanel text=" Best deal found!" top="70%" left="75%" delay={1} />
      <FloatingPanel text=" Real-time supplier match" top="80%" left="20%" delay={2} />

      
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="relative z-10 w-full max-w-md p-8 rounded-3xl bg-white/10 backdrop-blur-2xl border border-white/20 shadow-[0_0_40px_rgba(59,130,246,0.2)]"
      >

        
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

          
          <motion.button
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            onClick={() => navigate("/home")}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 shadow-lg hover:shadow-blue-500/30 transition"
          >
            {isLogin ? "Sign In" : "Register"}
          </motion.button>

          
          <div className="flex items-center gap-3 text-gray-400 text-sm">
            <div className="flex-1 h-px bg-gray-600" />
            OR
            <div className="flex-1 h-px bg-gray-600" />
          </div>

          
          <div className="flex gap-4">
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2 text-sm text-gray-300">
                <GoogleIcon />
                Google
              </div>
              <div ref={googleBtnRef} className="min-h-[40px]" />
              {!googleClientId && (
                <button
                  type="button"
                  onClick={() => setAuthError("Set VITE_GOOGLE_CLIENT_ID in frontend env to enable Google sign-in.")}
                  className="w-full py-2 border border-gray-600 rounded-lg hover:bg-white/10 transition flex items-center justify-center gap-2"
                >
                  <GoogleIcon />
                  Sign in with Google
                </button>
              )}
              {googleClientId && !hasValidGoogleClientId && (
                <button
                  type="button"
                  onClick={() =>
                    setAuthError(
                      "OAuth config error (GeneralOAuthFlow). Replace client secret with Web Client ID in frontend and backend env."
                    )
                  }
                  className="w-full py-2 border border-amber-500/60 rounded-lg hover:bg-amber-500/10 transition flex items-center justify-center gap-2 text-amber-200"
                >
                  <GoogleIcon />
                  Fix Google OAuth Config
                </button>
              )}
              {!googleClientId && (
                <p className="text-xs text-yellow-300 mt-2">
                  Set VITE_GOOGLE_CLIENT_ID in frontend env to enable Google sign-in.
                </p>
              )}
              {googleClientId && !hasValidGoogleClientId && (
                <p className="text-xs text-amber-300 mt-2">
                  Current value is not a Web Client ID. It must end with .apps.googleusercontent.com
                </p>
              )}
            </div>
            <SocialBtn text="GitHub" />
          </div>

          {isGoogleLoading && (
            <p className="text-sm text-blue-300">Signing in with Google...</p>
          )}

          {authError && (
            <p className="text-sm text-red-400">{authError}</p>
          )}
        </div>

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

function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true">
      <path fill="#EA4335" d="M12 10.2v3.9h5.5c-.2 1.3-1.6 3.8-5.5 3.8-3.3 0-6.1-2.8-6.1-6.2s2.8-6.2 6.1-6.2c1.9 0 3.2.8 3.9 1.5l2.7-2.7C17.2 2.9 14.8 2 12 2 6.9 2 2.8 6.2 2.8 11.3S6.9 20.6 12 20.6c6.9 0 9.2-4.8 9.2-7.3 0-.5-.1-.9-.1-1.3H12z" />
    </svg>
  );
}


function Input({ placeholder, type = "text" }) {
  return (
    <input
      type={type}
      placeholder={placeholder}
      className="w-full p-3 rounded-xl bg-black/40 border border-gray-700 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/30 outline-none transition"
    />
  );
}


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


function SocialBtn({ text }) {
  return (
    <button className="flex-1 py-2 border border-gray-600 rounded-lg hover:bg-white/10 transition">
      {text}
    </button>
  );
}