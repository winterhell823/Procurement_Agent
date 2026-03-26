import { FileText, Globe, BarChart3, Mail } from "lucide-react";

export default function ProcessSection() {
  return (
    <section className="px-8 py-28 text-center relative overflow-hidden">

      
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_30%_20%,rgba(59,130,246,0.12),transparent_40%)]"></div>

      <p className="text-blue-400 text-sm mb-4 tracking-wide">
        SIMPLE 4-STEP PROCESS
      </p>

      <h2 className="text-4xl md:text-5xl font-bold leading-tight">
        From spec to{" "}
        <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
          signed PO
        </span>
      </h2>

      <p className="text-gray-400 mt-4 max-w-2xl mx-auto">
        Automate sourcing, supplier outreach, quote comparison, and order placement —
        all powered by intelligent AI workflows.
      </p>

      <div className="grid md:grid-cols-4 gap-8 mt-20">

      
        {[
          {
            icon: <FileText className="text-blue-400" />,
            step: "01",
            title: "Describe Your Need",
            desc: "Upload specs, PDFs, or just type requirements.",
            extra: "Supports BOM, MOQ, certifications & custom inputs.",
            color: "blue",
          },
          {
            icon: <Globe className="text-purple-400" />,
            step: "02",
            title: "AI Finds Suppliers",
            desc: "Scans global supplier network instantly.",
            extra: "Filters by region, pricing, ratings & compliance.",
            color: "purple",
          },
          {
            icon: <BarChart3 className="text-green-400" />,
            step: "03",
            title: "Compare Quotes",
            desc: "All responses organized in one dashboard.",
            extra: "Auto-ranking based on cost, delivery & trust score.",
            color: "green",
          },
          {
            icon: <Mail className="text-cyan-400" />,
            step: "04",
            title: "Close the Deal",
            desc: "Send PO & finalize supplier instantly.",
            extra: "Negotiation + follow-ups handled automatically.",
            color: "cyan",
          },
        ].map((card, i) => (
          <div
            key={i}
            className="group relative rounded-2xl p-[1px] bg-gradient-to-r from-white/10 to-white/5 hover:from-blue-500/40 hover:to-purple-500/40 transition duration-500"
          >
            
            <div className="bg-[#0f172a] rounded-2xl p-6 h-full transition transform group-hover:-translate-y-2 group-hover:scale-[1.02] duration-500">

              
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition duration-500 bg-gradient-to-r from-blue-500/10 to-purple-500/10 blur-xl"></div>

              <div className="relative z-10 text-left">

                
                <div className="w-12 h-12 flex items-center justify-center rounded-xl bg-white/5 mb-6 group-hover:scale-110 transition">
                  {card.icon}
                </div>

                
                <p className="text-xs text-gray-500 mb-2">
                  STEP {card.step}
                </p>

                
                <h3 className="text-lg font-semibold mb-2">
                  {card.title}
                </h3>

                
                <p className="text-gray-400 text-sm">
                  {card.desc}
                </p>

                
                <p className="text-gray-500 text-xs mt-3 opacity-0 group-hover:opacity-100 transition duration-500">
                  {card.extra}
                </p>

              </div>
            </div>
          </div>
        ))}

      </div>
    </section>
  );
}