"""
Analytics and Visualization Module.
Uses Pandas to process metrics and Matplotlib to generate the comparative figures
described in Chapter 7 of the project report:
- Figure 7.1: Average Waiting Time
- Figure 7.2: Distribution of Waiting Times (Cumulative %)
- Figure 7.3: Short vs. Long Charging Sessions Waiting Time
- Figure 7.4: Maximum Waiting Time & Fairness (Standard Deviation)
- Figure 7.5: Slot Utilization and Charging Throughput
"""

import io
import base64
import os
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')  # Headless backend for web server
import matplotlib.pyplot as plt


def generate_comparative_plots(comparison_data: Dict[str, Any], output_dir: str = None) -> Dict[str, str]:
    """
    Generates Matplotlib charts for FCFS, SJF, and Hybrid Priority,
    matching the figures in the report.
    Returns a dict of chart_name -> base64_png_string.
    If output_dir is given, also saves them as PNG files.
    """
    algos = ['FCFS', 'SJF', 'HYBRID']
    display_names = ['FCFS', 'SJF', 'Hybrid']
    colors = ['#3b82f6', '#f97316', '#10b981']  # Blue, Orange, Emerald

    results = comparison_data['algorithms']
    encoded_charts = {}

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # Helper to convert current plt to base64
    def _save_and_encode(filename: str = None) -> str:
        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
        if output_dir and filename:
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(buf.getvalue())
        buf.seek(0)
        b64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return b64

    # -------------------------------------------------------------
    # Figure 7.1: Average Waiting Time (minutes)
    # -------------------------------------------------------------
    plt.figure(figsize=(6, 4.5))
    avg_waits = [results[a].get('mean_wait_time', 0.0) for a in algos]
    bars = plt.bar(display_names, avg_waits, color=colors, width=0.55, edgecolor='#1e293b', linewidth=1)
    plt.title('Average Waiting Time of the Three Algorithms', fontsize=12, fontweight='bold', pad=12)
    plt.ylabel('Average waiting time (minutes)', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    for bar in bars:
        h = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, h + 1.0, f'{h:.1f}', ha='center', va='bottom', fontsize=10, fontweight='semibold')
    plt.ylim(0, max(avg_waits) * 1.25)
    encoded_charts['fig7_1_avg_wait'] = _save_and_encode('figure_7_1_avg_wait.png')

    # -------------------------------------------------------------
    # Figure 7.2: Distribution of Waiting Times (CDF)
    # -------------------------------------------------------------
    plt.figure(figsize=(7, 4.5))
    max_x = 250
    x_grid = np.linspace(0, max_x, 100)
    for a, name, col in zip(algos, display_names, colors):
        w_list = np.sort(results[a].get('wait_times_list', []))
        if len(w_list) > 0:
            cdf_y = np.searchsorted(w_list, x_grid, side='right') / len(w_list) * 100.0
            plt.plot(x_grid, cdf_y, label=name, color=col, linewidth=2.2)

    plt.title('Distribution of Waiting Times', fontsize=12, fontweight='bold', pad=12)
    plt.xlabel('Waiting time (minutes)', fontsize=10)
    plt.ylabel('Vehicles served within this wait (%)', fontsize=10)
    plt.xlim(0, max_x)
    plt.ylim(0, 105)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.legend(frameon=True, loc='lower right')
    encoded_charts['fig7_2_distribution'] = _save_and_encode('figure_7_2_distribution.png')

    # -------------------------------------------------------------
    # Figure 7.3: Short vs. Long Charging Sessions Waiting Time
    # -------------------------------------------------------------
    plt.figure(figsize=(7, 4.5))
    x = np.arange(2)
    width = 0.25
    short_waits = [results[a].get('short_sessions_avg_wait', 0.0) for a in algos]
    long_waits = [results[a].get('long_sessions_avg_wait', 0.0) for a in algos]

    for idx, (a, name, col) in enumerate(zip(algos, display_names, colors)):
        vals = [short_waits[idx], long_waits[idx]]
        rects = plt.bar(x + (idx - 1) * width, vals, width, label=name, color=col, edgecolor='#1e293b', linewidth=0.8)
        for r in rects:
            h = r.get_height()
            plt.text(r.get_x() + r.get_width() / 2.0, h + 1.5, f'{h:.1f}', ha='center', va='bottom', fontsize=9)

    plt.xticks(x, ['Short sessions (<= 40 min)', 'Long sessions (>= 90 min)'], fontsize=10)
    plt.title('Who Waits? Short vs Long Charging Sessions', fontsize=12, fontweight='bold', pad=12)
    plt.ylabel('Average waiting time (minutes)', fontsize=10)
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    plt.ylim(0, max(max(short_waits + long_waits) * 1.25, 20))
    plt.legend(frameon=True)
    encoded_charts['fig7_3_short_vs_long'] = _save_and_encode('figure_7_3_short_vs_long.png')

    # -------------------------------------------------------------
    # Figure 7.4: Maximum Waiting Time & Fairness Spread (Std Dev)
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    max_waits = [results[a].get('max_wait_time', 0.0) for a in algos]
    b1 = ax1.bar(display_names, max_waits, color=colors, width=0.55, edgecolor='#1e293b', linewidth=1)
    ax1.set_title('Maximum Waiting Time', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Minutes', fontsize=9)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    for b in b1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2.0, h + 2.0, f'{h:.1f}', ha='center', va='bottom', fontsize=9)
    ax1.set_ylim(0, max(max_waits) * 1.25)

    std_waits = [results[a].get('fairness_std_dev', 0.0) for a in algos]
    b2 = ax2.bar(display_names, std_waits, color=colors, width=0.55, edgecolor='#1e293b', linewidth=1)
    ax2.set_title('Spread of Waiting Time (Fairness)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Standard deviation (minutes)', fontsize=9)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    for b in b2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2.0, h + 0.8, f'{h:.1f}', ha='center', va='bottom', fontsize=9)
    ax2.set_ylim(0, max(std_waits) * 1.25)

    encoded_charts['fig7_4_max_wait_fairness'] = _save_and_encode('figure_7_4_max_wait_fairness.png')

    # -------------------------------------------------------------
    # Figure 7.5: Slot Utilization and Throughput
    # -------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9, 4))
    utils = [results[a].get('slot_utilization_pct', 0.0) for a in algos]
    b1 = ax1.bar(display_names, utils, color=colors, width=0.55, edgecolor='#1e293b', linewidth=1)
    ax1.set_title('Slot Utilization', fontsize=11, fontweight='bold')
    ax1.set_ylabel('Utilization (%)', fontsize=9)
    ax1.grid(axis='y', linestyle='--', alpha=0.5)
    for b in b1:
        h = b.get_height()
        ax1.text(b.get_x() + b.get_width() / 2.0, h + 1.0, f'{h:.1f}%', ha='center', va='bottom', fontsize=9)
    ax1.set_ylim(0, 100)

    throughputs = [results[a].get('throughput_per_hour', 0.0) for a in algos]
    b2 = ax2.bar(display_names, throughputs, color=colors, width=0.55, edgecolor='#1e293b', linewidth=1)
    ax2.set_title('Throughput', fontsize=11, fontweight='bold')
    ax2.set_ylabel('Vehicles served per hour', fontsize=9)
    ax2.grid(axis='y', linestyle='--', alpha=0.5)
    for b in b2:
        h = b.get_height()
        ax2.text(b.get_x() + b.get_width() / 2.0, h + 0.05, f'{h:.2f}', ha='center', va='bottom', fontsize=9)
    ax2.set_ylim(0, max(throughputs) * 1.3)

    encoded_charts['fig7_5_utilization_throughput'] = _save_and_encode('figure_7_5_utilization_throughput.png')

    return encoded_charts

