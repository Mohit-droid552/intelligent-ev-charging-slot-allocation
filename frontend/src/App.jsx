import React, { useState, useEffect } from 'react';
import DockSlots from './components/DockSlots';
import RequestForm from './components/RequestForm';
import QueueTable from './components/QueueTable';

export default function App() {
  const [stationData, setStationData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [autoPlay, setAutoPlay] = useState(false);
  const [benchmarkResult, setBenchmarkResult] = useState(null);
  const [benchmarking, setBenchmarking] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status/');
      if (res.ok) {
        const data = await res.json();
        setStationData(data);
      }
    } catch (err) {
      console.error('Failed to fetch station status:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    let timer = null;
    if (autoPlay) {
      timer = setInterval(() => {
        advanceTime(5);
      }, 1500);
    }
    return () => {
      if (timer) clearInterval(timer);
    };
  }, [autoPlay]);

  const advanceTime = async (delta) => {
    try {
      await fetch('/api/tick/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ delta_minutes: delta })
      });
      fetchStatus();
    } catch (err) {
      console.error(err);
    }
  };

  const switchAlgorithm = async (algo) => {
    try {
      await fetch('/api/algorithm/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ algorithm: algo })
      });
      fetchStatus();
    } catch (err) {
      console.error(err);
    }
  };

  const resetStation = async () => {
    if (window.confirm('Reset station and clear queue?')) {
      setAutoPlay(false);
      await fetch('/api/reset/', { method: 'POST' });
      fetchStatus();
    }
  };

  const runBenchmark = async () => {
    setBenchmarking(true);
    try {
      const res = await fetch('/api/simulate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_vehicles: 42, duration_hours: 16.0 })
      });
      if (res.ok) {
        const data = await res.json();
        setBenchmarkResult(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setBenchmarking(false);
    }
  };

  if (loading || !stationData) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-slate-950 text-white font-mono">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
          <div>Loading EV Charging System...</div>
        </div>
      </div>
    );
  }

  const { config, slots, queue, metrics, recent_completed } = stationData;
  const hours = Math.floor(config.sim_time_minutes / 60);
  const minutes = Math.floor(config.sim_time_minutes % 60);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Navbar */}
      <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-400 flex items-center justify-center font-black text-slate-950 text-lg shadow-lg shadow-emerald-500/20">
              ⚡
            </div>
            <div>
              <h1 className="text-base font-bold text-white flex items-center gap-2">
                Intelligent EV Slot Allocation System
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                  React 18 + DRF
                </span>
              </h1>
              <p className="text-[11px] text-slate-400 font-mono">Non-Preemptive EV Charging Scheduling Prototype</p>
            </div>
          </div>

          <div className="flex items-center gap-2 bg-slate-950/80 border border-slate-800 rounded-xl p-1.5 px-3">
            <div className="text-right">
              <div className="text-[9px] uppercase font-bold text-slate-400">Simulation Time</div>
              <div className="font-mono text-xs font-bold text-emerald-400">
                {String(hours).padStart(2, '0')}h {String(minutes).padStart(2, '0')}m ({config.sim_time_minutes.toFixed(1)}m)
              </div>
            </div>
            <div className="h-6 w-[1px] bg-slate-800 mx-1"></div>
            <button onClick={() => advanceTime(5)} className="px-2 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 border border-slate-700">+5m</button>
            <button onClick={() => advanceTime(15)} className="px-2 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 border border-slate-700">+15m</button>
            <button onClick={() => advanceTime(60)} className="px-2 py-1 text-xs rounded bg-slate-800 hover:bg-slate-700 border border-slate-700">+1h</button>
            <button onClick={() => setAutoPlay(!autoPlay)} className={`px-2.5 py-1 text-xs font-bold rounded ${autoPlay ? 'bg-amber-600 text-white' : 'bg-emerald-600 text-white'}`}>
              {autoPlay ? '⏸ Pause' : '▶ Play'}
            </button>
            <button onClick={resetStation} className="px-2 py-1 text-xs rounded bg-red-950 hover:bg-red-900 text-red-300 border border-red-800" title="Reset">↺</button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-6 space-y-6 flex-1 w-full">
        {/* Algorithm Bar */}
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-4 flex flex-col md:flex-row justify-between items-center gap-4">
          <div>
            <div className="text-xs uppercase text-slate-400 font-bold">Active Scheduling Strategy:</div>
            <div className="text-xs text-slate-300 mt-1">
              {config.active_algorithm === 'FCFS' && <span className="text-blue-400 font-semibold">First-Come-First-Served (FCFS): Baseline queueing. All vehicles treated in strict order of arrival.</span>}
              {config.active_algorithm === 'SJF' && <span className="text-amber-400 font-semibold">Shortest Job First (SJF): Minimizes average wait times by serving shortest charging sessions first.</span>}
              {config.active_algorithm === 'HYBRID' && <span className="text-emerald-400 font-semibold">Hybrid Priority Algorithm: Dynamic weighting of wait time, duration and urgency eliminates starvation.</span>}
            </div>
          </div>

          <div className="inline-flex rounded-xl bg-slate-950 p-1 border border-slate-800">
            <button onClick={() => switchAlgorithm('FCFS')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${config.active_algorithm === 'FCFS' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:text-white'}`}>
              FCFS
            </button>
            <button onClick={() => switchAlgorithm('SJF')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${config.active_algorithm === 'SJF' ? 'bg-amber-600 text-white' : 'text-slate-400 hover:text-white'}`}>
              SJF
            </button>
            <button onClick={() => switchAlgorithm('HYBRID')} className={`px-3 py-1.5 rounded-lg text-xs font-bold transition ${config.active_algorithm === 'HYBRID' ? 'bg-emerald-600 text-white' : 'text-slate-400 hover:text-white'}`}>
              ★ Hybrid Priority
            </button>
          </div>
        </section>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="text-xs text-slate-400">Available Docks</div>
            <div className="text-2xl font-black text-white mt-1">{metrics.available_slots} / {slots.length}</div>
            <div className="text-[10px] text-emerald-400">50 kW Fast Chargers</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="text-xs text-slate-400">Pending Queue</div>
            <div className="text-2xl font-black text-white mt-1">{queue.length}</div>
            <div className="text-[10px] text-amber-400">In heap order</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="text-xs text-slate-400">Average Wait Time</div>
            <div className="text-2xl font-black text-white mt-1">{metrics.avg_wait_time_minutes}m</div>
            <div className="text-[10px] text-slate-400">Completed sessions</div>
          </div>
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4">
            <div className="text-xs text-slate-400">Vehicles Completed</div>
            <div className="text-2xl font-black text-white mt-1">{metrics.total_completed}</div>
            <div className="text-[10px] text-emerald-400">Served so far</div>
          </div>
        </div>

        {/* Dock Slots */}
        <DockSlots slots={slots} />

        {/* Grid: Form & Queue */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5 space-y-6">
            <RequestForm onSubmitted={fetchStatus} />
          </div>
          <div className="lg:col-span-7 space-y-6">
            <QueueTable queue={queue} recentCompleted={recent_completed} algo={config.active_algorithm} />
          </div>
        </div>

        {/* Benchmark Section */}
        <section className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 border-b border-slate-800 pb-4">
            <div>
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                📊 Comparative Benchmark & Analytics (Chapter 7)
              </h2>
              <p className="text-xs text-slate-400">Simulate 42 rush-hour EV arrivals across FCFS, SJF, and Hybrid Priority.</p>
            </div>
            <button
              onClick={runBenchmark}
              disabled={benchmarking}
              className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 font-bold text-xs text-white shadow-lg transition"
            >
              {benchmarking ? '⏳ Simulating Benchmark...' : '🚀 Run Full 3-Way Benchmark'}
            </button>
          </div>

          {benchmarkResult && (
            <div className="space-y-6">
              <div className="overflow-x-auto bg-slate-950 rounded-xl border border-slate-800">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-slate-900 text-slate-300 font-sans border-b border-slate-800">
                    <tr>
                      <th className="p-3">Metric</th>
                      <th className="p-3 text-blue-400">FCFS (Baseline)</th>
                      <th className="p-3 text-amber-400">SJF</th>
                      <th className="p-3 text-emerald-400">Hybrid Priority</th>
                      <th className="p-3 text-slate-400 font-sans">Theoretical Insight</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {benchmarkResult.summary_table.map((row, i) => (
                      <tr key={i} className="hover:bg-slate-900/40">
                        <td className="p-3 font-sans text-slate-200">{row.metric}</td>
                        <td className="p-3 text-blue-400 font-bold">{row.FCFS}</td>
                        <td className="p-3 text-amber-400 font-bold">{row.SJF}</td>
                        <td className="p-3 text-emerald-400 font-bold">{row.HYBRID}</td>
                        <td className="p-3 font-sans text-[11px] text-slate-400">{row.best}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {benchmarkResult.plots && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-2">
                  {Object.entries(benchmarkResult.plots).map(([k, b64]) => (
                    <div key={k} className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                      <div className="text-xs font-bold text-slate-300 mb-2 uppercase font-mono">{k}</div>
                      <img src={`data:image/png;base64,${b64}`} alt={k} className="rounded-lg w-full" />
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </section>
      </main>

      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-500 font-mono">
        Intelligent EV Slot Allocation Prototype • Non-preemptive scheduling heuristics
      </footer>
    </div>
  );
}

