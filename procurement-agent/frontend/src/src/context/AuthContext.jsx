import React, { createContext, useContext, useState, useEffect, useCallback } from "react";
import { getCurrentUser } from "../services/api";

const AuthContext = createContext();

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      if (token) {
        setLoading(true);
        const userData = await getCurrentUser();
        setUser(userData);
      } else {
        setUser(null);
      }
    } catch (error) {
      console.error("Failed to fetch user:", error);
      setUser(null);
      localStorage.removeItem("token");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
    window.location.href = "/auth";
  };

  return (
    <AuthContext.Provider value={{ user, loading, fetchUser, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
