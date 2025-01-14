import base64
import locale
import time
from datetime import datetime
from io import BytesIO

import PyPDF2
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.shortcuts import render, redirect, get_object_or_404

from ..models import *

locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')


@login_required(login_url='projectmanagement:login')
def all_draws(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    draws = Draw.objects.filter(project_id=project, submitted_date__isnull=True)
    submitted_draws = Draw.objects.filter(project_id=project, submitted_date__isnull=False)
    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)
    exhibits = Exhibit.objects.filter(project_id=project)
    cos = ChangeOrder.objects.filter(project_id=project)
    dcos = DeductiveChangeOrder.objects.filter(project_id=project)
    pos = PurchaseOrder.objects.filter(project_id=project)
    draw_summary_items = DrawSummaryLineItem.objects.filter(draw_id__in=submitted_draws)
    checks = Check.objects.filter(draw_item_id__in=draw_summary_items)

    print(submitted_draws)
    print(draw_summary_items)
    print(checks)

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
        draw_item = get_object_or_404(DrawSummaryLineItem, pk=check.draw_item_id.id)
        check_total += draw_item.draw_amount


    try:
        percent = (check_total / contract_total) * 100
    except:
        percent = 0

    no_group_subgroup = None
    no_group = None
    invoices_with_none_group_subgroup = None
    invoices_with_none_group = None

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

    group_subgroup_totals = {}
    for group in groups:
        group_subgroup_totals[group] = {}
        for subgroup in group.subgroup_set.all():
            group_subgroup_totals[group][subgroup] = 0

    context = {
        'draws': draws,
        'submitted_draws': submitted_draws,
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
def draw_view(request, draw_id):
    draw = get_object_or_404(Draw, pk=draw_id)
    project = get_object_or_404(Project, pk=draw.project_id.id)

    context = {
        'draw': draw,
        'project': project,
    }

    return render(request, 'draws/draw_view.html', context)

@login_required(login_url='projectmanagement:login')
def create_lr(request, draw_item_id, type):
    draw_item = get_object_or_404(DrawSummaryLineItem, pk=draw_item_id)
    lr = LienRelease()
    lr.date = datetime.now()
    lr.type = type
    lr.draw_item_id = draw_item
    lr.save()

    file_path = os.path.join(settings.STATIC_ROOT, f'pdf_templates\lr_{lr.get_LR_type_display_long().lower()}_template.pdf')

    output_path = draw_item.sub_id.name + "_LR_D" + str(draw_item.draw_id.num)

    if os.path.exists(output_path + ".pdf"):
        counter = 1
        while os.path.exists(output_path + "(" + str(counter) + ")" + ".pdf"):
            counter += 1
        output_path += "(" + str(counter) + ")"

    output_path += ".pdf"

    if os.path.exists(file_path):
        with open(file_path, 'rb') as file:
            input_pdf = PyPDF2.PdfReader(file)
            output_pdf = PyPDF2.PdfWriter()

            fields = input_pdf.get_fields()
            for field in fields:
                default = ''
                try:
                    if fields[field]['/DV'] != "":
                        default = fields[field]['/DV']
                    fields[field] = default
                except:
                    fields[field] = ''

            fields['project_name'] = draw_item.draw_id.project_id.name
            fields['project_address'] = draw_item.draw_id.project_id.address + ", " + draw_item.draw_id.project_id.city + ", " + draw_item.draw_id.project_id.state + " " + str(draw_item.draw_id.project_id.zip)
            fields['lr_date'] = lr.date.strftime('%m/%d/%Y')
            fields['draw_total'] = locale.currency(draw_item.draw_amount, grouping=True)
            fields['sub_name_1'] = draw_item.sub_id.name
            fields['sub_name_2'] = draw_item.sub_id.name
            fields['sub_address'] = draw_item.sub_id.address

            for page_num in range(input_pdf._get_num_pages()):
                page = input_pdf._get_page(page_num)
                output_pdf.add_page(page)
                output_pdf.update_page_form_field_values(output_pdf.get_page(page_num), fields)

            with BytesIO() as output_buffer:
                output_pdf.write(output_buffer)

                # Set the file pointer to the beginning of the BytesIO object
                output_buffer.seek(0)

                # Create a Django File object from the BytesIO object
                lr_pdf = File(output_buffer, name=output_path)

                # Assign the File object to the pdf field of the Contract model
                lr.pdf = lr_pdf
                lr.save()

    else:
        print("file path :" + file_path + "does not exist")


@login_required(login_url='projectmanagement:login')
def new_draw(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    project.date = datetime.now()
    project.edited_by = request.user.username

    #Include subs that have exhibits under this project
    exhibits = Exhibit.objects.filter(project_id=project)

    included_subs = []
    for exhibit in exhibits:
        if exhibit.sub_id not in included_subs:
            included_subs.append(exhibit.sub_id)

    context = {
        'project': project,
        'subcontractors': included_subs,
    }

    if request.method == "POST":
        datas = request.POST.get('json-data')
        datas = json.loads(datas)

        draw = Draw()
        draw.date = datetime.now()
        draw.project_id = project
        draw.edited_by = request.user.username
        draw.start_date = datetime.now()
        draw.num = len(Draw.objects.filter(project_id=project)) + 1
        draw.save()

        for data in datas:
            if data:
                draw_amount = data['drawAmountSum']
                description = data['description']

                for exhibitItem in data['exhibitLineItems']:
                    print(exhibitItem['lineItemId'])
                    sub = get_object_or_404(Subcontractor, name=data['subcontractorName'])
                    exhibit_line_item = get_object_or_404(ExhibitLineItem, pk=exhibitItem['lineItemId'])

                    drawItem = DrawLineItem()
                    drawItem.draw_id = draw
                    drawItem.sub_id = sub
                    drawItem.draw_amount = exhibitItem['lineItemValue'] * (exhibitItem['percentComplete'] / 100) - exhibit_line_item.total_paid
                    drawItem.description = description
                    drawItem.exhibit_item_id = exhibit_line_item

                    drawItem.save()

        return redirect('projectmanagement:all_draws', project_id=project_id)

    project.save()

    return render(request, 'draws/new_draw.html', context=context)

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
            if check.pdf:
                if os.path.exists(check.pdf.path):
                    time.sleep(3)
                    os.remove(check.pdf.path)
                    check.pdf.delete()
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
    pdf_bytes = check.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'draws/check_view.html', {'pdf_data': pdf_data, 'check': check})

@login_required(login_url='projectmanagement:login')
def new_check(request, draw_item_id):
    draw_summary_item = get_object_or_404(DrawSummaryLineItem, pk=draw_item_id)
    draw = get_object_or_404(Draw, pk=draw_summary_item.draw_id.id)
    project = get_object_or_404(Project, pk=draw.project_id.id)
    lr = get_object_or_404(LienRelease, draw_item_id=draw_item_id)
    draw_items = DrawLineItem.objects.filter(draw_id=draw, sub_id=draw_summary_item.sub_id)

    context = {
        'draw_summary_item': draw_summary_item,
        'draw_items': draw_items,
        'draw': draw,
        'project': project,
        'lr': lr
    }

    if request.method == 'POST':
        check_date = request.POST.get('check_date')
        check_number = request.POST.get('check_num')

        context.update({
            'check_date': check_date,
            'check_number': check_number,
        })

        if not check_date or not check_number:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'draws/new_check.html', context)

        check = Check()
        check.date = datetime.now()
        check.draw_item_id = draw_summary_item
        check.check_date = check_date
        check.check_num = check_number


        # Handle check PDF
        if 'pdf' in request.FILES:
            check.pdf = request.FILES['pdf']
            if not check.pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'draws/new_check.html', context)

        project.edited_by = request.user.username
        project.date = datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.now()
        draw.save()

        check.save()

        return redirect('projectmanagement:draw_view', draw_id=draw.id)  # Redirect to a success page

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

        # Handle check PDF
        if 'pdf' in request.FILES:
            invoice.invoice_pdf = request.FILES['pdf']
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


@login_required(login_url='projectmanagement:login')
def lr_view(request, lr_id):
    lr = get_object_or_404(LienRelease, pk=lr_id)
    pdf_bytes = lr.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'draws/lr_view.html', {'pdf_data': pdf_data, 'lr': lr})

@login_required(login_url='projectmanagement:login')
def edit_draw_summary_item(request, draw_summary_item_id):
    draw_item = get_object_or_404(DrawSummaryLineItem, pk=draw_summary_item_id)
    check = Check.objects.filter(draw_item_id=draw_item).first()
    lr = get_object_or_404(LienRelease, draw_item_id=draw_item)

    amount_remaining = draw_item.contract_total - draw_item.total_paid - draw_item.draw_amount

    context = {
        'draw_summary_item': draw_item,
        'amount_remaining': amount_remaining,
        'lr': lr,
        'check': check,
        'check_file_url': check.pdf.url if check.pdf else 'No check pdf!',
        'check_date': check.check_date.strftime('%Y-%m-%d') if check and check.check_date else '',
        'check_number': check.check_num if check else '',
        'has_check': check is not None
    }

    if request.method == 'POST':
        draw_amount = request.POST.get('draw_amount')
        description = request.POST.get('description')
        percent_complete = request.POST.get('percent_complete')
        remove_check = request.POST.get('remove_check')
        lr_signed = 'lr_signed' in request.POST

        # Handle file uploads
        lr_file = request.FILES.get('lr_file')
        check_file = request.FILES.get('check_file')

        if not draw_amount or not description or not percent_complete:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'draws/edit_draw_summary_item.html', context)

        # Update draw item details
        draw_item.draw_amount = draw_amount
        draw_item.description = description
        draw_item.percent_complete = percent_complete
        draw_item.save()

        # Handle Lien Release file
        if lr_file:
            lr.pdf = lr_file

        lr.signed = lr_signed
        lr.save()

        # Handle Check file and check removal
        if remove_check == "delete" and check:
            check.delete()
        elif check_file:
            if check:
                check.pdf = check_file
                check.save()
            else:
                # Create a new check if it does not exist
                Check.objects.create(
                    draw_item_id=draw_item,
                    pdf=check_file,
                    check_date=request.POST.get('check_date'),
                    check_number=request.POST.get('check_number')
                )

        return redirect('projectmanagement:draw_view', draw_id=draw_item.draw_id.id)

    return render(request, 'draws/edit_draw_summary_item.html', context)


@login_required(login_url='projectmanagement:login')
def submit_draw(request, draw_id):
    draw = get_object_or_404(Draw, pk=draw_id)
    draw.submitted_date = datetime.now()
    draw.save()

    draw_line_items = DrawLineItem.objects.filter(draw_id=draw)
    for draw_line_item in draw_line_items:
        draw_line_items = DrawLineItem.objects.filter()

    return redirect("projectmanagement:all_draws", project_id=draw.project_id.id)



