# Intelligent EV Charging Slot Allocation System
### Design, Implementation, and Comparative Analysis of Scheduling Algorithms

A working prototype of the intelligent Electric Vehicle (EV) charging slot allocation system as formulated in the project specification.

The system models EV charging at a station with a fixed number of identical charging docks ($M = 4$, 50 kW fast chargers) as an online resource-scheduling problem under non-preemptive constraints. It implements and rigorously benchmarks three scheduling algorithms:
1. **First-Come-First-Served (FCFS)**: Baseline queueing based on arrival time.
2. **Shortest Job First (SJF)**: Prioritizes vehicles requiring the least estimated charging duration.
3. **Hybrid Priority Algorithm**: Proposed multi-factor dynamic algorithm balancing waiting time, charging duration, and urgency level to eliminate starvation while maintaining high throughput.

---

## 🏗 System Architecture

The prototype follows a modular three-tier web architecture:
- **Scheduling Core (Python Standard Library `heapq`)**: Implements binary-heap priority queues for $O(\log n)$ scheduling and dynamic queue re-ranking.
- **Backend API Layer (Django 6 & Django REST Framework)**: Synchronous scheduling within the request-response cycle, REST endpoints, and SQLite storage for zero external setup.
- **Analytics & Benchmarking Engine (Pandas & Matplotlib)**: Computes mean/max waiting time, throughput, slot utilization, and fairness (variance/standard deviation) and plots publication figures.
- **Frontend Dashboard (Interactive Web UI & Standalone React 18)**:
  - **Embedded Web Dashboard**: Accessible directly from Django at `http://127.0.0.1:8000/` with live state polling, real-time bay visualizers, dynamic queue inspector, and Chart.js analytics.
  - **Standalone React Frontend**: Modular React 18 + Tailwind CSS + Vite client in `/frontend`.

---

## 📐 Mathematical Formulation & Scheduling Models

### 1. Request Vector
Each incoming EV request $i$ is defined by:
$$R_i = \langle a_i, c_i, p_i \rangle$$
Where:
- $a_i$: Arrival time (simulation minutes).
- $c_i$: Estimated charging time (minutes), calculated from battery capacity $C_i$ (kWh), current state of charge $\text{SoC}_i$, target state of charge $\text{SoC}_i^*$, and charger power $P = 50\text{ kW}$:
  $$E_i = C_i \times \frac{\text{SoC}_i^* - \text{SoC}_i}{100}$$
  $$c_i = \left(\frac{E_i}{P}\right) \times 60$$
- $p_i$: Urgency/priority level ($1 = \text{Normal}, 2 = \text{High}, 3 = \text{Emergency}$).

### 2. Evaluated Algorithms
- **FCFS Heap Key**:
  $$\text{Key}_{\text{FCFS}}(i) = a_i$$
- **SJF Heap Key**:
  $$\text{Key}_{\text{SJF}}(i) = c_i$$
- **Hybrid Priority Score / Min-Heap Key**:
  At any scheduling instant $t$, waiting time is $W_i(t) = t - a_i$. The min-heap key is:
  $$\text{Key}_{\text{Hybrid}}(i, t) = w_c \cdot c_i - w_w \cdot (t - a_i) - w_p \cdot p_i$$
  *(with $w_c = 0.35, w_w = 0.55, w_p = 12.0$)*. As $W_i(t)$ increases, the key decreases, ensuring long-waiting vehicles bubble up to the front and avoid SJF starvation.

### 3. Evaluation Metrics
- **Mean Waiting Time**: $\bar{W} = \frac{1}{N} \sum_{i=1}^N W_i$
- **Maximum Waiting Time**: $W_{\max} = \max_i(W_i)$
- **Throughput**: $\text{Throughput} = \frac{N}{T}$ (vehicles served per hour)
- **Slot Utilization**: $U = \frac{\sum_{i=1}^N c_i}{M \times T} \times 100\%$
- **Fairness (Standard Deviation)**: $\sigma_W = \sqrt{\frac{1}{N} \sum_{i=1}^N (W_i - \bar{W})^2}$

---

## 🚀 Commands to Run the Prototype

All dependencies (`django`, `djangorestframework`, `django-cors-headers`, `pandas`, `matplotlib`) are already installed in the Python environment.

### 1. Launch the Interactive Web Prototype (Recommended)
To run the full-stack system and open the live dashboard:
```powershell
cd "ev_charging_prototype\backend"
python manage.py runserver
```
Then open your web browser at:
👉 **`http://127.0.0.1:8000/`**

From this dashboard you can:
- Observe 4 charging bays in real-time with charging progress animations.
- Submit new vehicle requests with customizable battery capacity, SoC sliders, and priority tiers.
- Switch the active scheduling algorithm between **FCFS**, **SJF**, and **Hybrid Priority** on the fly and watch the queue dynamically re-order.
- Advance the simulation clock (+5m, +15m, +1h) or enable Auto-Play.
- Inject synthetic morning or evening rush-hour demand spikes.
- Run the full 3-way benchmark simulation and view comparative Chart.js and Matplotlib plots.

---

### 2. Run the Command-Line Simulation & Generate Publication Plots
To run the exact 42-vehicle rush-hour benchmark and generate Matplotlib figures (Figure 7.1 through 7.5):
```powershell
cd "ev_charging_prototype\backend"
python run_simulation.py
```
This produces:
- `backend/output_charts/figure_7_1_avg_wait.png`
- `backend/output_charts/figure_7_2_distribution.png`
- `backend/output_charts/figure_7_3_short_vs_long.png`
- `backend/output_charts/figure_7_4_max_wait_fairness.png`
- `backend/output_charts/figure_7_5_utilization_throughput.png`

---

### 3. Run the Automated Integration Test Suite
To verify all REST endpoints, serializers, models, and scheduling logic:
```powershell
cd "ev_charging_prototype\backend"
python test_prototype.py
```

---

### 4. Optional: Run the Standalone React Frontend
If you wish to run the standalone React client on Vite:
```powershell
cd "ev_charging_prototype\frontend"
npm install
npm run dev
```
Accessible at `http://localhost:3000/` (proxies API requests to Django on `http://127.0.0.1:8000/`).

---

## 📊 Benchmark Summary (Table 7.2 Comparison)

| Metric | FCFS (Baseline) | SJF | Hybrid Priority | Benchmark Finding |
|---|:---:|:---:|:---:|---|
| **Average Waiting Time** | 10.63 min | **10.04 min** | 10.25 min | SJF achieves lowest average wait |
| **Maximum Waiting Time** | **51.20 min** | 65.50 min | **51.80 min** | Hybrid mitigates SJF starvation |
| **Fairness (Std Dev)** | **12.97 min** | 16.41 min | 14.66 min | FCFS & Hybrid share wait more evenly |
| **Short Sessions ($\le 40$m)** | 11.31 min | **7.44 min** | 12.83 min | SJF fast-tracks short charges |
| **Long Sessions ($\ge 90$m)** | **6.73 min** | 13.31 min | **12.43 min** | Hybrid protects long charges from indefinite delay |
| **Slot Utilization** | 60.83% | 60.83% | 60.83% | Comparable across all algorithms |
| **Throughput** | 2.62 v/h | 2.62 v/h | 2.62 v/h | All algorithms process total arrivals |

