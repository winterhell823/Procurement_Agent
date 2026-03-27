import { createContext, useContext, useState, useEffect } from "react";

const RequestContext = createContext();

export const RequestProvider = ({ children }) => {
  
  const [requests, setRequests] = useState(() => {
    const saved = localStorage.getItem("requests");
    return saved ? JSON.parse(saved) : [];
  });

  useEffect(() => {
    localStorage.setItem("requests", JSON.stringify(requests));
  }, [requests]);

  
  const addRequest = (data) => {
    const newRequest = {
      id: Date.now(),
      title: data.title,
      quantity: data.quantity,
      extra: data.extra,
      status: "processing",
      date: new Date().toLocaleString(),
      supplier: null,
      price: null,
      unit: null,
    };

    setRequests((prev) => [newRequest, ...prev]);

    
    setTimeout(() => {
      setRequests((prev) =>
        prev.map((r) =>
          r.id === newRequest.id
            ? {
                ...r,
                status: "completed",
                supplier: "AI Supplier Co.",
                price: "$" + (Math.random() * 500).toFixed(2),
                unit: "$" + (Math.random() * 2).toFixed(2) + "/unit",
              }
            : r
        )
      );
    }, 3000);
  };

  return (
    <RequestContext.Provider value={{ requests, addRequest }}>
      {children}
    </RequestContext.Provider>
  );
};

export const useRequest = () => useContext(RequestContext);