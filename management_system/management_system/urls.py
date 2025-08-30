from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core import views
from django.contrib.auth.views import LoginView, LogoutView

urlpatterns = [
    path('', views.dashboard_redirect, name='home'),  # New root path
    path('admin/', admin.site.urls),
    path('login/', LoginView.as_view(template_name='core/login.html'), name='login'),
    path('logout/', LogoutView.as_view(template_name='core/logout.html', next_page='/login/'), name='logout'),
    path('dashboard/', views.dashboard_redirect, name='dashboard'),
    path('', include('core.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)