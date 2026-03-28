import { createContext, useContext, useState } from "react";

const RequestContext = createContext();

export function RequestProvider({ children }) {
  const [requests, setRequests] = useState([]);

  const addRequest = (data) => {
    const newRequest = {
      id: Date.now(),
      title: data.title,
      quantity: data.quantity,
      status: "processing",
      supplier: null,
      price: null,
    };

    setRequests((prev) => [...prev, newRequest]);

   
    setTimeout(() => {
      setRequests((prev) =>
        prev.map((req) =>
          req.id === newRequest.id
            ? {
                ...req,
                status: "completed",
                supplier: "ABC Supplies",
                price: "$" + (Math.floor(Math.random() * 500) + 100),
              }
            : req
        )
      );
    }, 3000);
  };

  return (
    <RequestContext.Provider value={{ requests, addRequest }}>
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