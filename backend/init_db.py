"""
Initialize station database with 4 slots and a few sample vehicles.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ev_system.settings')
django.setup()

from scheduling_core.models import StationConfig, ChargingSlot, VehicleRequest
from scheduling_core.views import ensure_initialized, process_docking

def main():
    config = ensure_initialized()
    print(f"Station initialized: {config.total_slots} slots, algorithm: {config.active_algorithm}")

    # Reset any existing test records
    ChargingSlot.objects.update(status='AVAILABLE', current_request=None, session_start_time=None, session_end_time=None)
    VehicleRequest.objects.all().delete()

    # Pre-populate with initial demonstration vehicles
    sample_vehicles = [
        {'vid': 'EV-101', 'cap': 60.0, 'curr': 20.0, 'targ': 80.0, 'pri': 1, 'arr': 0.0},
        {'vid': 'EV-102', 'cap': 40.0, 'curr': 40.0, 'targ': 80.0, 'pri': 2, 'arr': 2.0},
        {'vid': 'EV-103', 'cap': 75.0, 'curr': 15.0, 'targ': 85.0, 'pri': 1, 'arr': 5.0},
        {'vid': 'EV-104', 'cap': 50.0, 'curr': 30.0, 'targ': 70.0, 'pri': 3, 'arr': 8.0},
        {'vid': 'EV-105', 'cap': 100.0, 'curr': 10.0, 'targ': 90.0, 'pri': 1, 'arr': 12.0},
        {'vid': 'EV-106', 'cap': 60.0, 'curr': 35.0, 'targ': 80.0, 'pri': 2, 'arr': 15.0},
        {'vid': 'EV-107', 'cap': 40.0, 'curr': 50.0, 'targ': 80.0, 'pri': 1, 'arr': 18.0},
    ]

    for v in sample_vehicles:
        req = VehicleRequest(
            vehicle_id=v['vid'],
            battery_capacity_kwh=v['cap'],
            current_soc_pct=v['curr'],
            target_soc_pct=v['targ'],
            priority=v['pri'],
            arrival_time=v['arr'],
            status='PENDING',
            algorithm_used=config.active_algorithm
        )
        req.save()

    print(f"Created {len(sample_vehicles)} sample vehicle requests.")
    process_docking(config)

    occupied = ChargingSlot.objects.filter(status='OCCUPIED').count()
    pending = VehicleRequest.objects.filter(status='PENDING').count()
    print(f"Slots occupied: {occupied}/4, Pending in queue: {pending}")

if __name__ == '__main__':
    main()

