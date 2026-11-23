import React, { useState } from 'react';

export default function RequestForm({ onSubmitted }) {
  const [vehicleId, setVehicleId] = useState('');
  const [batteryCap, setBatteryCap] = useState(60);
  const [currentSoc, setCurrentSoc] = useState(20);
  const [targetSoc, setTargetSoc] = useState(80);
  const [priority, setPriority] = useState(1);

  const socDelta = Math.max(0, targetSoc - currentSoc) / 100.0;
  const energyNeeded = (batteryCap * socDelta).toFixed(1);
  const chargingTime = ((energyNeeded / 50.0) * 60.0).toFixed(1);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/requests/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          vehicle_id: vehicleId || undefined,
          battery_capacity_kwh: parseFloat(batteryCap),
          current_soc_pct: parseFloat(currentSoc),
          target_soc_pct: parseFloat(targetSoc),
          charger_power_kw: 50.0,
          priority: parseInt(priority)
        })
      });
      if (res.ok) {
        setVehicleId('');
        onSubmitted();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const injectRushHour = async (type, count) => {
    try {
      await fetch('/api/rush-hour/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ batch_type: type, count: count })
      });
      onSubmitted();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <h3 className="text-sm font-bold text-white mb-1">Request Charging Slot</h3>
        <p className="text-xs text-slate-400 mb-4">Submit incoming EV charging requirements</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Vehicle License / ID</label>
            <input
              type="text"
              value={vehicleId}
              onChange={(e) => setVehicleId(e.target.value)}
              placeholder="e.g. EV-204"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-sm text-white font-mono focus:border-emerald-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Battery Size</label>
              <select
                value={batteryCap}
                onChange={(e) => setBatteryCap(Number(e.target.value))}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none"
              >
                <option value={40}>40 kWh (Compact)</option>
                <option value={60}>60 kWh (Standard)</option>
                <option value={75}>75 kWh (Long Range)</option>
                <option value={100}>100 kWh (Fleet)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Charger Rating</label>
              <div className="bg-slate-950/70 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-400 font-mono">
                50.0 kW
              </div>
            </div>
          </div>

          <div className="space-y-3 bg-slate-950/60 p-3 rounded-xl border border-slate-800/80">
            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Current SoC:</span>
                <span className="font-bold text-amber-400">{currentSoc}%</span>
              </div>
              <input
                type="range"
                min="5"
                max="80"
                step="5"
                value={currentSoc}
                onChange={(e) => {
                  const val = Number(e.target.value);
                  setCurrentSoc(val);
                  if (val >= targetSoc) setTargetSoc(val + 10);
                }}
                className="w-full accent-amber-500"
              />
            </div>

            <div>
              <div className="flex justify-between text-xs text-slate-300 mb-1">
                <span>Target SoC:</span>
                <span className="font-bold text-emerald-400">{targetSoc}%</span>
              </div>
              <input
                type="range"
                min="30"
                max="100"
                step="5"
                value={targetSoc}
                onChange={(e) => setTargetSoc(Number(e.target.value))}
                className="w-full accent-emerald-500"
              />
            </div>

            <div className="pt-2 border-t border-slate-800/80 flex justify-between text-xs font-mono">
              <span className="text-slate-400 font-sans">Energy Needed:</span>
              <span className="text-white font-bold">{energyNeeded} kWh</span>
            </div>
            <div className="flex justify-between text-xs font-mono">
              <span className="text-slate-400 font-sans">Estimated Time:</span>
              <span className="text-emerald-400 font-bold">{chargingTime} min</span>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-300 mb-1">Priority Level</label>
            <div className="grid grid-cols-3 gap-2">
              <label className={`cursor-pointer border rounded-xl p-2 text-center text-xs flex flex-col items-center ${priority === 1 ? 'border-emerald-500 bg-emerald-950/30 text-emerald-400 font-bold' : 'border-slate-800 bg-slate-950 text-slate-400'}`}>
                <input type="radio" name="pri" value={1} checked={priority === 1} onChange={() => setPriority(1)} className="hidden" />
                <span>Normal</span>
                <span className="text-[9px] opacity-70">Tier 1</span>
              </label>
              <label className={`cursor-pointer border rounded-xl p-2 text-center text-xs flex flex-col items-center ${priority === 2 ? 'border-blue-500 bg-blue-950/30 text-blue-400 font-bold' : 'border-slate-800 bg-slate-950 text-slate-400'}`}>
                <input type="radio" name="pri" value={2} checked={priority === 2} onChange={() => setPriority(2)} className="hidden" />
                <span>High</span>
                <span className="text-[9px] opacity-70">Tier 2</span>
              </label>
              <label className={`cursor-pointer border rounded-xl p-2 text-center text-xs flex flex-col items-center ${priority === 3 ? 'border-red-500 bg-red-950/30 text-red-400 font-bold' : 'border-slate-800 bg-slate-950 text-slate-400'}`}>
                <input type="radio" name="pri" value={3} checked={priority === 3} onChange={() => setPriority(3)} className="hidden" />
                <span>Urgent</span>
                <span className="text-[9px] opacity-70">Tier 3</span>
              </label>
            </div>
          </div>

          <button
            type="submit"
            className="w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 font-semibold text-sm text-white shadow-lg shadow-emerald-900/30 transition"
          >
            Submit Request to Station
          </button>
        </form>
      </div>

      {/* Demand Generator */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl space-y-3">
        <h4 className="text-xs font-bold text-white uppercase tracking-wider">Rush-Hour Injections</h4>
        <div className="grid grid-cols-2 gap-2">
          <button onClick={() => injectRushHour('morning', 5)} className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:bg-slate-800 text-left transition">
            <div className="text-xs font-bold text-amber-300">🌅 Morning Rush</div>
            <div className="text-[10px] text-slate-400">Add 5 EVs</div>
          </button>
          <button onClick={() => injectRushHour('evening', 6)} className="p-2 rounded-xl bg-slate-950 border border-slate-800 hover:bg-slate-800 text-left transition">
            <div className="text-xs font-bold text-orange-400">🌆 Evening Peak</div>
            <div className="text-[10px] text-slate-400">Add 6 EVs</div>
          </button>
        </div>
      </div>
    </div>
  );
}

