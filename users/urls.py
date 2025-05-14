from django.urls import path
from . import views

urlpatterns = [
    path('scan/', views.scan_fingerprint, name='scan_fingerprint'),
]