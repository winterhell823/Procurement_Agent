import { useEffect, useState } from "react";
import { FileText, Globe, BarChart3, CheckCircle } from "lucide-react";

const steps = [
  { text: "Parsing product specifications...", icon: <FileText size={16} /> },
  { text: "Searching 15 supplier databases...", icon: <Globe size={16} /> },
  { text: "Filling quote forms on supplier portals...", icon: <Globe size={16} /> },
  { text: "Logging into manufacturer portals...", icon: <Globe size={16} /> },
  { text: "6 quotes received — comparing now...", icon: <BarChart3 size={16} /> },
  { text: "Best deal found: $4.20/unit 🎉", icon: <CheckCircle size={16} />, success: true },
];

export default function AIProcessDemo() {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (index >= steps.length) return;

    const timer = setTimeout(() => {
      setIndex((prev) => prev + 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [index]);

  return (
    <div className="bg-[#0f172a] border border-white/10 rounded-2xl p-6 max-w-2xl mx-auto text-left">

      
      <div className="mb-6 bg-[#020617] border border-white/10 rounded-lg px-4 py-3 text-sm text-gray-300">
        500 units of industrial gloves, size L, nitrile, powder-free
      </div>

      
      <div className="space-y-4">
        {steps.slice(0, index).map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 text-sm transition-all duration-500 ${
              step.success ? "text-green-400" : "text-gray-300"
            }`}
          >
            <span className="text-blue-400">{step.icon}</span>
            {step.text}
          </div>
        ))}
      </div>
    </div>
  );
}