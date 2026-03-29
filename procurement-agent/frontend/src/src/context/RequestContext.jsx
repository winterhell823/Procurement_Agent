import { createContext, useContext, useState, useEffect } from "react";
import { getProcurementRequests, createProcurementRequest } from "../services/api";

const RequestContext = createContext();

export function RequestProvider({ children }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Fetch requests from backend
  const fetchRequests = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getProcurementRequests();
      setRequests(data || []);
    } catch (err) {
      setError(err.message);
      console.error("Failed to fetch requests:", err);
    } finally {
      setLoading(false);
    }
  };

  // Load requests on mount
  useEffect(() => {
    const token = localStorage.getItem("token");
    if (token) {
      fetchRequests();
    }
  }, []);

  // Add new request
  const addRequest = async (data) => {
    try {
      setError(null);
      const newRequest = await createProcurementRequest(data);
      // Add to local state immediately for responsiveness
      setRequests((prev) => [newRequest, ...prev]);
      return newRequest;
    } catch (err) {
      setError(err.message);
      console.error("Failed to create request:", err);
      throw err;
    }
  };

  return (
    <RequestContext.Provider
      value={{
        requests,
        loading,
        error,
        addRequest,
        fetchRequests,
      }}
    >
      {children}
    </RequestContext.Provider>
  );
}

export const useRequests = () => {
  const context = useContext(RequestContext);

  if (!context) {
    throw new Error("useRequests must be used inside RequestProvider");
  }

  return context;
};