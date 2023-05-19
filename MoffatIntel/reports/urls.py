from django.urls import path, include
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('home/', views.home, name='home'),
    path('all/', views.all, name='all'),
    path('new_proj/', views.new_proj, name='new_proj'),
    path('input_data/', views.input_data, name='input_data'),
    path('all_subs/', views.all_subs, name='all_subs'),
    path('edit_sub/<int:sub_id>/',views.edit_sub, name='edit_sub'),
    path('delete_sub/<int:sub_id>/', views.delete_sub, name='delete_sub'),
    path('new_draw/<int:project_id>', views.new_draw, name='new_draw'),
    path('new_invoice/<int:project_id>/<int:draw_id>/', views.new_invoice, name='new_invoice'),
    path('all_draws/<int:project_id>/', views.all_draws, name='all_draws'),
    path('all_plans/<int:project_id>', views.all_plans, name='all_plans'),
    path('delete_draw/<int:project_id>/', views.delete_draw, name='delete_draw'),
    path('edit_proj/<int:project_id>/', views.edit_proj, name='edit_proj'),
    path('project_view/<int:project_id>/', views.project_view, name='project_view'),
    path('delete_proj/<int:project_id>/', views.delete_proj, name='delete_proj'),
    path('upload_plan/<int:project_id>/', views.upload_plan, name='upload_plan'),
    path('delete_plan/<int:project_id>', views.delete_plan, name='delete_plan'),
    path('invoice_view/<int:project_id>/<int:draw_id>/<int:invoice_id>/', views.invoice_view, name='invoice_view'),
    path('delete_invoice/<int:project_id>/<int:draw_id>/<int:invoice_id>/', views.delete_invoice, name='delete_invoice'),
    path('plan_view/<int:project_id>/<int:plan_id>/', views.plan_view, name='plan_view'),
    path('draw_view/<int:project_id>/<int:draw_id>/', views.draw_view, name='draw_view'),
    path('log_out/', views.log_out, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),
]
app_name = "reports"
