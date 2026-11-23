"""
Standalone Simulation & Evaluation Runner for Intelligent EV Charging Slot Allocation.
Executes the simulation as described in Chapter 5 & 7 of the project:
- 42 synthetic vehicles generated with rush-hour arrival distribution
- 4 identical charging slots (50 kW) over a 16-hour operating window
- Evaluates FCFS, SJF, and Hybrid Priority algorithms on identical arrivals
- Computes metrics using Pandas and saves Matplotlib publication charts
"""

import os
import sys
import pandas as pd

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scheduling_core.simulation import run_comparative_simulation
from scheduling_core.analytics import generate_comparative_plots


def main():
    print("=" * 80)
    print(" INTELLIGENT EV CHARGING SLOT ALLOCATION - SCHEDULING BENCHMARK")
    print("=" * 80)
    print("Configuring Simulation:")
    print(" - Total Charging Docks (Slots): 4")
    print(" - Operating Duration: 16.0 hours (960 minutes)")
    print(" - Vehicle Arrival Count: 42 requests (rush hour pattern: morning & evening)")
    print(" - Algorithms Evaluated: FCFS (Baseline), SJF, Hybrid Priority")
    print("-" * 80)

    print("Running simulation engine across all 3 algorithms on identical arrival streams...")
    results = run_comparative_simulation(num_vehicles=42, num_slots=4, duration_hours=16.0, seed=42)

    algos = results['algorithms']
    print("\nSimulation completed successfully!")
    print("\n" + "=" * 80)
    print(" COMPARATIVE RESULTS SUMMARY (Table 7.2 equivalent)")
    print("=" * 80)

    summary_df = pd.DataFrame(results['summary_table'])
    print(summary_df.to_string(index=False))

    print("\n" + "=" * 80)
    print(" DETAILED ALGORITHM BREAKDOWN")
    print("=" * 80)
    for name, data in algos.items():
        print(f"\n--- {data['algorithm']} ---")
        print(f"Total Vehicles Served:        {data['total_served']}")
        print(f"Mean Waiting Time:            {data['mean_wait_time']} minutes")
        print(f"Maximum Waiting Time:         {data['max_wait_time']} minutes")
        print(f"Fairness (Standard Dev):      {data['fairness_std_dev']} minutes (Variance: {data['fairness_variance']})")
        print(f"Short Sessions Wait (<=40m):  {data['short_sessions_avg_wait']} minutes")
        print(f"Long Sessions Wait (>=90m):   {data['long_sessions_avg_wait']} minutes")
        print(f"Slot Utilization:             {data['slot_utilization_pct']}%")
        print(f"Charging Throughput:          {data['throughput_per_hour']} vehicles/hour")

    # Generate and save Matplotlib charts
    charts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output_charts")
    print(f"\nGenerating and saving Matplotlib publication figures to: {charts_dir}")
    generate_comparative_plots(results, output_dir=charts_dir)

    print(f"Charts saved:")
    print(f"  [1] {os.path.join(charts_dir, 'figure_7_1_avg_wait.png')}")
    print(f"  [2] {os.path.join(charts_dir, 'figure_7_2_distribution.png')}")
    print(f"  [3] {os.path.join(charts_dir, 'figure_7_3_short_vs_long.png')}")
    print(f"  [4] {os.path.join(charts_dir, 'figure_7_4_max_wait_fairness.png')}")
    print(f"  [5] {os.path.join(charts_dir, 'figure_7_5_utilization_throughput.png')}")

    print("\n" + "=" * 80)
    print(" KEY FINDINGS:")
    print(" 1. SJF achieves the lowest average waiting time, prioritizing short charges.")
    print(" 2. FCFS eliminates starvation but suffers from the convoy effect behind long charges.")
    print(" 3. The Hybrid Priority algorithm balances the two: it mitigates starvation of long")
    print("    charges through wait-time aging while preserving high throughput.")
    print("=" * 80)


if __name__ == "__main__":
    main()

