import { useState, useEffect, useRef } from "react";
import { getProcurementRequest } from "./api";

export function useProcurement(procurementId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const pollingRef = useRef(null);

  useEffect(() => {
    if (!procurementId) return;

    const fetchStatus = async () => {
      // Pause polling if document is hidden
      if (document.visibilityState !== 'visible') return;

      try {
        const result = await getProcurementRequest(procurementId);
        setData(result);
        setError(null);
        
        // Stop polling if completed or failed
        if (result.status === 'completed' || result.status === 'failed') {
          if (pollingRef.current) clearInterval(pollingRef.current);
        }
      } catch (err) {
        console.error("Polling error:", err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    // Initial fetch
    fetchStatus();

    // Start polling every 2s
    pollingRef.current = setInterval(fetchStatus, 2000);

    // Listen for visibility change to trigger fetch immediately when coming back
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        fetchStatus();
      }
    };
    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [procurementId]);

  return { data, loading, error };
}
