import { BrowserRouter, Routes, Route } from "react-router-dom";
import React from "react";
import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Homepage from "./pages/Homepage";
import Dashboard from "./pages/Dashboard";
import NewRequest from "./pages/NewRequest";

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, message: "" };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, message: error?.message || "Unexpected error" };
  }

  componentDidCatch(error, info) {
    console.error("App render error:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-black text-white flex items-center justify-center p-6">
          <div className="max-w-xl w-full border border-red-500/40 bg-red-500/10 rounded-xl p-5">
            <h1 className="text-xl font-semibold mb-2">Frontend runtime error</h1>
            <p className="text-sm text-red-200 break-words">{this.state.message}</p>
            <p className="text-xs text-gray-300 mt-3">
              Open DevTools console for the full stack trace.
            </p>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default function App() {
  return (
    <AppErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/auth" element={<AuthPage />} />
          <Route path="/home" element={<Homepage />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/new-request" element={<NewRequest />} />
        </Routes>
      </BrowserRouter>
    </AppErrorBoundary>
  );
}