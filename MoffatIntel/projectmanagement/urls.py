from django.urls import path, include
from .views import contracts, data, draws, estimates, misc, plans, projects, registration, reports
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', registration.index, name='index'),
    path('change_password/<str:username>/', registration.change_password, name='change_password'),
    path('home/', projects.home, name='home'),
    path('all/', projects.all, name='all'),
    path('new_proj/', projects.new_proj, name='new_proj'),
    path('input_data/', data.input_data, name='input_data'),
    path('todo/', misc.todo, name='todo'),
    path('reports/', reports.reports, name='reports'),
    path('new_contract/', contracts.new_contract, name='new_contract'),
    path('new_contract/<int:project_id>/<int:sub_id>', contracts.new_contract, name='new_contract'),

    path('contract_pdf_view/<int:contract_id>/', contracts.contract_pdf_view, name='contract_pdf_view'),
    path('exhibit_pdf_view/<int:exhibit_id>/', contracts.exhibit_pdf_view, name='exhibit_pdf_view'),
    path('swo_pdf_view/<int:swo_id>/', contracts.swo_pdf_view, name='swo_pdf_view'),
    path('co_pdf_view/<int:co_id>/', contracts.co_pdf_view, name='co_pdf_view'),
    path('po_pdf_view/<int:po_id>/', contracts.po_pdf_view, name='po_pdf_view'),
    path('dco_pdf_view/<int:dco_id>/', contracts.dco_pdf_view, name='dco_pdf_view'),
    path('estimate_pdf_view/<int:estimate_id>', estimates.estimate_pdf_view, name='estimate_pdf_view'),

    path('delete_exhibit/<int:exhibit_id>/', contracts.delete_exhibit, name='delete_exhibit'),
    path('delete_estimate/<int:estimate_id>/', estimates.delete_estimate, name='delete_estimate'),
    path('delete_master/<int:master_id>/', estimates.delete_master, name='delete_master'),
    path('delete_contract/<int:contract_id>/', contracts.delete_contract, name='delete_contract'),
    path('delete_swo/<int:swo_id>/', contracts.delete_swo, name='delete_swo'),
    path('delete_estimate/<int:estimate_id>/', estimates.delete_estimate, name='delete_estimate'),
    path('delete_sub/<int:sub_id>/', data.delete_sub, name='delete_sub'),
    path('delete_proj/<int:project_id>/', projects.delete_proj, name='delete_proj'),
    path('delete_vendor/<int:vendor_id>/', data.delete_vendor, name='delete_vendor'),
    path('delete_change_order/<int:co_id>/', contracts.delete_change_order, name='delete_change_order'),
    path('delete_invoice/<int:project_id>/<int:draw_id>/<int:invoice_id>/', contracts.delete_invoice, name='delete_invoice'),
    path('delete_check/<int:check_id>/', draws.delete_check, name='delete_check'),
    path('delete_plan/<int:project_id>', plans.delete_plan, name='delete_plan'),
    path('delete_deductive_change_order/<int:dco_id>/', contracts.delete_deductive_change_order, name='delete_deductive_change_order'),
    path('delete_purchase_order/<int:po_id>/', contracts.delete_purchase_order, name='delete_purchase_order'),
    path('delete_draw/<int:project_id>/', draws.delete_draw, name='delete_draw'),

    path('all_subs/', data.all_subs, name='all_subs'),
    path('all_vendors/', data.all_vendors, name='all_vendors'),
    path('all_draws/<int:project_id>/', draws.all_draws, name='all_draws'),
    path('all_plans/<int:project_id>', plans.all_plans, name='all_plans'),
    path('all_estimates/<int:project_id>', estimates.all_estimates, name='all_estimates'),

    path('edit_sub/<int:sub_id>/', data.edit_sub, name='edit_sub'),
    path('edit_check/<int:check_id>/', draws.edit_check, name='edit_check'),
    path('edit_vendor/<int:vendor_id>/', data.edit_vendor, name='edit_vendor'),
    path('edit_proj/<int:project_id>/', projects.edit_proj, name='edit_proj'),
    path('edit_estimate/<int:estimate_id>/', estimates.edit_estimate, name='edit_estimate'),

    path('new_draw/<int:project_id>', draws.new_draw, name='new_draw'),
    path('new_check/<int:draw_item_id>', draws.new_check, name='new_check'),
    path('new_change_order/<int:project_id>/<int:sub_id>/', contracts.new_change_order, name='new_change_order'),
    path('new_change_order/', contracts.new_change_order, name='new_change_order'),
    path('new_deductive_change_order/<int:project_id>/<int:sub_id>/', contracts.new_deductive_change_order, name='new_deductive_change_order'),
    path('new_deductive_change_order', contracts.new_deductive_change_order, name='new_deductive_change_order'),
    path('new_purchase_order/<int:project_id>/', contracts.new_purchase_order, name='new_purchase_order'),
    path('new_purchase_order/', contracts.new_purchase_order, name='new_purchase_order'),
    path('new_exhibit/<int:project_id>/<int:sub_id>/', contracts.new_exhibit, name='new_exhibit'),
    path('new_master/<int:project_id>/', estimates.new_master, name='new_master'),

    path('contract_view/<int:project_id>/<int:sub_id>', contracts.contract_view, name='contract_view'),
    path('draw_view/<int:draw_id>/', draws.draw_view, name='draw_view'),
    path('plan_view/<int:project_id>/<int:plan_id>/', plans.plan_view, name='plan_view'),
    path('check_view/<int:check_id>/', draws.check_view, name='check_view'),
    path('lr_view/<int:lr_id>/', contracts.lr_view, name='lr_view'),
    path('project_view/<int:project_id>/', projects.project_view, name='project_view'),
    path('sub_select/<int:project_id>/', contracts.sub_select, name='sub_select'),
    path('change_orders/<int:project_id>/<int:sub_id>/', contracts.change_orders, name='change_orders'),
    path('deductive_change_orders/<int:project_id>/<int:sub_id>/', contracts.deductive_change_orders, name='deductive_change_orders'),
    path('purchase_orders/<int:project_id>/', contracts.purchase_orders, name='purchase_orders'),
    path('upload_plan/<int:project_id>/', plans.upload_plan, name='upload_plan'),

    path('log_out/', registration.log_out, name='logout'),
    path('accounts/', include('django.contrib.auth.urls')),

    #APIs
    path('get_master_format/', misc.get_master_format, name='get_master_format'),
    path('get_exhibits/<str:sub_name>/<int:project_id>', misc.get_exhibits, name='get_exhibits'),
    path('get_exhibit_line_items/<int:exhibit_id>', misc.get_exhibit_line_items, name='get_exhibit_line_items'),
    path('get_sub_data/<str:sub_name>', misc.get_sub_data, name='get_sub_data'),
    path('get_draw_data/<int:draw_id>', misc.get_draw_data, name='get_draw_data'),
    path('get_lr_for_draw_item/<int:draw_item_id>/<str:type>', misc.get_lr_for_draw_item, name='get_lr_for_draw_item'),
    path('get_check_for_draw_item/<int:draw_item_id>', misc.get_check_for_draw_item, name='get_check_for_draw_item'),
]
app_name = "projectmanagement"

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)