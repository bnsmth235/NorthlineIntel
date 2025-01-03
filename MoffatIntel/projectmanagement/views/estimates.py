import base64
import json
import os
import time
import re
import PyPDF2
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime

from ..models import Project, Estimate, Subcontractor, ExhibitLineItem, Group, Subgroup, Vendor, \
    EstimateLineItem, MasterEstimate, MasterEstimateLineItem, csi_data
from ..pdf_create.create_estimate import create_estimate


@login_required(login_url='projectmanagement:login')
def all_estimates(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    masters = MasterEstimate.objects.filter(project_id=project)
    subs = Subcontractor.objects.order_by('name')
    vendors = Vendor.objects.order_by('name')
    estimates = Estimate.objects.filter(master_estimate_id__in=masters)

    divisions = {}
    for division_code, division_info in csi_data.items():
        if len(division_code) == 2:  # Check if it's a division code
            divisions[division_code] = division_info['name']

    context = {
        'project': project,
        'estimates': estimates,
        'masters': masters,
        'subs': subs,
        'vendors': vendors,
        'divisions': divisions,
    }

    if request.method == 'POST':
        division = request.POST.get('division')
        sub_id = request.POST.get('sub')
        total = request.POST.get('total')

        sub = None
        try:
            sub = get_object_or_404(Subcontractor, pk=sub_id)
        except:
            sub = get_object_or_404(Vendor, pk=sub_id)

        master = get_object_or_404(MasterEstimate, pk=request.POST.get('master'))

        estimate = Estimate()
        estimate.master_estimate_id= master
        estimate.name = f"{project.name} {sub.name} {master.csi} Estimate"
        estimate.date = datetime.now()
        estimate.csi = master.csi
        try:
            estimate.sub_id = sub
        except:
            estimate.vendor_id = sub

        try:
            estimate.total = float(total)
        except:
            estimate.total = 0.0
        estimate.save()

        line_items = MasterEstimateLineItem.objects.filter(estimate_id=master)

        for line_item in line_items:
            copy = EstimateLineItem()
            copy.estimate_id = estimate
            copy.sub_id = line_item.sub_id
            copy.vendor_id = line_item.vendor_id
            copy.group_id = line_item.group_id
            copy.subgroup_id = line_item.subgroup_id
            copy.scope = line_item.scope
            copy.project_id = project
            copy.save()

        if 'pdf' in request.FILES:
            estimate.pdf = request.FILES['pdf']
            if not estimate.pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the SWO PDF"})
                return render(request, 'estimates/all_estimates.html', context)
            estimate.save()

        pdf_file = open(estimate.pdf.path, 'rb')
        pdf_reader = PyPDF2.PdfReader(pdf_file)

        pdf_text = ""
        # Read and print the content from each page
        for page_number in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_number]
            pdf_text += page.extract_text()

        line_items = MasterEstimateLineItem.objects.filter(estimate_id=master)
        for line_item in line_items:
            print(pdf_text)
            amounts = re.findall(fr'{line_item.scope}.?\n', pdf_text)
            print()
            print(amounts)

        # Close the PDF file
        pdf_file.close()

        return redirect('projectmanagement:all_estimates', project_id=project.id)

    return render(request, 'estimates/all_estimates.html', context)


@login_required(login_url='projectmanagement:login')
def delete_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = estimate.project_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(estimate.pdf.path):
            time.sleep(3)
            os.remove(estimate.pdf.path)
            estimate.delete()

    return redirect('projectmanagement:all_estimates', project_id=project.id)


@login_required(login_url='projectmanagement:login')
def delete_master(request, master_id):
    master = get_object_or_404(MasterEstimate, pk=master_id)
    project = master.project_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(master.pdf.path):
            time.sleep(3)
            os.remove(master.pdf.path)
            master.delete()

    return redirect('projectmanagement:all_estimates', project_id=project.id)


@login_required(login_url='projectmanagement:login')
def edit_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = get_object_or_404(Project, pk=estimate.project_id.id)
    subs = Subcontractor.objects.order_by('name')

    context = {
        'estimate': estimate,
        'project': project,
        'subs': subs,
    }

    if request.method == 'POST':
        date = request.POST.get('date')
        sub = request.POST.get('sub')
        csi = request.POST.get('csi')
        total = request.POST.get('total')

        if not date or not sub or not csi or not total:
            context.update({'error_message': "Please enter the subcontractor name. (Less than 50 characters)"})
            return render(request, 'estimates/edit_estimate.html', context)

        estimate.date = date
        estimate.sub_id = get_object_or_404(Subcontractor, pk=sub)
        estimate.csi = csi
        estimate.total = total

        if 'pdf' in request.FILES:
            estimate.pdf = request.FILES['pdf']
            if not estimate.pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Estimate PDF"})
                return render(request, 'estimates/edit_estimate.html', context)

        estimate.save()

    return render(request, 'estimates/edit_estimate.html', context)


@login_required(login_url='projectmanagement:login')
def new_master(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    subs = Subcontractor.objects.order_by("name")
    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)
    total_groups = len(groups) + len(subgroups)

    groups_json = json.dumps(
        [{'id': group.id, 'subgroups': list(subgroups.filter(group_id=group.id).values('id', 'name'))} for group in
         groups])

    if request.method == 'POST':
        csi = request.POST.get('csi')
        master = MasterEstimate()
        master.name = f"{project.name} {csi} Master Estimate"
        master.date = datetime.now()
        master.project_id = project
        master.total = 0
        master.csi = csi
        master.save()

        line_items = process_form_data(request, project)

        for line_item in line_items:
            line_item.estimate_id = master
            line_item.save()


        master = create_estimate(line_items, project, master)
        master.save()

        return redirect('projectmanagement:all_estimates', project_id=project.id)

    return render(request, 'estimates/new_estimate.html', {'project': project, 'subs': subs, 'groups': groups, 'subgroups': subgroups, 'groups_json': groups_json, 'total_groups': total_groups})

def process_form_data(request, project):
    grouped_data = []
    line_items = []
    current_group = None

    for key, values in request.POST.lists():
        if key.startswith('group'):
            group_index = int(key[5:])
            current_group = {'group': values[0], 'rows': []}
            grouped_data.append(current_group)
        elif key.startswith('subgroup'):
            if current_group is not None:
                current_group['subgroup'] = values[0]
        elif key.startswith('scope'):
            if current_group is not None:
                row_index = int(key.split('[')[2].split(']')[0])
                row_data = {
                    'scope': values[0],
                    'qty': request.POST.get(f'qty[{group_index}][{row_index}]'),
                    'unitPrice': request.POST.get(f'unitprice[{group_index}][{row_index}]'),
                    'totalPrice': request.POST.get(f'totalprice[{group_index}][{row_index}]'),
                }
                current_group['rows'].append(row_data)

    for group in grouped_data:
        for row in group['rows']:
            line_item = MasterEstimateLineItem()

            # Convert the string IDs to integers using int()
            try:
                group_id = int(group.get('group'))
            except:
                group_id = None
            try:
                subgroup_id = int(group.get('subgroup'))
            except:
                subgroup_id = None

            # Set the group_id and subgroup_id fields
            line_item.group_id = get_object_or_404(Group, id=group_id) if group_id else None
            line_item.subgroup_id = get_object_or_404(Subgroup, id=subgroup_id)if subgroup_id else None

            # Set the remaining fields
            line_item.project_id = project
            line_item.scope = row['scope']
            line_item.qty = row['qty']
            line_item.unit_price = row['unitPrice']
            line_item.total = float(line_item.qty) * float(line_item.unit_price)

            line_items.append(line_item)

    return line_items
@login_required(login_url='projectmanagement:login')
def estimate_pdf_view(request, estimate_id):
    try:
        estimate = get_object_or_404(Estimate, pk=estimate_id)
    except:
        estimate = get_object_or_404(MasterEstimate, pk=estimate_id)
    pdf_bytes = estimate.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'estimates/estimate_pdf_view.html', {'pdf_data': pdf_data, 'estimate': estimate})

