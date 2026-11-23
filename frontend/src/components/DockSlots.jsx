import React from 'react';

export default function DockSlots({ slots }) {
  return (
    <section>
      <div className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
        <span className="w-2 h-2 rounded-full bg-emerald-400"></span> Charging Bays (Identical 50 kW Docks)
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {slots.map(slot => {
          const isOccupied = slot.status === 'OCCUPIED';
          return (
            <div
              key={slot.slot_number}
              className={`rounded-2xl p-4 border transition-all ${
                isOccupied
                  ? 'bg-gradient-to-b from-slate-900 to-slate-950 border-emerald-500/40 shadow-lg shadow-emerald-950/20'
                  : 'bg-slate-900/60 border-slate-800'
              }`}
            >
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-mono font-bold text-slate-300">DOCK #0{slot.slot_number}</span>
                <span
                  className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                    isOccupied
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                      : 'bg-slate-800 text-slate-400 border border-slate-700'
                  }`}
                >
                  {isOccupied ? '⚡ Charging' : '○ Available'}
                </span>
              </div>

              <div className="min-h-[85px] flex flex-col justify-center">
                {isOccupied ? (
                  <>
                    <div className="flex justify-between items-baseline mb-1">
                      <span className="text-sm font-mono font-bold text-white">{slot.current_vehicle_id}</span>
                      <span className="text-xs font-mono text-emerald-400 font-semibold">{slot.remaining_minutes}m left</span>
                    </div>
                    <div className="w-full bg-slate-950 rounded-full h-2 mb-2 overflow-hidden border border-slate-800">
                      <div
                        className="bg-gradient-to-r from-emerald-500 to-teal-400 h-2 rounded-full transition-all duration-500"
                        style={{ width: `${slot.progress_pct}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-[10px] text-slate-400 font-mono">
                      <span>SoC: {slot.progress_pct}%</span>
                      <span>50 kW Fast</span>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-3 text-slate-500 text-xs">
                    <div className="text-lg mb-1">🔌</div>
                    <div>Slot Available</div>
                  </div>
                )}
              </div>

              <div className="mt-3 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400 font-mono">
                <span>Delivered: {slot.total_energy_delivered.toFixed(1)} kWh</span>
                <span>Sessions: {slot.total_sessions_completed}</span>
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}

