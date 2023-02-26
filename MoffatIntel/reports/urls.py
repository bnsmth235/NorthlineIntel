from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = "reports"
urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('log_out/', views.log_out, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]
