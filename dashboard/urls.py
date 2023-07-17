from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='dashboard-home'),
    path('pdax', views.pdax, name='dashboard-pdax'),
    path('getKrakenData', views.getKrakenData, name='getKrakenData'),
    path('bitso', views.bitso, name='dashboard-bitso'),
    path('bitstamp', views.bitstamp, name='dashboard-bitstamp'),
]