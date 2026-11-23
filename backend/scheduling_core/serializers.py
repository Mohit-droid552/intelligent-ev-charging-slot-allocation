from rest_framework import serializers
from .models import ChargingSlot, VehicleRequest, StationConfig, SimulationLog


class StationConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = StationConfig
        fields = '__all__'


class ChargingSlotSerializer(serializers.ModelSerializer):
    current_vehicle_id = serializers.SerializerMethodField()
    remaining_minutes = serializers.SerializerMethodField()
    progress_pct = serializers.SerializerMethodField()

    class Meta:
        model = ChargingSlot
        fields = [
            'id', 'slot_number', 'status', 'current_request', 'current_vehicle_id',
            'session_start_time', 'session_end_time', 'remaining_minutes',
            'progress_pct', 'total_energy_delivered', 'total_sessions_completed'
        ]

    def get_current_vehicle_id(self, obj):
        return obj.current_request.vehicle_id if obj.current_request else None

    def get_remaining_minutes(self, obj):
        config = StationConfig.get_instance()
        if obj.status == 'OCCUPIED' and obj.session_end_time:
            rem = obj.session_end_time - config.sim_time_minutes
            return max(0.0, round(rem, 1))
        return 0.0

    def get_progress_pct(self, obj):
        config = StationConfig.get_instance()
        if obj.status == 'OCCUPIED' and obj.session_start_time is not None and obj.session_end_time:
            total_duration = obj.session_end_time - obj.session_start_time
            if total_duration > 0:
                elapsed = config.sim_time_minutes - obj.session_start_time
                pct = min(100.0, max(0.0, (elapsed / total_duration) * 100.0))
                return round(pct, 1)
        return 0.0


class VehicleRequestSerializer(serializers.ModelSerializer):
    current_wait_time = serializers.SerializerMethodField()
    queue_position = serializers.IntegerField(read_only=True, required=False)
    computed_score = serializers.FloatField(read_only=True, required=False)

    class Meta:
        model = VehicleRequest
        fields = [
            'id', 'vehicle_id', 'battery_capacity_kwh', 'current_soc_pct',
            'target_soc_pct', 'charger_power_kw', 'energy_needed_kwh',
            'charging_time_minutes', 'priority', 'arrival_time', 'status',
            'start_time', 'completion_time', 'wait_time_minutes',
            'assigned_slot', 'algorithm_used', 'created_at',
            'current_wait_time', 'queue_position', 'computed_score'
        ]
        read_only_fields = ['energy_needed_kwh', 'charging_time_minutes', 'wait_time_minutes']

    def get_current_wait_time(self, obj):
        config = StationConfig.get_instance()
        if obj.status == 'PENDING':
            return max(0.0, round(config.sim_time_minutes - obj.arrival_time, 1))
        elif obj.wait_time_minutes is not None:
            return round(obj.wait_time_minutes, 1)
        return 0.0


class SimulationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SimulationLog
        fields = '__all__'

