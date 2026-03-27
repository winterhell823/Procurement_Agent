import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { RequestProvider } from "./context/RequestContext";
import { Toaster } from "react-hot-toast";

import LandingPage from "./pages/LandingPage";
import AuthPage from "./pages/AuthPage";
import Homepage from "./pages/Homepage";
import Dashboard from "./pages/Dashboard";
import NewRequest from "./pages/NewRequest";


const isAuthenticated = () => {
  return localStorage.getItem("user"); 
};


function ProtectedRoute({ children }) {
  return isAuthenticated() ? children : <Navigate to="/auth" />;
}


export default function App() {
  return (
    <RequestProvider>
      <BrowserRouter>

        
        <Toaster position="top-right" />

        <Routes>

          
          <Route path="/" element={<Navigate to="/home" />} />

          
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

          
          <Route path="*" element={<h1 className="text-white p-10">404 Not Found</h1>} />

        </Routes>

      </BrowserRouter>
    </RequestProvider>
  );
}