import DashboardLayout from "../components/DashboardLayout";
import FeaturesSection from "../components/FeaturesSection";
import AIProcessDemo from "../components/AIProcessDemo";
import ProcessSection from "../components/ProcessSection";
import AINetwork from "../components/AINetwork";
import Footer from "../components/Footer";
import { Bot } from "lucide-react";

export default function Homepage() {
  return (
    <DashboardLayout>
      <div className="bg-[#0b0f17] text-white min-h-screen">
        
        <nav className="flex justify-between items-center px-8 py-5 border-b border-white/10">
          <div className="flex items-center gap-2 text-lg font-semibold">
            <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
              <Bot size={18} />
            </div>
            ProcureAI
          </div>

          <div className="flex items-center gap-4">
            <button className="text-gray-300">Log in</button>
            <button className="bg-gradient-to-r from-blue-500 to-purple-500 px-5 py-2 rounded-lg text-sm font-medium">
              Get Started Free
            </button>
          </div>
        </nav>

        
        <section className="grid md:grid-cols-2 gap-10 px-8 py-20 items-center">
          <div>
            <p className="text-blue-400 mb-4 text-sm">
              AI-Powered Procurement Automation
            </p>

            <h1 className="text-5xl font-bold leading-tight">
              Stop chasing <br />
              <span className="bg-gradient-to-r from-blue-400 to-purple-500 bg-clip-text text-transparent">
                supplier quotes.
              </span>
            </h1>

            <p className="text-gray-400 mt-6 max-w-lg">
              Give our AI agent a product spec and watch it navigate supplier
              portals, request quotes, track responses, and close the best deal.
            </p>

            <div className="flex gap-4 mt-8">
              <button className="bg-gradient-to-r from-blue-500 to-purple-500 px-6 py-3 rounded-lg font-medium">
                Start Procuring
              </button>
              <button className="border border-white/20 px-6 py-3 rounded-lg">
                Watch Demo
              </button>
            </div>
          </div>

          <div className="h-[420px] relative">
            <AINetwork />

            <div className="absolute top-16 right-10 bg-black/60 backdrop-blur-md border border-white/10 px-4 py-3 rounded-xl">
              <p className="text-sm text-gray-400">Best Quote Found</p>
              <p className="text-green-400 font-semibold">$4.20 / unit</p>
            </div>

            <div className="absolute bottom-16 left-10 bg-black/60 backdrop-blur-md border border-white/10 px-4 py-3 rounded-xl">
              <p className="text-sm text-gray-400">Suppliers Contacted</p>
              <p className="text-blue-400 font-semibold">14 / 15</p>
            </div>
          </div>
        </section>

        
        <ProcessSection />

        
        <section className="px-8 py-24">
          <h2 className="text-4xl font-bold text-center mb-12">
            See it in <span className="text-blue-400">action</span>
          </h2>

          <AIProcessDemo />
        </section>

        <FeaturesSection />
        <Footer />
      </div>
    </DashboardLayout>
  );
}