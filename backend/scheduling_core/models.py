from django.db import models
from django.utils import timezone


class StationConfig(models.Model):
    """Configuration and global state of the EV Charging Station."""
    ALGORITHM_CHOICES = [
        ('FCFS', 'First-Come-First-Served (FCFS)'),
        ('SJF', 'Shortest Job First (SJF)'),
        ('HYBRID', 'Hybrid Priority Scheduling'),
    ]

    total_slots = models.IntegerField(default=4)
    charger_power_kw = models.FloatField(default=50.0)  # Default 50 kW Fast Charger
    active_algorithm = models.CharField(max_length=20, choices=ALGORITHM_CHOICES, default='HYBRID')
    sim_time_minutes = models.FloatField(default=0.0)
    is_simulating = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get_instance(cls):
        obj, _ = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return f"Station (Slots: {self.total_slots}, Algo: {self.active_algorithm}, SimTime: {self.sim_time_minutes:.1f}m)"


class ChargingSlot(models.Model):
    """Represents a physical charging dock / bay at the station."""
    STATUS_CHOICES = [
        ('AVAILABLE', 'Available'),
        ('OCCUPIED', 'Occupied / Charging'),
        ('MAINTENANCE', 'Under Maintenance'),
    ]

    slot_number = models.IntegerField(unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='AVAILABLE')
    current_request = models.OneToOneField(
        'VehicleRequest',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='occupying_slot'
    )
    session_start_time = models.FloatField(null=True, blank=True)
    session_end_time = models.FloatField(null=True, blank=True)
    total_energy_delivered = models.FloatField(default=0.0)
    total_sessions_completed = models.IntegerField(default=0)

    class Meta:
        ordering = ['slot_number']

    def __str__(self):
        return f"Slot #{self.slot_number} [{self.status}]"


class VehicleRequest(models.Model):
    """Represents an incoming EV charging request."""
    PRIORITY_CHOICES = [
        (1, 'Normal (1)'),
        (2, 'High (2)'),
        (3, 'Emergency / VIP (3)'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'In Queue'),
        ('CHARGING', 'Charging'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    vehicle_id = models.CharField(max_length=32)
    battery_capacity_kwh = models.FloatField(default=60.0)
    current_soc_pct = models.FloatField(default=20.0)   # State of Charge %
    target_soc_pct = models.FloatField(default=80.0)
    charger_power_kw = models.FloatField(default=50.0)
    energy_needed_kwh = models.FloatField(default=36.0)
    charging_time_minutes = models.FloatField(default=43.2)
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=1)

    arrival_time = models.FloatField(default=0.0)  # Simulation time in minutes
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    start_time = models.FloatField(null=True, blank=True)
    completion_time = models.FloatField(null=True, blank=True)
    wait_time_minutes = models.FloatField(null=True, blank=True)
    assigned_slot = models.ForeignKey(
        ChargingSlot,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='assigned_requests'
    )
    algorithm_used = models.CharField(max_length=20, default='HYBRID')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['arrival_time', 'id']

    def save(self, *args, **kwargs):
        # Calculate energy needed & charging duration if not specified
        if self.target_soc_pct > self.current_soc_pct and self.battery_capacity_kwh > 0:
            soc_delta = (self.target_soc_pct - self.current_soc_pct) / 100.0
            self.energy_needed_kwh = round(self.battery_capacity_kwh * soc_delta, 2)
            power = self.charger_power_kw if self.charger_power_kw > 0 else 50.0
            self.charging_time_minutes = round((self.energy_needed_kwh / power) * 60.0, 1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vehicle_id} ({self.charging_time_minutes} min, Pri:{self.priority}, Status:{self.status})"


class SimulationLog(models.Model):
    """Stores comparative simulation results between FCFS, SJF, and Hybrid."""
    run_timestamp = models.DateTimeField(default=timezone.now)
    algorithm = models.CharField(max_length=20)
    num_vehicles = models.IntegerField()
    total_sim_hours = models.FloatField(default=16.0)
    slots_count = models.IntegerField(default=4)

    mean_wait_time = models.FloatField()
    max_wait_time = models.FloatField()
    throughput_per_hour = models.FloatField()
    slot_utilization_pct = models.FloatField()
    fairness_variance = models.FloatField()
    fairness_std_dev = models.FloatField()
    short_sessions_avg_wait = models.FloatField()
    long_sessions_avg_wait = models.FloatField()

    class Meta:
        ordering = ['-run_timestamp', 'algorithm']
