import { BrowserRouter, Routes, Route } from "react-router-dom";

import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Homepage from "./pages/Homepage";
import Dashboard from "./pages/Dashboard";
import NewRequest from "./pages/NewRequest";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* 🌐 PUBLIC */}
        <Route path="/" element={<LandingPage />} />

        {/* 🔐 AUTH */}
        <Route path="/auth" element={<AuthPage />} />

        {/* 🏠 AFTER LOGIN */}
        <Route path="/home" element={<Homepage />} />

        {/* 📊 MAIN APP */}
        <Route path="/dashboard" element={<Dashboard />} />
        
<Route path="/new-request" element={<NewRequest />} />

      </Routes>
    </BrowserRouter>
  );
}