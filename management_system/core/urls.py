from django.urls import path
from .views import WorkerListView, export_workers, company_monitor_contractors, contractor_dashboard, worker_dashboard, department_tracking, register
from django.contrib.auth.views import LogoutView
urlpatterns = [
    path('company/dashboard/', WorkerListView.as_view(), name='company_dashboard'),
    path('company/monitor/', company_monitor_contractors, name='company_monitor'),
    path('company/export/', export_workers, name='export_workers'),
    path('contractor/dashboard/', contractor_dashboard, name='contractor_dashboard'),
    path('worker/dashboard/', worker_dashboard, name='worker_dashboard'),
    path('departments/', department_tracking, name='department_tracking'),
    path('register/', register, name='register'),
]