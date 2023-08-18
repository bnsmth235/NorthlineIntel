import json
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404
from datetime import datetime
from ..models import *

@login_required(login_url='projectmanagement:login')
def all_draws(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    draws = Draw.objects.order_by('-num').filter(project_id=project)
    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)
    exhibits = Exhibit.objects.filter(project_id=project)
    cos = ChangeOrder.objects.filter(project_id=project)
    dcos = DeductiveChangeOrder.objects.filter(project_id=project)
    pos = PurchaseOrder.objects.filter(project_id=project)
    invoices = Invoice.objects.filter(draw_id__in=draws)
    checks = Check.objects.filter(invoice_id__in=invoices)

    contract_total = 0
    for exhibit in exhibits:
        contract_total += exhibit.total
    for co in cos:
        contract_total += co.total
    for dco in dcos:
        contract_total -= dco.total
    for po in pos:
        contract_total += po.total

    check_total = 0
    for check in checks:
        check_total += check.check_total

    try:
        percent = (check_total / contract_total) * 100
    except:
        percent = 0

    no_group_subgroup = None
    no_group = None
    invoices_with_none_group_subgroup = Invoice.objects.filter(group_id=None, subgroup_id=None)
    invoices_with_none_group = Invoice.objects.filter(group_id=None, subgroup_id=None)

    if invoices_with_none_group_subgroup:
        no_group_subgroup = [[0, 0, 0, 0]] * invoices_with_none_group_subgroup.values('draw_id').distinct().count()
        for invoice in invoices_with_none_group_subgroup:
            no_group_subgroup[invoice.draw_id.num - 1][0] = invoice.draw_id.num - 1
            no_group_subgroup[invoice.draw_id.num - 1][1] += invoice.invoice_total
            for check in Check.objects.filter(invoice_id=invoice):
                no_group_subgroup[invoice.draw_id.num - 1][2] += check.check_total
            try:
                no_group_subgroup[invoice.draw_id.num - 1][3] = (no_group_subgroup[invoice.draw_id.num - 1][2] / no_group_subgroup[invoice.draw_id.num - 1][1]) * 100
            except:
                no_group_subgroup[invoice.draw_id.num - 1][3] = 0

    if invoices_with_none_group:
        no_group = [[0, 0, 0, 0]] * invoices_with_none_group.values('draw_id').distinct().count()
        for invoice in invoices_with_none_group:
            no_group[invoice.draw_id.num - 1][0] = invoice.draw_id.num - 1
            no_group[invoice.draw_id.num - 1][1] += invoice.invoice_total
            for check in Check.objects.filter(invoice_id=invoice):
                no_group[invoice.draw_id.num - 1][2] += check.check_total
            try:
                no_group[invoice.draw_id.num - 1][3] = (no_group[invoice.draw_id.num - 1][2] / no_group[invoice.draw_id.num - 1][1]) * 100
            except:
                no_group[invoice.draw_id.num - 1][3] = 0

    try:
        max_rows = max(len(subgroup.subgroup_set.all()) for subgroup in groups)
    except:
        max_rows = 0
    print("Max rows: ", max_rows)

    context = {
        'draws': draws,
        'project': project,
        'groups': groups,
        'subgroups': subgroups,
        'max_rows': max_rows,
        'no_group_subgroup':no_group_subgroup,
        'no_group': no_group,
        'contract_total': contract_total,
        'check_total': check_total,
        'percent': percent
    }

    return render(request, 'draws/all_draws.html', context)


@login_required(login_url='projectmanagement:login')
def draw_view(request, project_id, draw_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    contracts = Contract.objects.order_by('-date').filter(project_id=project.id)
    draws = Draw.objects.order_by('-date').filter(project_id=project.id)
    invoices = Invoice.objects.order_by('-invoice_date').order_by('sub_id').filter(draw_id=draw.id)
    checks = Check.objects.order_by('-check_date').order_by('invoice_id').filter(invoice_id__in=invoices)
    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)

    total_invoice_amount = invoices.aggregate(total=Sum('invoice_total'))['total']

    return render(request, 'draws/draw_view.html', {'draw': draw, 'draws': draws, 'invoices': invoices, 'total_invoice_amount':total_invoice_amount,'project': project, 'contracts': contracts, 'checks': checks, 'groups': groups, 'subgroups': subgroups})



@login_required(login_url='projectmanagement:login')
def new_draw(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    project.date = datetime.now()
    project.edited_by = request.user.username

    draw = Draw()
    draw.date = datetime.now()
    draw.project_id = project
    draw.edited_by = request.user.username
    draw.start_date = datetime.now()
    draw.num = len(Draw.objects.filter(project_id=project)) + 1

    draw.save()
    project.save()

    return redirect('projectmanagement:all_draws', project_id=project_id)


@login_required(login_url='projectmanagement:login')
def delete_draw(request, project_id):
    if request.method == 'POST':
        draw_id = request.POST.get('draw_id')
        username = request.POST.get('username')
        print("Attempting to delete draw " + draw_id)

        if username == request.user.username:
            cur_draw = get_object_or_404(Draw, pk=draw_id)
            cur_draw.delete()
            print("Draw deleted")
        else:
            print("Username incorrect")

    return redirect('projectmanagement:all_draws', project_id=project_id)



@login_required(login_url='projectmanagement:login')
def new_invoice(request, project_id, draw_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    subs = Subcontractor.objects.order_by('name')
    vendors = Vendor.objects.order_by('name')
    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)

    groups_json = json.dumps(
        [{'id': group.id, 'subgroups': list(subgroups.filter(group_id=group.id).values('id', 'name'))} for group in groups])

    context = {
        'subs': subs,
        'vendors': vendors,
        'project': project,
        'groups': groups,
        'groups_json': groups_json,
        'subgroups': subgroups,
        'draw': draw,
        'method_choices': METHOD_OPTIONS,
    }

    if request.method == 'POST':
        invoice_date = request.POST.get('invoice_date')
        invoice_num = request.POST.get('invoice_num')
        csi = request.POST.get('csi')
        category = request.POST.get('category')
        method = request.POST.get('method')
        subven_name = request.POST.get('subven')
        try_sub = Subcontractor.objects.filter(name=subven_name).first()
        if not try_sub:
            sub = Vendor.objects.filter(name=subven_name).first()
        else:
            sub = try_sub

        invoice_total = request.POST.get('invoice_total')
        group = request.POST.get('group')
        subgroup = request.POST.get('subgroup')
        description = request.POST.get('description')
        w9 = sub.w9

        context.update({
            'invoice_date': invoice_date,
            'invoice_num': invoice_num,
            'csi': csi,
            'category': category,
            'methodselect': method,
            'subselect': sub,
            'invoice_total': invoice_total,
            'description': description
        })

        if not csi or not category or not method or not sub or not invoice_total or not description:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'draws/new_invoice.html', context)

        invoice = Invoice()
        invoice.draw_id = draw
        invoice.invoice_date = invoice_date
        invoice.invoice_num = invoice_num
        invoice.csi = csi
        invoice.category = category
        invoice.method = method
        try:
            invoice.sub_id = sub
        except:
            invoice.vendor_id = sub
        invoice.invoice_total = invoice_total
        invoice.description = description
        try:
            invoice.group_id = get_object_or_404(Group, pk=group)
        except:
            pass

        try:
            invoice.subgroup_id = get_object_or_404(Subgroup, pk=subgroup)
        except:
            pass
        invoice.w9 = w9

        # Handle invoice PDF
        if 'invoice_pdf' in request.FILES:
            invoice.invoice_pdf = request.FILES['invoice_pdf']
            if not invoice.invoice_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Invoice PDF"})
                return render(request, 'draws/new_invoice.html', context)

        # Save invoice and related objects
        project.edited_by = request.user.username
        project.date = datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.now()
        draw.save()

        invoice.save()

        return redirect('projectmanagement:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'draws/new_invoice.html', context)


@login_required(login_url='projectmanagement:login')
def edit_invoice(request, project_id, draw_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    sub = None
    vendor = None
    try:
        sub = get_object_or_404(Subcontractor, pk=invoice.sub_id.id)
    except:
        vendor = get_object_or_404(Vendor, pk=invoice.vendor_id.id)
    subs = Subcontractor.objects.order_by('name')
    vendors = Vendor.objects.order_by('name')
    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)

    groups_json = json.dumps(
        [{'id': group.id, 'subgroups': list(subgroups.filter(group_id=group.id).values('id', 'name'))} for group in
         groups])

    context = {
        'subs': subs,
        'vendors': vendors,
        'subselect': sub,
        'vendorselect': vendor,
        'project': project,
        'invoice': invoice,
        'groups': groups,
        'subgroups': subgroups,
        'groups_json': groups_json,
        'draw': draw,
        'method_choices': METHOD_OPTIONS,
    }

    if request.method == 'POST':
        invoice_date = request.POST.get('invoice_date')
        invoice_num = request.POST.get('invoice_num')
        csi = request.POST.get('csi')
        category = request.POST.get('category')
        method = request.POST.get('method')
        subven_name = request.POST.get('sub')
        try_sub = Subcontractor.objects.filter(name=subven_name).first()
        if not try_sub:
            invoice.sub_id = None
            invoice.vendor_id = Vendor.objects.filter(name=subven_name).first()
            invoice.w9 = invoice.vendor_id.w9
        else:
            sub = try_sub
            invoice.vendor_id = None
            invoice.sub_id = sub
            invoice.w9 = sub.w9
        group = request.POST.get('group')
        subgroup = request.POST.get('subgroup')
        invoice_total = request.POST.get('invoice_total')
        description = request.POST.get('description')

        if group != 'None':
            invoice.group_id = get_object_or_404(Group, pk=group)
        if group == 'None':
            invoice.group_id = None
        if subgroup and subgroup != 'None':
            invoice.subgroup_id = get_object_or_404(Subgroup, pk=subgroup)
        if subgroup == 'None':
            invoice.subgroup_id = None
        if invoice_date:
            invoice.invoice_date = invoice_date
        if invoice_num:
            invoice.invoice_num = invoice_num
        if csi:
            invoice.csi = csi
        if category:
            invoice.category = category
        if method:
            invoice.method = method
        if invoice_total:
            invoice.invoice_total = invoice_total
        if description:
            invoice.description = description

        # Handle invoice PDF
        if 'invoice_pdf' in request.FILES:
            invoice.invoice_pdf = request.FILES['invoice_pdf']
            if not invoice.invoice_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Invoice PDF"})
                return render(request, 'draws/edit_invoice.html', context)

        # Save invoice and related objects
        project.edited_by = request.user.username
        project.date = datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.now()
        draw.save()

        invoice.save()

        return redirect('projectmanagement:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'draws/edit_invoice.html', context)


@login_required(login_url='projectmanagement:login')
def delete_check(request, check_id):
    check = get_object_or_404(Check, pk=check_id)
    invoice = check.invoice_id
    draw = invoice.draw_id
    project = draw.project_id

    if request.method == 'POST':
        print("Attempting to delete check")
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            # Delete the PDF file from storage
            if check.check_pdf:
                if os.path.exists(check.check_pdf.path):
                    time.sleep(3)
                    os.remove(check.check_pdf.path)
                    check.check_pdf.delete()
            if check.lien_release_pdf:
                if os.path.exists(check.lien_release_pdf.path):
                    time.sleep(3)
                    os.remove(check.lien_release_pdf.path)
                    check.lien_release_pdf.delete()

            project.date = datetime.now()
            draw.date = datetime.now()
            invoice.date = datetime.now()

            project.save()
            draw.save()
            invoice.save()
            check.delete()

        return redirect('projectmanagement:draw_view', project_id=project.id, draw_id=draw.id)  # Redirect to a success page

    return render(request, 'draws/draw_view.html', {'project': project, 'draw':draw, 'error_message': "Document could not be deleted."})


@login_required(login_url='projectmanagement:login')
def check_view(request, check_id):
    check = get_object_or_404(Check, pk=check_id)
    pdf_bytes = check.check_pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'draws/check_view.html', {'pdf_data': pdf_data, 'check': check})


@login_required(login_url='projectmanagement:login')
def invoice_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    pdf_bytes = invoice.invoice_pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/invoice_view.html', {'pdf_data': pdf_data, 'invoice': invoice})




@login_required(login_url='projectmanagement:login')
def new_check(request, project_id, draw_id, invoice_id):
    draw = get_object_or_404(Draw, pk=draw_id)
    project = get_object_or_404(Project, pk=project_id)
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    subs = Subcontractor.objects.order_by('name')

    context = {
        'draw': draw,
        'project': project,
        'invoice': invoice,
        'subs': subs,
        'lien_release_type_choices': LIEN_RELEASE_OPTIONS
    }

    if request.method == 'POST':
        check_date = request.POST.get('check_date')
        check_number = request.POST.get('check_num')
        sub = request.POST.get('sub')
        total = request.POST.get('check_total')
        lien_release_type = request.POST.get('lien_release_type')
        distributed = request.POST.get('distributed')
        signed = bool(request.POST.get('signed', False))

        context.update({
            'check_date': check_date,
            'check_number': check_number,
            'sub': sub,
            'check_total': total,
            'lien_release_type': lien_release_type,
            'distributed': distributed,
            'signed': signed
        })

        if not check_date or not check_number or not total or not sub:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'draws/new_check.html', context)

        check = Check()
        check.date = datetime.now()
        check.draw_id = draw
        check.sub_id = sub
        check.invoice_id = invoice
        check.check_date = check_date
        check.check_num = check_number
        check.check_total = total
        check.lien_release_type = lien_release_type
        check.signed = signed
        check.distributed = distributed

        # Handle lien release PDF
        if 'check_pdf' in request.FILES:
            check.check_pdf = request.FILES['check_pdf']
            if not check.check_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'draws/new_check.html', context)

        # Handle lien release PDF
        if 'lien_release_pdf' in request.FILES:
            check.lien_release_pdf = request.FILES['lien_release_pdf']
            if not check.lien_release_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'draws/new_check.html', context)

        else:
            check.signed = False

        project.edited_by = request.user.username
        project.date = datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.now()
        draw.save()

        invoice.date = datetime.now()
        invoice.save()

        check.save()

        return redirect('projectmanagement:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'draws/new_check.html', context)


@login_required(login_url='projectmanagement:login')
def edit_check(request, check_id):
    check = get_object_or_404(Check, pk=check_id)
    invoice = check.invoice_id
    draw = invoice.draw_id
    project = draw.project_id
    sub = get_object_or_404(Subcontractor, pk=invoice.sub_id.id)
    subs = Subcontractor.objects.order_by('name')

    context = {
        'subs': subs,
        'subselect': sub,
        'check': check,
        'lien_release_type_choices': LIEN_RELEASE_OPTIONS
    }

    if request.method == 'POST':
        check_date = request.POST.get('check_date')
        check_num = request.POST.get('check_num')
        sub = request.POST.get('sub')
        check_total = request.POST.get('check_total')
        lien_release_type = request.POST.get('lien_release_type')
        distributed = request.POST.get('distributed')
        signed = bool(request.POST.get('signed', False))

        if not check_date or not check_num or not sub or not check_total or not lien_release_type:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'draws/edit_check.html', context)

        check.date = datetime.now()
        check.check_date = check_date
        check.check_num = check_num
        check.check_total = check_total
        check.sub_id = sub
        check.lien_release_type = lien_release_type
        check.distributed = distributed
        check.signed = signed

        print("******************************")
        print(check.signed)
        print("******************************")

        # Handle check PDF
        if 'check_pdf' in request.FILES:
            invoice.invoice_pdf = request.FILES['check_pdf']
            if not invoice.invoice_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Check PDF"})
                return render(request, 'draws/edit_check.html', context)

        # Handle lien release PDF
        if 'lien_release_pdf' in request.FILES:
            invoice.lien_release_pdf = request.FILES['lien_release_pdf']
            if not invoice.lien_release_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'draws/edit_check.html', context)

        else:
            check.signed = None

        # Save invoice and related objects
        project.edited_by = request.user.username
        project.date = datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.now()
        draw.save()

        invoice.date = datetime.now()

        check.save()

        return redirect('projectmanagement:draw_view', project_id=project.id, draw_id=draw.id)  # Redirect to a success page

    return render(request, 'draws/edit_check.html', context)

