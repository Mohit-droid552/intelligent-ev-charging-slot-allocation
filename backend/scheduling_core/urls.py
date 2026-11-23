from django.urls import path
from .views import (
    StationStatusAPIView,
    VehicleRequestCreateAPIView,
    AlgorithmSelectAPIView,
    SimulationTickAPIView,
    RushHourBatchAPIView,
    ResetStationAPIView,
    ComparativeSimulationAPIView,
    index_view
)

urlpatterns = [
    path('', index_view, name='dashboard'),
    path('api/status/', StationStatusAPIView.as_view(), name='station-status'),
    path('api/requests/', VehicleRequestCreateAPIView.as_view(), name='vehicle-request-create'),
    path('api/algorithm/', AlgorithmSelectAPIView.as_view(), name='algorithm-select'),
    path('api/tick/', SimulationTickAPIView.as_view(), name='simulation-tick'),
    path('api/rush-hour/', RushHourBatchAPIView.as_view(), name='rush-hour-batch'),
    path('api/reset/', ResetStationAPIView.as_view(), name='reset-station'),
    path('api/simulate/', ComparativeSimulationAPIView.as_view(), name='comparative-simulation'),
]

