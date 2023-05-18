from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

app_name = "reports"
urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('all/', views.all, name='all'),
    path('create_proj/', views.create_proj, name='create_proj'),
    path('<int:project_id>/edit_proj/', views.edit_proj, name='edit_proj'),
    path('<int:project_id>/project_view/', views.project_view, name='project_view'),
    path('delete_proj/<int:project_id>/', views.delete_proj, name='delete_proj'),
    path('log_out/', views.log_out, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]
