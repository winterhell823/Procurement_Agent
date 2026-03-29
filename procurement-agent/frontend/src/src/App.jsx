import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { RequestProvider } from "./context/RequestContext";
import { AuthProvider } from "./context/AuthContext";
import { Toaster } from "react-hot-toast";


import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Homepage from "./pages/Homepage";
import Dashboard from "./pages/Dashboard";
import NewRequest from "./pages/NewRequest";
import AgentPage from "./pages/AgentPage";


const isAuthenticated = () => {
  return !!localStorage.getItem("token");
};


function ProtectedRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/auth" />;
}

export default function App() {
  return (
    <AuthProvider>
      <RequestProvider>
        <BrowserRouter>

        <Toaster position="top-right" />

        <Routes>

          
          <Route path="/" element={<LandingPage />} />

        
          <Route path="/home" element={<Homepage />} />
          <Route path="/auth" element={<AuthPage />} />

         
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />

          <Route
            path="/new-request"
            element={
              <ProtectedRoute>
                <NewRequest />
              </ProtectedRoute>
            }
          />

          <Route
            path="/agent/:procurementId"
            element={
              <ProtectedRoute>
                <AgentPage />
              </ProtectedRoute>
            }
          />

        
          <Route
            path="*"
            element={
              <div className="text-white flex items-center justify-center h-screen text-2xl">
                404 - Page Not Found
              </div>
            }
          />

        </Routes>

      </BrowserRouter>
    </RequestProvider>
  </AuthProvider>
  );
}