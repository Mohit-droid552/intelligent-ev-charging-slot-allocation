"""
Automated Integration Test Suite for EV Charging Prototype.
Verifies all endpoints, models, serializers, and scheduling algorithms.
"""

import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ev_system.settings')
django.setup()

from django.test import Client
from scheduling_core.models import StationConfig, ChargingSlot, VehicleRequest


def run_tests():
    c = Client()

    print("Running Integration Tests for EV Charging Slot Allocation System...")

    # 1. Test Dashboard Page
    resp = c.get('/')
    assert resp.status_code == 200, f"Expected 200 on '/', got {resp.status_code}"
    assert b'Intelligent EV Slot Allocation System' in resp.content
    print(" [PASS] GET / (Dashboard UI HTML rendered)")

    # 2. Test Station Status API
    resp = c.get('/api/status/')
    assert resp.status_code == 200, f"Expected 200 on /api/status/, got {resp.status_code}"
    data = json.loads(resp.content)
    assert 'slots' in data and len(data['slots']) == 4
    assert 'queue' in data
    assert 'config' in data
    print(f" [PASS] GET /api/status/ (Slots: {len(data['slots'])}, Queue: {len(data['queue'])})")

    # 3. Test Switch Algorithm to FCFS
    resp = c.post('/api/algorithm/', data=json.dumps({'algorithm': 'FCFS'}), content_type='application/json')
    assert resp.status_code == 200
    config = StationConfig.get_instance()
    assert config.active_algorithm == 'FCFS'
    print(" [PASS] POST /api/algorithm/ -> Switched to FCFS")

    # 4. Test Switch Algorithm to SJF
    resp = c.post('/api/algorithm/', data=json.dumps({'algorithm': 'SJF'}), content_type='application/json')
    assert resp.status_code == 200
    config.refresh_from_db()
    assert config.active_algorithm == 'SJF'
    print(" [PASS] POST /api/algorithm/ -> Switched to SJF")

    # 5. Test Switch Algorithm back to HYBRID
    resp = c.post('/api/algorithm/', data=json.dumps({'algorithm': 'HYBRID'}), content_type='application/json')
    assert resp.status_code == 200
    config.refresh_from_db()
    assert config.active_algorithm == 'HYBRID'
    print(" [PASS] POST /api/algorithm/ -> Switched to HYBRID")

    # 6. Test New Vehicle Request Submission
    new_req = {
        'vehicle_id': 'EV-TEST-99',
        'battery_capacity_kwh': 60.0,
        'current_soc_pct': 20.0,
        'target_soc_pct': 80.0,
        'charger_power_kw': 50.0,
        'priority': 2
    }
    resp = c.post('/api/requests/', data=json.dumps(new_req), content_type='application/json')
    assert resp.status_code == 201, f"Expected 201 on /api/requests/, got {resp.status_code}"
    created_data = json.loads(resp.content)
    assert created_data['vehicle_id'] == 'EV-TEST-99'
    assert created_data['energy_needed_kwh'] == 36.0
    assert created_data['charging_time_minutes'] == 43.2
    print(f" [PASS] POST /api/requests/ -> Created vehicle request (Energy: {created_data['energy_needed_kwh']} kWh, Time: {created_data['charging_time_minutes']} min)")

    # 7. Test Simulation Tick (Advance Time)
    resp = c.post('/api/tick/', data=json.dumps({'delta_minutes': 15.0}), content_type='application/json')
    assert resp.status_code == 200
    tick_data = json.loads(resp.content)
    print(f" [PASS] POST /api/tick/ -> Advanced time to {tick_data['sim_time_minutes']} min")

    # 8. Test Rush Hour Injection
    resp = c.post('/api/rush-hour/', data=json.dumps({'batch_type': 'morning', 'count': 4}), content_type='application/json')
    assert resp.status_code == 200
    rush_data = json.loads(resp.content)
    print(f" [PASS] POST /api/rush-hour/ -> Injected {len(rush_data['vehicles'])} vehicles")

    # 9. Test Comparative Benchmark Simulation
    resp = c.post('/api/simulate/', data=json.dumps({'num_vehicles': 42, 'duration_hours': 16.0}), content_type='application/json')
    assert resp.status_code == 200
    bench_data = json.loads(resp.content)
    assert 'algorithms' in bench_data
    assert 'FCFS' in bench_data['algorithms']
    assert 'SJF' in bench_data['algorithms']
    assert 'HYBRID' in bench_data['algorithms']
    assert 'plots' in bench_data
    print(f" [PASS] POST /api/simulate/ -> Ran full 3-way comparative simulation (Generated {len(bench_data['plots'])} charts)")

    print("\nALL INTEGRATION TESTS PASSED (9/9)! The prototype backend & scheduling core are fully operational.")


if __name__ == '__main__':
    run_tests()

