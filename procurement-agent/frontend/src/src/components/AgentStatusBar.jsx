import React, { memo, useCallback, useEffect, useRef } from "react";
import { FaTerminal } from "react-icons/fa";

// Memoized individual log line
const LogLine = memo(({ text, type }) => {
  const color = type === "error" ? "text-red-400" : type === "success" ? "text-green-400" : "text-gray-300";
  return (
    <div className={`p-1 font-mono text-sm border-l-2 border-transparent hover:border-blue-500/50 hover:bg-white/5 transition-all ${color}`}>
      <span className="opacity-50 mr-2">$</span>
      {text}
    </div>
  );
});

const AgentStatusBar = memo(({ status, logs = [] }) => {
  const scrollRef = useRef(null);
  const prevLogsLength = useRef(0);

  // Auto-scroll logic only if logs length changed
  useEffect(() => {
    if (logs.length > prevLogsLength.current) {
      if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      }
      prevLogsLength.current = logs.length;
    }
  }, [logs.length]);

  return (
    <div className="bg-[#0b0f17] border border-white/10 rounded-xl overflow-hidden flex flex-col h-full shadow-2xl">
      {/* Header */}
      <div className="bg-white/5 px-4 py-3 border-b border-white/10 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <h3 className="text-sm font-semibold text-white tracking-wide uppercase">Agent Execution Log</h3>
        </div>
        <div className="flex items-center gap-2 px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 text-[10px] font-mono text-blue-400 uppercase">
          Status: {status}
        </div>
      </div>

      {/* Terminal Area */}
      <div 
        ref={scrollRef}
        className="flex-1 p-4 overflow-y-auto scroll-smooth custom-scrollbar bg-black/40"
      >
        {logs.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center opacity-20">
            <FaTerminal className="text-4xl mb-2" />
            <p className="text-xs font-mono">Initializing agent connection...</p>
          </div>
        ) : (
          logs.map((log, idx) => (
            <LogLine key={idx} text={log.text || log} type={log.type || 'info'} />
          ))
        )}
      </div>
    </div>
  );
});

export default AgentStatusBar;
