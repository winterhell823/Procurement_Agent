import React from "react";
import { useParams, Link } from "react-router-dom";
import DashboardLayout from "../components/DashboardLayout";
import AgentStatusBar from "../components/AgentStatusBar";
import { useProcurement } from "../services/useProcurement";
import { FaGlobe, FaChevronLeft, FaRobot, FaCheckCircle, FaSpinner } from "react-icons/fa";

export default function AgentPage() {
  const { procurementId } = useParams();
  const { data, loading, error } = useProcurement(procurementId);

  const isCompleted = data?.status === "completed";
  const logs = data?.logs || []; // Backend should return job logs

  return (
    <DashboardLayout>
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header Navigation */}
        <div className="flex items-center justify-between">
          <Link 
            to="/dashboard"
            className="flex items-center gap-2 text-gray-400 hover:text-white transition-colors group"
          >
            <FaChevronLeft className="text-xs group-hover:-translate-x-1 transition-transform" />
            <span className="font-medium">Back to Dashboard</span>
          </Link>
          
          <div className="flex items-center gap-3">
            {isCompleted ? (
              <span className="flex items-center gap-2 px-3 py-1 bg-green-500/10 border border-green-500/20 text-green-400 text-xs font-bold rounded-full uppercase tracking-widest">
                <FaCheckCircle /> Mission Accomplished
              </span>
            ) : (
              <span className="flex items-center gap-2 px-3 py-1 bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-bold rounded-full uppercase tracking-widest">
                <FaSpinner className="animate-spin" /> Agent Active
              </span>
            )}
          </div>
        </div>

        {/* Hero Section */}
        <div className="glass p-8 rounded-3xl border border-white/5 relative overflow-hidden bg-gradient-to-br from-blue-500/5 to-purple-500/5">
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-2">
              <div className="flex items-center gap-3 text-blue-400 font-mono text-sm">
                <FaRobot /> ID: {procurementId?.substring(0, 12)}...
              </div>
              <h1 className="text-4xl font-bold text-white tracking-tight">
                {data?.product_name || data?.raw_description || "Analyzing Procurement Request..."}
              </h1>
              <p className="text-gray-400 max-w-2xl leading-relaxed">
                The agent is currently navigating supplier portals, extracting pricing, and performing a reliability match based on your company profile.
              </p>
            </div>
          </div>
        </div>

        {/* Content Grid */}
        <div className="grid lg:grid-cols-2 gap-8 h-[600px]">
          {/* Live Status Panel (Log) */}
          <div className="h-full">
            <AgentStatusBar status={data?.status || "initializing"} logs={logs} />
          </div>

          {/* Browser Viewport Placeholder */}
          <div className="flex flex-col h-full bg-[#0b0f17] border border-white/10 rounded-2xl overflow-hidden shadow-2xl">
            {/* Browser Header */}
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 flex items-center gap-4">
              <div className="flex gap-1.5">
                <div className="w-2.5 h-2.5 rounded-full bg-red-500/50" />
                <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/50" />
                <div className="w-2.5 h-2.5 rounded-full bg-green-500/50" />
              </div>
              <div className="flex-1 bg-black/40 px-3 py-1 rounded text-[10px] text-gray-500 font-mono flex items-center gap-2 truncate">
                <FaGlobe className="text-[8px]" />
                {isCompleted ? "analysis_summary.pdf" : "https://tinyfish-agent-viewport.internal/session/" + procurementId?.substring(0,8)}
              </div>
            </div>

            {/* Viewport Content */}
            <div className="flex-1 relative bg-black/40 flex items-center justify-center p-8 text-center group">
              {!isCompleted ? (
                <div className="w-full max-w-lg h-64 border-2 border-cyan-500/50 rounded-xl relative overflow-hidden flex flex-col items-center justify-center pulse-soft shadow-[0_0_20px_rgba(6,182,212,0.2)]">
                  {/* Animated Skeleton */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-cyan-500/10 to-transparent animate-[load_2s_infinite]" />
                  <FaGlobe className="text-4xl text-cyan-400 mb-4 animate-bounce" />
                  <h3 className="text-lg font-bold text-white mb-2 font-mono">Agent navigating {data?.current_supplier || "supplier"}...</h3>
                  <div className="flex gap-2">
                    <div className="w-16 h-2 bg-cyan-500/30 rounded-full" />
                    <div className="w-8 h-2 bg-cyan-500/30 rounded-full" />
                    <div className="w-24 h-2 bg-cyan-500/30 rounded-full" />
                  </div>
                </div>
              ) : (
                <div className="space-y-6 w-full max-w-lg animate-fadeIn text-left">
                  <div className="flex items-center gap-4 mb-6">
                    <div className="w-12 h-12 bg-green-500/10 border border-green-500/20 rounded-full flex items-center justify-center text-green-400 text-2xl shadow-[0_0_30px_rgba(34,197,94,0.15)]">
                      <FaCheckCircle />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-white">Job Completed</h3>
                      <p className="text-sm text-gray-400 font-mono">All supplier sources ranked</p>
                    </div>
                  </div>

                  {/* Summary of what each agent did */}
                  <div className="space-y-3 mb-6">
                    {data?.quotes?.length > 0 ? data.quotes.map((q, i) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-white/5 rounded-lg border border-white/10 font-mono text-sm">
                        <span className="text-white">{q.supplier_name}</span>
                        <div className="flex gap-4">
                          <span className={q.status === 'failed' ? "text-red-400" : "text-green-400"}>
                            {q.status === 'failed' ? 'Failed' : 'Success'}
                          </span>
                          <span className="text-cyan-400 w-16 text-right">${q.price || '-'}</span>
                        </div>
                      </div>
                    )) : (
                      <div className="p-3 bg-white/5 rounded-lg border border-white/10 font-mono text-sm text-gray-400">
                        Summary extracted from agent operations. Validating quotes...
                      </div>
                    )}
                  </div>

                  <div className="flex justify-center mt-8">
                    <Link 
                      to={`/quotes/${procurementId}`}
                      className="inline-flex items-center gap-2 px-8 py-3 bg-cyan-600 hover:bg-cyan-500 text-white rounded-xl text-sm font-bold transition-all hover:scale-105 active:scale-95 shadow-lg shadow-cyan-500/20"
                    >
                      View Quotes
                    </Link>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}
