from django.shortcuts import render
from django.utils import timezone
from django.db import transaction, models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import random
import os

from .models import StationConfig, ChargingSlot, VehicleRequest, SimulationLog
from .serializers import StationConfigSerializer, ChargingSlotSerializer, VehicleRequestSerializer, SimulationLogSerializer
from .algorithms import get_scheduler
from .simulation import generate_rush_hour_requests, run_comparative_simulation
from .analytics import generate_comparative_plots


def ensure_initialized():
    """Ensure station config and 4 charging slots exist."""
    config = StationConfig.get_instance()
    for s_num in range(1, config.total_slots + 1):
        ChargingSlot.objects.get_or_create(slot_number=s_num)
    return config


def process_docking(config: StationConfig):
    """
    Synchronous scheduling core logic:
    Checks for available charging slots and docks the next vehicle according to the active algorithm.
    """
    free_slots = list(ChargingSlot.objects.filter(status='AVAILABLE').order_by('slot_number'))
    if not free_slots:
        return

    pending_qs = VehicleRequest.objects.filter(status='PENDING').order_by('arrival_time', 'id')
    if not pending_qs.exists():
        return

    # Extract pending requests as dicts
    pending_list = [
        {
            'id': req.id,
            'vehicle_id': req.vehicle_id,
            'arrival_time': req.arrival_time,
            'charging_time_minutes': req.charging_time_minutes,
            'energy_needed_kwh': req.energy_needed_kwh,
            'priority': req.priority,
            'battery_capacity_kwh': req.battery_capacity_kwh,
            'current_soc_pct': req.current_soc_pct,
            'target_soc_pct': req.target_soc_pct,
        }
        for req in pending_qs
    ]

    scheduler = get_scheduler(config.active_algorithm)
    ordered_queue = scheduler.get_queue_order(pending_list, config.sim_time_minutes)

    for selected_item in ordered_queue:
        if not free_slots:
            break

        slot = free_slots.pop(0)
        req_obj = VehicleRequest.objects.get(id=selected_item['id'])

        start_time = config.sim_time_minutes
        end_time = start_time + req_obj.charging_time_minutes
        wait_time = max(0.0, start_time - req_obj.arrival_time)

        req_obj.status = 'CHARGING'
        req_obj.start_time = start_time
        req_obj.completion_time = end_time
        req_obj.wait_time_minutes = round(wait_time, 1)
        req_obj.assigned_slot = slot
        req_obj.algorithm_used = config.active_algorithm
        req_obj.save()

        slot.status = 'OCCUPIED'
        slot.current_request = req_obj
        slot.session_start_time = start_time
        slot.session_end_time = end_time
        slot.save()


class StationStatusAPIView(APIView):
    """Returns current live station state, slots, and dynamically ranked queue."""
    def get(self, request):
        config = ensure_initialized()
        slots = ChargingSlot.objects.all().order_by('slot_number')

        pending_qs = VehicleRequest.objects.filter(status='PENDING').order_by('arrival_time', 'id')
        pending_list = [
            {
                'id': req.id,
                'vehicle_id': req.vehicle_id,
                'arrival_time': req.arrival_time,
                'charging_time_minutes': req.charging_time_minutes,
                'energy_needed_kwh': req.energy_needed_kwh,
                'priority': req.priority,
                'battery_capacity_kwh': req.battery_capacity_kwh,
                'current_soc_pct': req.current_soc_pct,
                'target_soc_pct': req.target_soc_pct,
                'created_at': req.created_at.isoformat()
            }
            for req in pending_qs
        ]

        scheduler = get_scheduler(config.active_algorithm)
        ordered_queue = scheduler.get_queue_order(pending_list, config.sim_time_minutes)

        active_charging = VehicleRequest.objects.filter(status='CHARGING').order_by('completion_time')
        completed = VehicleRequest.objects.filter(status='COMPLETED').order_by('-completion_time')[:10]

        # Calculate live session stats
        completed_all = VehicleRequest.objects.filter(status='COMPLETED')
        total_completed = completed_all.count()
        avg_wait = completed_all.aggregate(models.Avg('wait_time_minutes'))['wait_time_minutes__avg'] or 0.0

        return Response({
            'config': StationConfigSerializer(config).data,
            'slots': ChargingSlotSerializer(slots, many=True).data,
            'queue': ordered_queue,
            'queue_count': len(ordered_queue),
            'active_charging': VehicleRequestSerializer(active_charging, many=True).data,
            'recent_completed': VehicleRequestSerializer(completed, many=True).data,
            'metrics': {
                'total_completed': total_completed,
                'avg_wait_time_minutes': round(avg_wait, 1),
                'available_slots': slots.filter(status='AVAILABLE').count(),
                'occupied_slots': slots.filter(status='OCCUPIED').count(),
            }
        })


class VehicleRequestCreateAPIView(APIView):
    """Submit a new vehicle charging request."""
    def post(self, request):
        config = ensure_initialized()
        data = request.data.copy()

        # Generate vehicle ID if not provided
        if not data.get('vehicle_id'):
            count = VehicleRequest.objects.count() + 1
            data['vehicle_id'] = f"EV-{100 + count}"

        data['arrival_time'] = config.sim_time_minutes
        data['status'] = 'PENDING'
        data['algorithm_used'] = config.active_algorithm

        serializer = VehicleRequestSerializer(data=data)
        if serializer.is_valid():
            req_obj = serializer.save()
            # Immediately attempt to assign slot synchronously
            process_docking(config)
            return Response(VehicleRequestSerializer(req_obj).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlgorithmSelectAPIView(APIView):
    """Switch active scheduling algorithm between FCFS, SJF, and HYBRID."""
    def post(self, request):
        config = ensure_initialized()
        algo = request.data.get('algorithm', 'HYBRID').upper()
        if algo not in ['FCFS', 'SJF', 'HYBRID']:
            return Response({'error': 'Invalid algorithm. Choose FCFS, SJF, or HYBRID.'}, status=status.HTTP_400_BAD_REQUEST)

        config.active_algorithm = algo
        config.save()
        return Response({
            'message': f'Active algorithm set to {algo}',
            'active_algorithm': algo
        })


class SimulationTickAPIView(APIView):
    """
    Advances simulation clock by delta_minutes, updates active charging sessions,
    frees completed bays, and schedules pending vehicles synchronously.
    """
    def post(self, request):
        config = ensure_initialized()
        try:
            delta = float(request.data.get('delta_minutes', 5.0))
        except (ValueError, TypeError):
            delta = 5.0

        with transaction.atomic():
            new_sim_time = config.sim_time_minutes + delta
            config.sim_time_minutes = round(new_sim_time, 1)
            config.save()

            # Process slot completions
            slots = ChargingSlot.objects.filter(status='OCCUPIED')
            for slot in slots:
                if slot.session_end_time and slot.session_end_time <= new_sim_time:
                    # Vehicle finished
                    req = slot.current_request
                    if req:
                        req.status = 'COMPLETED'
                        req.completion_time = slot.session_end_time
                        req.save()
                        slot.total_energy_delivered += req.energy_needed_kwh
                        slot.total_sessions_completed += 1

                    slot.status = 'AVAILABLE'
                    slot.current_request = None
                    slot.session_start_time = None
                    slot.session_end_time = None
                    slot.save()

            # Synchronous allocation of newly freed slots
            process_docking(config)

        return Response({
            'message': f'Advanced simulation by {delta} minutes',
            'sim_time_minutes': config.sim_time_minutes
        })


class RushHourBatchAPIView(APIView):
    """Injects a batch of synthetic rush-hour vehicle arrivals."""
    def post(self, request):
        config = ensure_initialized()
        batch_type = request.data.get('batch_type', 'random')
        count = int(request.data.get('count', 6))

        created = []
        rng = random.Random()
        for i in range(count):
            total_reqs = VehicleRequest.objects.count() + 1
            vid = f"EV-{100 + total_reqs}"
            cap = rng.choice([50.0, 60.0, 75.0, 85.0])
            soc_curr = round(rng.uniform(15.0, 45.0), 1)
            soc_targ = round(rng.uniform(80.0, 95.0), 1)
            power = 50.0

            # Priority weighting: 70% 1, 20% 2, 10% 3
            pri = rng.choices([1, 2, 3], weights=[0.7, 0.2, 0.1], k=1)[0]
            if batch_type == 'morning':
                pri = rng.choices([1, 2, 3], weights=[0.6, 0.3, 0.1], k=1)[0]
            elif batch_type == 'emergency':
                pri = 3

            req = VehicleRequest(
                vehicle_id=vid,
                battery_capacity_kwh=cap,
                current_soc_pct=soc_curr,
                target_soc_pct=soc_targ,
                charger_power_kw=power,
                priority=pri,
                arrival_time=config.sim_time_minutes + round(rng.uniform(0.0, 5.0), 1),
                status='PENDING',
                algorithm_used=config.active_algorithm
            )
            req.save()
            created.append(req.vehicle_id)

        process_docking(config)
        return Response({
            'message': f'Injected {len(created)} vehicles into queue',
            'vehicles': created
        })


class ResetStationAPIView(APIView):
    """Resets simulation time, slots, and requests to clean initial state."""
    def post(self, request):
        config = ensure_initialized()
        config.sim_time_minutes = 0.0
        config.save()

        # Free all slots
        ChargingSlot.objects.update(
            status='AVAILABLE',
            current_request=None,
            session_start_time=None,
            session_end_time=None,
            total_energy_delivered=0.0,
            total_sessions_completed=0
        )

        # Clear existing requests
        VehicleRequest.objects.all().delete()

        return Response({'message': 'Station reset successfully to minute 0.0'})


class ComparativeSimulationAPIView(APIView):
    """
    Runs full comparative evaluation comparing FCFS, SJF, and Hybrid Priority
    matching Chapter 7 of the report. Generates Matplotlib figures and returns metrics.
    """
    def post(self, request):
        num_vehicles = int(request.data.get('num_vehicles', 42))
        duration_hours = float(request.data.get('duration_hours', 16.0))
        seed = int(request.data.get('seed', 42))

        comparison = run_comparative_simulation(
            num_vehicles=num_vehicles,
            num_slots=4,
            duration_hours=duration_hours,
            seed=seed
        )

        # Save to SimulationLog model
        for algo_key in ['FCFS', 'SJF', 'HYBRID']:
            res = comparison['algorithms'][algo_key]
            SimulationLog.objects.create(
                algorithm=algo_key,
                num_vehicles=num_vehicles,
                total_sim_hours=duration_hours,
                slots_count=4,
                mean_wait_time=res.get('mean_wait_time', 0.0),
                max_wait_time=res.get('max_wait_time', 0.0),
                throughput_per_hour=res.get('throughput_per_hour', 0.0),
                slot_utilization_pct=res.get('slot_utilization_pct', 0.0),
                fairness_variance=res.get('fairness_variance', 0.0),
                fairness_std_dev=res.get('fairness_std_dev', 0.0),
                short_sessions_avg_wait=res.get('short_sessions_avg_wait', 0.0),
                long_sessions_avg_wait=res.get('long_sessions_avg_wait', 0.0)
            )

        # Generate Matplotlib plots
        plots_b64 = generate_comparative_plots(comparison)
        comparison['plots'] = plots_b64

        return Response(comparison)


def index_view(request):
    """Serve the primary interactive web dashboard."""
    return render(request, 'dashboard.html')
