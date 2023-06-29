from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dashboard-home'),
    path('bitso', views.bitso, name='dashboard-bitso'),
    path('bitstamp', views.bitstamp, name='dashboard-bitstamp'),
]