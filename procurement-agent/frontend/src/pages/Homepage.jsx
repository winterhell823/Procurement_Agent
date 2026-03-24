import { useNavigate } from "react-router-dom";

export default function Homepage() {
  const navigate = useNavigate();

  return (
    <div className="bg-black text-white min-h-screen relative overflow-x-hidden">

      
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_20%_30%,rgba(59,130,246,0.15),transparent_40%),radial-gradient(circle_at_80%_70%,rgba(168,85,247,0.15),transparent_40%)]" />

      
      <div className="flex justify-between items-center px-10 py-6 border-b border-white/10">
        <h1 className="text-xl font-bold">
          Procure<span className="text-blue-400">AI</span>
        </h1>

        <div className="flex gap-4">
          <button
            onClick={() => navigate("/auth")}
            className="px-5 py-2 border border-gray-600 rounded-lg hover:bg-white/10 transition"
          >
            Sign In
          </button>

          <button
            onClick={() => navigate("/dashboard")}
            className="px-5 py-2 bg-blue-500 rounded-lg hover:opacity-90"
          >
            Dashboard
          </button>
        </div>
      </div>

      
      <div className="px-10 mt-16 grid md:grid-cols-2 gap-10 items-center">

        
        <div>
          <h1 className="text-5xl md:text-6xl font-bold leading-tight">
            Stop Wasting Time on
            <br />
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              Supplier Quotes
            </span>
          </h1>

          <p className="text-gray-400 mt-6">
            Let AI handle the tedious work of getting quotes from multiple suppliers.
            Save 15-20 hours per week and reduce procurement costs by up to 40%.
          </p>

          
          <div className="flex gap-4 mt-8">

            <button
              onClick={() => navigate("/new-request")}
              className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg shadow-lg hover:scale-105 transition"
            >
              New Procurement Request
            </button>

            <button
              onClick={() => navigate("/dashboard")}
              className="px-6 py-3 border border-gray-600 rounded-lg hover:bg-white/10"
            >
              View Dashboard
            </button>

          </div>
        </div>

        
        <div className="space-y-4">
          <GlassCard text=" AI agent scanning 15 suppliers..." />
          <GlassCard text=" Comparing prices across vendors" />
          <GlassCard text=" Best quote found: $2,450!" />

          <div className="grid grid-cols-3 gap-4 mt-6">
            <Stat value="15-20 hrs" label="Saved/week" />
            <Stat value="40%" label="Cost Reduction" />
            <Stat value="10-15" label="Suppliers" />
          </div>
        </div>
      </div>

      
      <SectionTitle title="How It Works" />

      <div className="grid md:grid-cols-2 gap-6 px-10">
        <FeatureCard title="Multi-Supplier Search" desc="AI scans 10-15 supplier websites instantly." />
        <FeatureCard title="Automated Form Filling" desc="Auto-fills quote forms across platforms." />
        <FeatureCard title="Smart Comparison" desc="Compare all quotes in one dashboard." />
        <FeatureCard title="Auto-Outreach" desc="AI emails best supplier automatically." />
      </div>

      
      <SectionTitle title="Why Choose ProcureAI?" />

      <div className="grid md:grid-cols-4 gap-6 px-10">
        <FeatureCard title="Secure & Compliant" desc="Enterprise-grade security." />
        <FeatureCard title="Best Price Guarantee" desc="Always get best value." />
        <FeatureCard title="Detailed Analytics" desc="Track spending patterns." />
        <FeatureCard title="Audit Trail" desc="Complete documentation." />
      </div>

      
      <SectionTitle title="Trusted by SMBs Worldwide" />

      <div className="grid md:grid-cols-3 gap-6 px-10">
        <Testimonial text="Reduced procurement time drastically!" name="Sarah Chen" />
        <Testimonial text="Saved 35% cost instantly!" name="Michael Roberts" />
        <Testimonial text="Best tool for SMBs!" name="Emily Park" />
      </div>

      
      <div className="text-center text-gray-500 text-sm py-10 border-t border-white/10 mt-20">
        © 2026 ProcureAI
      </div>
    </div>
  );
}

////////////////////////////////////////////////////

function GlassCard({ text }) {
  return (
    <div className="bg-white/10 p-4 rounded-xl border border-white/10 hover:scale-105 transition">
      {text}
    </div>
  );
}

function Stat({ value, label }) {
  return (
    <div className="bg-white/10 p-4 rounded-xl text-center">
      <h2 className="font-bold">{value}</h2>
      <p className="text-gray-400 text-sm">{label}</p>
    </div>
  );
}

function SectionTitle({ title }) {
  return (
    <div className="mt-28 mb-12 text-center">
      <h2 className="text-3xl font-bold">{title}</h2>
      <div className="w-16 h-[2px] bg-blue-400 mx-auto mt-3" />
    </div>
  );
}

function FeatureCard({ title, desc }) {
  return (
    <div className="bg-white/10 p-6 rounded-xl border border-white/10 hover:scale-105 transition">
      <h3 className="font-semibold mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{desc}</p>
    </div>
  );
}

function Testimonial({ text, name }) {
  return (
    <div className="bg-white/10 p-6 rounded-xl border border-white/10">
      <div className="text-yellow-400 mb-2">★★★★★</div>
      <p className="text-gray-300 mb-4">"{text}"</p>
      <p className="text-sm text-gray-500">{name}</p>
    </div>
  );
}