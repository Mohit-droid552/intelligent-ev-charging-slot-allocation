import React from 'react';

export default function QueueTable({ queue, recentCompleted, algo }) {
  return (
    <div className="space-y-6">
      {/* Live Queue */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div className="flex justify-between items-center border-b border-slate-800 pb-3 mb-4">
          <div>
            <h3 className="text-sm font-bold text-white">Live Scheduling Queue</h3>
            <p className="text-xs text-slate-400">Current waiting list ranked by <span className="text-emerald-400 font-semibold">{algo}</span></p>
          </div>
          <span className="text-xs font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
            {queue.length} pending
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px] font-sans">
              <tr>
                <th className="py-2 px-3">Rank</th>
                <th className="py-2 px-3">Vehicle</th>
                <th className="py-2 px-3">Wait Time</th>
                <th className="py-2 px-3">Charge Duration</th>
                <th className="py-2 px-3">Priority</th>
                <th className="py-2 px-3 text-right">Score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {queue.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-6 text-center text-slate-500 font-sans text-xs">
                    Queue is empty. All vehicles are docked or finished.
                  </td>
                </tr>
              ) : (
                queue.map((req, idx) => (
                  <tr key={req.id} className="hover:bg-slate-800/40 transition">
                    <td className="py-2 px-3">
                      <span className={`w-5 h-5 inline-flex items-center justify-center rounded-full ${idx === 0 ? 'bg-emerald-500/20 text-emerald-400 font-bold' : 'text-slate-400'}`}>
                        #{idx + 1}
                      </span>
                    </td>
                    <td className="py-2 px-3 font-bold text-white">{req.vehicle_id}</td>
                    <td className="py-2 px-3 text-amber-300 font-semibold">{req.current_wait_time.toFixed(1)}m</td>
                    <td className="py-2 px-3 text-emerald-400">{req.charging_time_minutes.toFixed(1)}m</td>
                    <td className="py-2 px-3 font-sans">
                      {req.priority === 3 ? (
                        <span className="text-red-400 font-bold">🚨 Urgent</span>
                      ) : req.priority === 2 ? (
                        <span className="text-blue-400 font-bold">High</span>
                      ) : (
                        <span className="text-slate-400">Normal</span>
                      )}
                    </td>
                    <td className="py-2 px-3 text-right font-bold text-indigo-400">{req.computed_score}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Recent Completed */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-3">Recently Completed</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="text-slate-400 border-b border-slate-800 uppercase tracking-wider text-[10px] font-sans">
              <tr>
                <th className="py-1.5 px-3">Vehicle</th>
                <th className="py-1.5 px-3">Wait Time</th>
                <th className="py-1.5 px-3">Energy</th>
                <th className="py-1.5 px-3">Algo</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {recentCompleted.length === 0 ? (
                <tr>
                  <td colSpan="4" className="py-3 text-center text-slate-500 font-sans text-xs">No sessions completed yet.</td>
                </tr>
              ) : (
                recentCompleted.map(c => (
                  <tr key={c.id} className="text-slate-300 hover:bg-slate-800/30">
                    <td className="py-1.5 px-3 font-bold text-white">{c.vehicle_id}</td>
                    <td className="py-1.5 px-3 text-amber-300">{c.wait_time_minutes ? c.wait_time_minutes.toFixed(1) + 'm' : '0.0m'}</td>
                    <td className="py-1.5 px-3 text-emerald-400">{c.energy_needed_kwh.toFixed(1)} kWh</td>
                    <td className="py-1.5 px-3 text-[10px] font-sans text-slate-400">{c.algorithm_used}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

