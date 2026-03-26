import {
  Brain,
  Eye,
  ShieldCheck,
  Clock,
  DollarSign,
  RefreshCw,
  Lock,
  BarChart3,
  Zap,
} from "lucide-react";

import { motion } from "framer-motion";

const features = [
  {
    icon: <Brain />,
    title: "AI-Powered Negotiation",
    desc: "Machine learning optimizes your procurement strategy based on historical data and market trends.",
  },
  {
    icon: <Eye />,
    title: "Real-Time Tracking",
    desc: "Watch quotes arrive in real-time. Every supplier interaction is logged and visible.",
  },
  {
    icon: <ShieldCheck />,
    title: "Supplier Verification",
    desc: "Auto-verified supplier credentials, reviews, and compliance before any quote request.",
  },
  {
    icon: <Clock />,
    title: "95% Time Savings",
    desc: "What took 3–5 business days now takes under 15 minutes from spec to compared quotes.",
  },
  {
    icon: <DollarSign />,
    title: "Cost Optimization",
    desc: "AI analyzes pricing patterns to ensure you always get the most competitive rates.",
  },
  {
    icon: <RefreshCw />,
    title: "Auto-Renewal Alerts",
    desc: "Never miss a contract renewal. Get notified before terms expire with better alternatives.",
  },
  {
    icon: <Lock />,
    title: "Secure Portals",
    desc: "Bank-level encryption for all supplier communication and credential management.",
  },
  {
    icon: <BarChart3 />,
    title: "Spend Analytics",
    desc: "Deep insights into your procurement spend across categories, suppliers, and time.",
  },
  {
    icon: <Zap />,
    title: "Instant Comparison",
    desc: "Side-by-side quote comparison with weighted scoring on price, quality, and delivery.",
  },
];

export default function FeaturesSection() {
  return (
    <section className="px-8 py-28 relative">

      
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_70%_20%,rgba(59,130,246,0.12),transparent_40%)]"></div>

      
      <div className="text-center mb-16">
        <p className="text-blue-400 text-sm mb-3 tracking-wide">
          POWERFUL FEATURES
        </p>

        <h2 className="text-4xl md:text-5xl font-bold">
          Everything you need to{" "}
          <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
            automate procurement
          </span>
        </h2>
      </div>

      
      <div className="grid md:grid-cols-3 gap-6">

        {features.map((feature, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, y: 60 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-50px" }}
            transition={{ duration: 0.6, delay: i * 0.15 }}
            className="group relative rounded-2xl p-[1px] bg-gradient-to-r from-white/10 to-white/5 hover:from-blue-500/40 hover:to-purple-500/40 transition duration-500"
          >
           
            <div className="bg-[#0f172a] rounded-2xl p-6 h-full transition transform group-hover:-translate-y-2 group-hover:scale-[1.02] duration-500">

             
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition duration-500 bg-gradient-to-r from-blue-500/10 to-purple-500/10 blur-xl"></div>

              <div className="relative z-10">

                
                <div className="w-12 h-12 flex items-center justify-center rounded-xl bg-white/5 mb-6 text-blue-400 group-hover:scale-110 transition">
                  {feature.icon}
                </div>

                
                <h3 className="text-lg font-semibold mb-2">
                  {feature.title}
                </h3>

                
                <p className="text-gray-400 text-sm leading-relaxed">
                  {feature.desc}
                </p>

              </div>
            </div>
          </motion.div>
        ))}

      </div>
    </section>
  );
}