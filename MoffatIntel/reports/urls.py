from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('all/', views.all, name='all'),
    path('create_proj/', views.create_proj, name='create_proj'),
    path('create_draw/<int:project_id>', views.create_draw, name='create_draw'),
    path('all_draws/<int:project_id>/', views.all_draws, name='all_draws'),
    path('all_plans/<int:project_id>', views.all_plans, name='all_plans'),
    path('delete_draw/<int:project_id>/', views.delete_draw, name='delete_draw'),
    path('edit_proj/<int:project_id>/', views.edit_proj, name='edit_proj'),
    path('project_view/<int:project_id>/', views.project_view, name='project_view'),
    path('delete_proj/<int:project_id>/', views.delete_proj, name='delete_proj'),
    path('upload_plan/<int:project_id>/', views.upload_plan, name='upload_plan'),
    path('delete_plan/<int:project_id>', views.delete_plan, name='delete_plan'),
    path('plan_view/<int:project_id>/<int:plan_id>', views.plan_view, name='plan_view'),
    path('log_out/', views.log_out, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]
app_name = "reports"
