"""
Scheduling Core for Intelligent EV Charging Slot Allocation.
Implements:
1. First-Come-First-Served (FCFS) - Baseline
2. Shortest Job First (SJF)
3. Hybrid Priority Algorithm (Weighted sum of wait time, charge time, and priority)

All queues use Python's built-in heapq module for binary heap priority queue operations.
"""

import heapq
from typing import List, Dict, Any, Optional


class ScheduledItem:
    """Represents a request inside the scheduling heap."""
    def __init__(self, key: float, seq: int, req_id: int, data: Dict[str, Any]):
        self.key = key
        self.seq = seq
        self.req_id = req_id
        self.data = data

    def __lt__(self, other: 'ScheduledItem') -> bool:
        if self.key != other.key:
            return self.key < other.key
        return self.seq < other.seq


class BaseScheduler:
    """Base class for EV charging slot schedulers."""
    def __init__(self, name: str):
        self.name = name
        self.seq_counter = 0

    def get_queue_order(self, pending_requests: List[Dict[str, Any]], current_time: float) -> List[Dict[str, Any]]:
        """Return the pending requests sorted in the order they will be served."""
        raise NotImplementedError

    def select_next(self, pending_requests: List[Dict[str, Any]], current_time: float) -> Optional[Dict[str, Any]]:
        """Select and return the next vehicle to be assigned to an available slot."""
        ordered = self.get_queue_order(pending_requests, current_time)
        return ordered[0] if ordered else None


class FCFSScheduler(BaseScheduler):
    """
    First-Come-First-Served (FCFS) Scheduler.
    Baseline algorithm: vehicles are placed in queue in the order of their arrival.
    Key = arrival_time.
    """
    def __init__(self):
        super().__init__("FCFS")

    def get_queue_order(self, pending_requests: List[Dict[str, Any]], current_time: float) -> List[Dict[str, Any]]:
        if not pending_requests:
            return []

        heap: List[ScheduledItem] = []
        for req in pending_requests:
            self.seq_counter += 1
            # Key is arrival_time
            arrival = float(req.get('arrival_time', 0.0))
            item = ScheduledItem(
                key=arrival,
                seq=self.seq_counter,
                req_id=req.get('id', self.seq_counter),
                data=dict(req)
            )
            heapq.heappush(heap, item)

        ordered = []
        rank = 1
        while heap:
            item = heapq.heappop(heap)
            req_data = item.data
            req_data['queue_position'] = rank
            req_data['computed_score'] = round(item.key, 2)
            req_data['current_wait_time'] = max(0.0, round(current_time - float(req_data.get('arrival_time', 0.0)), 2))
            ordered.append(req_data)
            rank += 1

        return ordered


class SJFScheduler(BaseScheduler):
    """
    Shortest Job First (SJF) Scheduler.
    Prioritizes vehicles requiring the shortest estimated charging duration.
    Key = estimated_charging_time.
    """
    def __init__(self):
        super().__init__("SJF")

    def get_queue_order(self, pending_requests: List[Dict[str, Any]], current_time: float) -> List[Dict[str, Any]]:
        if not pending_requests:
            return []

        heap: List[ScheduledItem] = []
        for req in pending_requests:
            self.seq_counter += 1
            # Key is charging duration
            charge_time = float(req.get('charging_time_minutes', 0.0))
            item = ScheduledItem(
                key=charge_time,
                seq=self.seq_counter,
                req_id=req.get('id', self.seq_counter),
                data=dict(req)
            )
            heapq.heappush(heap, item)

        ordered = []
        rank = 1
        while heap:
            item = heapq.heappop(heap)
            req_data = item.data
            req_data['queue_position'] = rank
            req_data['computed_score'] = round(item.key, 2)
            req_data['current_wait_time'] = max(0.0, round(current_time - float(req_data.get('arrival_time', 0.0)), 2))
            ordered.append(req_data)
            rank += 1

        return ordered


class HybridPriorityScheduler(BaseScheduler):
    """
    Hybrid Priority Scheduling Algorithm.
    Balances:
    1. Waiting time of the request: W_i(t) = t - a_i (reduces starvation)
    2. Expected charging duration: c_i (promotes throughput)
    3. Urgency / priority level: p_i (1=Normal, 2=High, 3=Emergency)

    Key for min-heap:
      key = (w_c * c_i) - (w_w * W_i) - (w_p * p_i)
    Lower key is popped first.
    As a vehicle waits longer, (w_w * W_i) increases, drastically lowering its key
    so that long-waiting jobs will overtake newly arrived short jobs, mitigating starvation.
    """
    def __init__(self, weight_charge: float = 0.35, weight_wait: float = 0.55, weight_priority: float = 12.0):
        super().__init__("Hybrid Priority")
        self.w_c = weight_charge
        self.w_w = weight_wait
        self.w_p = weight_priority

    def calculate_key(self, charging_time: float, wait_time: float, priority: float) -> float:
        # Min-heap key: smaller key gets served earlier
        # Higher wait_time -> smaller key
        # Higher priority -> smaller key
        # Lower charging_time -> smaller key
        return (self.w_c * charging_time) - (self.w_w * wait_time) - (self.w_p * priority)

    def get_queue_order(self, pending_requests: List[Dict[str, Any]], current_time: float) -> List[Dict[str, Any]]:
        if not pending_requests:
            return []

        heap: List[ScheduledItem] = []
        for req in pending_requests:
            self.seq_counter += 1
            charge_time = float(req.get('charging_time_minutes', 0.0))
            arrival = float(req.get('arrival_time', 0.0))
            wait_time = max(0.0, current_time - arrival)
            priority = float(req.get('priority', 1))

            key = self.calculate_key(charge_time, wait_time, priority)

            item = ScheduledItem(
                key=key,
                seq=self.seq_counter,
                req_id=req.get('id', self.seq_counter),
                data=dict(req)
            )
            heapq.heappush(heap, item)

        ordered = []
        rank = 1
        while heap:
            item = heapq.heappop(heap)
            req_data = item.data
            req_data['queue_position'] = rank
            # Normalized display score: higher is higher priority
            req_data['computed_score'] = round(-item.key, 2)
            req_data['current_wait_time'] = max(0.0, round(current_time - float(req_data.get('arrival_time', 0.0)), 2))
            ordered.append(req_data)
            rank += 1

        return ordered


def get_scheduler(algorithm_name: str) -> BaseScheduler:
    """Factory to retrieve scheduler by name."""
    algo = (algorithm_name or 'HYBRID').upper()
    if 'FCFS' in algo:
        return FCFSScheduler()
    elif 'SJF' in algo:
        return SJFScheduler()
    else:
        return HybridPriorityScheduler()

