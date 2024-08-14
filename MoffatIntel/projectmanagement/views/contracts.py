from datetime import datetime
import time
from io import BytesIO
from PyPDF2.generic import NameObject
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render, redirect, get_object_or_404
import base64
import PyPDF2
from ..models import *
from ..pdf_create.create_change_order import create_change_order
from ..pdf_create.create_exhibit import create_exhibit
from ..pdf_create.create_purchase_order import create_purchase_order
from django.db import transaction


@login_required(login_url='projectmanagement:login')
def contract_view(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    contracts = Contract.objects.order_by("-date").filter(project_id=project).filter(sub_id=sub)
    exhibits = Exhibit.objects.order_by("-date").filter(project_id=project).filter(sub_id=sub)
    swos = SWO.objects.order_by("-date").filter(project_id=project).filter(sub_id=sub)

    context = {
        'project': project,
        'sub': sub,
        'contracts': contracts,
        'exhibits': exhibits,
        'SWOs': swos,
    }

    if request.method == 'POST':
        form_type = request.POST.get('form-type')
        if form_type == 'swo':
            swo = SWO()
            swo.date = datetime.now()
            swo.total = request.POST.get('total')
            swo.sub_id = sub
            swo.project_id = project

            if 'swo_pdf' in request.FILES:
                swo.pdf = request.FILES['swo_pdf']
                if not swo.pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the SWO PDF"})
                    return render(request, 'contracts/contract_view.html', context)

            try:
                swo.total = float(swo.total)
                if swo.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'contracts/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'contracts/contract_view.html', context)

            swo.save()
            return redirect('projectmanagement:contract_view', project_id, sub_id)

        if form_type == 'exhibit':
            exhibit = Exhibit()
            exhibit.date = datetime.now()
            exhibit.total = request.POST.get('total')
            exhibit.sub_id = sub
            exhibit.project_id = project

            if 'exhibit_pdf' in request.FILES:
                exhibit.pdf = request.FILES['exhibit_pdf']
                if not exhibit.pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the Exhibit PDF"})
                    return render(request, 'contracts/contract_view.html', context)

            try:
                exhibit.total = float(exhibit.total)
                if exhibit.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'contracts/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'contracts/contract_view.html', context)

            exhibit.save()
            return redirect('projectmanagement:contract_view', project_id, sub_id)

        if form_type == 'contract':
            contract = Contract()
            contract.date = datetime.now()
            contract.total = request.POST.get('total')
            contract.sub_id = sub
            contract.project_id = project

            if 'contract_pdf' in request.FILES:
                contract.pdf = request.FILES['contract_pdf']
                if not contract.pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the Contract PDF"})
                    return render(request, 'contracts/contract_view.html', context)

            try:
                contract.total = float(contract.total)
                if contract.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'contracts/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'contracts/contract_view.html', context)

            contract.save()
            return redirect('projectmanagement:contract_view', project_id, sub_id)

    return render(request, 'contracts/contract_view.html', context)

@login_required(login_url='projectmanagement:login')
def deductive_change_orders(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    dcos = DeductiveChangeOrder.objects.order_by('-date').filter(project_id=project).filter(sub_id=sub)

    return render(request, 'contracts/deductive_change_orders.html', {'project': project, 'sub': sub, 'dcos': dcos})


@login_required(login_url='projectmanagement:login')
def change_orders(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    cos = ChangeOrder.objects.order_by('-date').filter(project_id=project).filter(sub_id=sub)

    return render(request, 'contracts/change_orders.html', {'project': project, 'sub': sub, 'cos': cos})


@login_required(login_url='projectmanagement:login')
def purchase_orders(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    pos = PurchaseOrder.objects.order_by('-date').order_by('vendor_id').filter(project_id=project)

    return render(request, 'contracts/purchase_orders.html', {'project': project, 'pos': pos})


@login_required(login_url='projectmanagement:login')
def new_change_order(request, project_id=None, sub_id=None):
    projectselect = get_object_or_404(Project, pk=project_id) if project_id else None
    subselect = get_object_or_404(Subcontractor, pk=sub_id) if sub_id else None
    projects = Project.objects.order_by('name')
    subs = Subcontractor.objects.order_by('name')
    contracts = Contract.objects.order_by('-date')
    contracts_data = json.dumps(
        [
            {
                'id': contract.id,
                'project_id': contract.project_id.id,
                'sub_id': contract.sub_id.id,
                'total': contract.total,
                'date': contract.date.isoformat(),  # Convert datetime to string
            }
            for contract in contracts
        ],
        cls=DjangoJSONEncoder
    )

    context = {
        'projectselect': projectselect,
        'subselect': subselect,
        'projects': projects,
        'subs': subs,
        'contracts_data': contracts_data,
    }

    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=request.POST.get('contract'))
        project = contract.project_id
        sub = contract.sub_id

        rows = []
        for key, value in request.POST.items():
            if key.startswith('scope'):
                # Handle scope field
                scope_index = key.replace('scope', '')
                scope_value = value
                # Process the scope value

                # Get corresponding qty, unitprice, and totalprice values
                qty_key = f'qty{scope_index}'
                unitprice_key = f'unitprice{scope_index}'

                qty_value = request.POST.get(qty_key)
                unitprice_value = request.POST.get(unitprice_key)
                totalprice_value = float(qty_value) * float(unitprice_value)

                if scope_value == "" or float(qty_value) <= 0 or float(unitprice_value) <= 0:
                    context.update({'error_message': "All fields need to be filled."})
                    return render(request, 'contracts/new_change_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'contracts/new_change_order.html', context)

                # Create a dictionary for the change order data
                co_data = {
                    'scope_value': scope_value,
                    'qty_value': qty_value,
                    'unitprice_value': unitprice_value,
                    'totalprice_value': totalprice_value,
                }

                rows.append(co_data)

        co = create_change_order(request.POST, "Change Order", rows)

        return redirect('projectmanagement:change_orders', project_id=project.id, sub_id=sub.id)

    return render(request, 'contracts/new_change_order.html', context)


@login_required(login_url='projectmanagement:login')
def delete_change_order(request, co_id):
    co = get_object_or_404(ChangeOrder, pk=co_id)

    file_path = co.pdf.path
    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(file_path):
            time.sleep(3)
            os.remove(file_path)
            co.delete()

    return redirect('projectmanagement:change_orders', project_id=get_object_or_404(Project, pk=co.project_id), sub_id=get_object_or_404(Subcontractor, pk=co.sub_id))

@login_required(login_url='projectmanagement:login')
def delete_deductive_change_order(request, dco_id):
    dco = get_object_or_404(DeductiveChangeOrder, pk=dco_id)
    project = dco.project_id
    sub = dco.sub_id

    file_path = dco.pdf.path
    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(file_path):
            time.sleep(3)
            os.remove(file_path)
            dco.delete()

    return redirect('projectmanagement:deductive_change_orders', project.id, sub.id)

@login_required(login_url='projectmanagement:login')
def delete_purchase_order(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    project = po.project_id
    file_path = po.pdf.path
    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(file_path):
            time.sleep(3)
            os.remove(file_path)
            po.delete()

    return redirect('projectmanagement:purchase_orders', project_id=project.id)



@login_required(login_url='projectmanagement:login')
def new_deductive_change_order(request, project_id = None, sub_id = None):
    projectselect = get_object_or_404(Project, pk=project_id) if project_id else None
    subselect = get_object_or_404(Subcontractor, pk=sub_id) if sub_id else None
    projects = Project.objects.order_by('name')
    subs = Subcontractor.objects.order_by('name')
    contracts = Contract.objects.order_by('-date')
    contracts_data = json.dumps(
        [
            {
                'id': contract.id,
                'project_id': contract.project_id.id,
                'sub_id': contract.sub_id.id,
                'total': contract.total,
                'date': contract.date.isoformat(),  # Convert datetime to string
            }
            for contract in contracts
        ],
        cls=DjangoJSONEncoder
    )

    context = {
        'projectselect': projectselect,
        'subselect': subselect,
        'projects': projects,
        'subs': subs,
        'contracts_data': contracts_data,
    }

    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=request.POST.get('contract'))
        project = contract.project_id
        sub = contract.sub_id

        rows = []
        for key, value in request.POST.items():
            if key.startswith('scope'):
                # Handle scope field
                scope_index = key.replace('scope', '')
                scope_value = value
                # Process the scope value

                # Get corresponding qty, unitprice, and totalprice values
                qty_key = f'qty{scope_index}'
                unitprice_key = f'unitprice{scope_index}'

                qty_value = request.POST.get(qty_key)
                unitprice_value = request.POST.get(unitprice_key)
                totalprice_value = float(qty_value) * float(unitprice_value)

                if scope_value == "" or float(qty_value) <= 0 or float(unitprice_value) <= 0:
                    context.update({'error_message': "All fields need to be filled."})
                    return render(request, 'contracts/new_deductive_change_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'contracts/new_deductive_change_order.html', context)

                # Create a dictionary for the change order data
                co_data = {
                    'scope_value': scope_value,
                    'qty_value': qty_value,
                    'unitprice_value': unitprice_value,
                    'totalprice_value': totalprice_value,
                }

                rows.append(co_data)

        dco = create_change_order(request.POST, "Deductive Change Order", rows)

        return redirect('projectmanagement:deductive_change_orders', project_id=project.id, sub_id=sub.id)

    return render(request, 'contracts/new_deductive_change_order.html', context)



@login_required(login_url='projectmanagement:login')
def new_contract(request, project_id = None, sub_id = None):
    projects = Project.objects.order_by('name')
    subs = Subcontractor.objects.order_by('name')

    context = {'projects': projects, 'subs': subs}
    if project_id:
        project = get_object_or_404(Project, pk=project_id)
        context.update({'projectselect': project})
    if sub_id:
        sub = get_object_or_404(Subcontractor, pk=project_id)
        context.update({'subselect':sub})

    if request.method == 'POST':
        project = get_object_or_404(Project, pk=request.POST.get('project'))
        sub = get_object_or_404(Subcontractor, pk=request.POST.get('sub'))
        contract_date = request.POST.get('contract_date')
        description = request.POST.get('description')
        contract_total = request.POST.get('contract_total')
        p_and_p = bool(request.POST.get('p_and_p'))
        guarantor = bool(request.POST.get('guarantor'))
        payroll_cert = bool(request.POST.get('payroll_cert'))
        complete_drawings = bool(request.POST.get('complete_drawings'))
        o_and_m = bool(request.POST.get('o_and_m'))
        as_built = bool(request.POST.get('as_built'))
        manuals = bool(request.POST.get('manuals'))
        listed_in_subcontract = bool(request.POST.get('listed_in_subcontract'))
        listed_in_exhibit = bool(request.POST.get('listed_in_exhibit'))
        offsite_disposal = bool(request.POST.get('offsite_disposal'))
        onsite_dumpster_sub_pay = bool(request.POST.get('onsite_dumpster_sub_pay'))
        onsite_dumpster = bool(request.POST.get('onsite_dumpster'))

        context.update({
            'failure': True,
            'projectselect': project,
            'subselect': sub,
            'contract_date': contract_date,
            'description': description,
            'contract_total': contract_total,
            'p_and_p': p_and_p,
            'guarantor': guarantor,
            'payroll_cert': payroll_cert,
            'complete_drawings': complete_drawings,
            'o_and_m': o_and_m,
            'as_built': as_built,
            'manuals': manuals,
            'listed_in_subcontract': listed_in_subcontract,
            'listed_in_exhibit': listed_in_exhibit,
            'offsite_disposal': offsite_disposal,
            'onsite_dumpster_sub_pay': onsite_dumpster_sub_pay,
            'onsite_dumpster': onsite_dumpster,
        })

        if not project or not sub or not description or not contract_total or not contract_date:
            context.update({'error_message': "Please fill out all fields as specified (missing req data)"})
            return render(request, 'contracts/new_contract.html', context)

        if listed_in_exhibit == listed_in_subcontract:
            context.update({'error_message': "Please fill out all fields as specified (sub/exhibit)"})
            return render(request, 'contracts/new_contract.html', context)

        if (offsite_disposal + onsite_dumpster + onsite_dumpster_sub_pay) != 1:
            context.update({'error_message': "Please fill out all fields as specified (disposal)"})
            return render(request, 'contracts/new_contract.html', context)

        if not project in projects or not sub in subs:
            context.update({'error_message': "Please pick an existing Project and Subcontractor"})
            return render(request, 'contracts/new_contract.html', context)

        try:
            contract_total = float(contract_total)
            if contract_total < 0:
                raise
        except:
            context.update({'error_message': "Contract total must be a positive number"})
            return render(request, 'contracts/new_contract.html', context)

        swo = SWO()
        swo.date = contract_date
        swo.total = contract_total
        swo.sub_id = sub
        swo.description = description[:196]+"..."
        swo.project_id = project

        file_path = os.path.join(settings.STATIC_ROOT, 'pdf_templates\contract_template.pdf')

        output_path = sub.name + " Contract " + contract_date

        if os.path.exists(output_path + ".pdf"):
            counter = 1
            while os.path.exists(output_path + "("+str(counter)+")" + ".pdf"):
                counter += 1
            output_path += "("+str(counter)+")"

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

                fields['sub_name'] = sub.name
                fields['sub_address'] = sub.address
                fields['job_number'] = project.id
                fields['contract_date'] = contract_date
                fields['project_name'] = project.name
                fields['project_address'] = project.address
                fields['project_city_state_zip'] = project.city + ", " + project.state + ", " + str(project.zip)
                fields['contract_num'] = len(Contract.objects.all()) + 1
                fields['sub_w9'] = sub.w9
                fields['description'] = description
                fields['contract_total'] = "$" + "{:.2f}".format(contract_total)
                fields['contract_total_2'] = "$" + "{:.2f}".format(contract_total)

                fields['p_and_p_req'] = NameObject("/0") if p_and_p else "/Off"
                fields['p_and_p_no_req'] = NameObject("/0") if not p_and_p else "/Off"
                fields['guarantor_req'] = NameObject("/0") if guarantor else "/Off"
                fields['guarantor_no_req'] = NameObject("/0") if not guarantor else "/Off"
                fields['payroll_cert_req'] = NameObject("/0") if payroll_cert else "/Off"
                fields['payroll_cert_no_req'] = NameObject("/0") if not payroll_cert else "/Off"
                fields['complete_drawings'] = NameObject("/0") if complete_drawings else "/Off"
                fields['o_and_m'] = NameObject("/0") if o_and_m else "/Off"
                fields['as_built'] = NameObject("/0") if as_built else "/Off"
                fields['manuals'] = NameObject("/0") if manuals else "/Off"
                fields['drawings_no_req'] = NameObject("/0") if not complete_drawings and not o_and_m and not as_built and not manuals else "\Off"
                fields['listed_in_subcontract'] = NameObject("/0") if listed_in_subcontract else "/Off"
                fields['listed_in_exhibit'] = NameObject("/0") if listed_in_exhibit else "/Off"
                fields['offsite_disposal'] = NameObject("/0") if offsite_disposal else "/Off"
                fields['onsite_dumpster_sub_pay'] = NameObject("/0") if onsite_dumpster_sub_pay else "/Off"
                fields['onsite_dumpster'] = NameObject("/0") if onsite_dumpster else "/Off"

                for page_num in range(input_pdf._get_num_pages()):
                    page = input_pdf._get_page(page_num)
                    output_pdf.add_page(page)
                    output_pdf.update_page_form_field_values(output_pdf.get_page(page_num), fields)

                with BytesIO() as output_buffer:
                    output_pdf.write(output_buffer)

                    # Set the file pointer to the beginning of the BytesIO object
                    output_buffer.seek(0)

                    # Create a Django File object from the BytesIO object
                    contract_pdf = File(output_buffer, name=output_path)

                    # Assign the File object to the pdf field of the Contract model
                    swo.pdf = contract_pdf
                    swo.save()

                    if listed_in_exhibit:
                        print("***********LISTED IN EXHIBIT**************")
                        exhibit = create_exhibit(request.POST, project, sub)

                        merger = PyPDF2.PdfMerger()

                        input_files = [swo.pdf.path, exhibit.pdf.path]

                        for file in input_files:
                            merger.append(file)

                        temp_path = os.path.join(settings.STATIC_ROOT, "temp.pdf")

                        merger.write(temp_path)
                        merger.close()

                        with open(temp_path, 'rb') as file:
                            file_content = file.read()

                        file_data = ContentFile(file_content)
                        os.remove(temp_path)
                        print("*************MERGED**************")

                        contract = Contract()
                        contract.date = contract_date
                        contract.total = contract_total
                        contract.sub_id = sub
                        contract.description = description[:196] + "..."
                        contract.project_id = project

                        contract.pdf.delete(save=False)
                        contract.pdf.save(output_path, file_data)
                        contract.save()

                project.date = datetime.now()
                project.edited_by = request.user.username
                project.save()

        else:
            print("file path :" + file_path +"does not exist")

        return redirect('projectmanagement:contract_view', project_id=project.id, sub_id=sub.id)

    return render(request, 'contracts/new_contract.html', context)


@login_required(login_url='projectmanagement:login')
def new_purchase_order(request, project_id=None):
    projectselect = get_object_or_404(Project, pk=project_id) if project_id else None
    projects = Project.objects.order_by('name')
    vendors = Vendor.objects.order_by('name')

    context = {
        'projectselect': projectselect,
        'projects': projects,
        'vendors': vendors,
    }

    if request.method == 'POST':
        project = get_object_or_404(Project, pk=request.POST.get('project'))
        vendor = get_object_or_404(Vendor, pk=request.POST.get('vendor'))
        rows = []
        for key, value in request.POST.items():
            if key.startswith('scope'):
                # Handle scope field
                scope_index = key.replace('scope', '')
                scope_value = value
                # Process the scope value

                # Get corresponding qty, unitprice, and totalprice values
                qty_key = f'qty{scope_index}'
                unitprice_key = f'unitprice{scope_index}'

                qty_value = request.POST.get(qty_key)
                unitprice_value = request.POST.get(unitprice_key)
                totalprice_value = float(qty_value) * float(unitprice_value)

                if scope_value == "" or float(qty_value) <= 0 or float(unitprice_value) <= 0:
                    context.update({'error_message': "All fields need to be filled."})
                    return render(request, 'contracts/new_purchase_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'contracts/new_purchase_order.html', context)

                # Create a dictionary for the change order data
                po_data = {
                    'scope_value': scope_value,
                    'qty_value': qty_value,
                    'unitprice_value': unitprice_value,
                    'totalprice_value': totalprice_value,
                }

                rows.append(po_data)
        print("Going into creation...")
        po = create_purchase_order(project, vendor, rows)

        return redirect('projectmanagement:purchase_orders', project_id=project.id)

    return render(request, 'contracts/new_purchase_order.html', context)


@login_required(login_url='projectmanagement:login')
def delete_contract(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    project = contract.project_id
    sub = contract.sub_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(contract.pdf.path):
            time.sleep(3)
            os.remove(contract.pdf.path)
            contract.delete()

    return redirect('projectmanagement:contract_view', project_id=project.id, sub_id=sub.id)


@login_required(login_url='projectmanagement:login')
def delete_swo(request, swo_id):
    swo = get_object_or_404(SWO, pk=swo_id)
    project = swo.project_id
    sub = swo.sub_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(swo.pdf.path):
            time.sleep(3)
            os.remove(swo.pdf.path)
            swo.delete()

    return redirect('projectmanagement:contract_view', project_id=project.id, sub_id=sub.id)

@login_required(login_url='projectmanagement:login')
def contract_pdf_view(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    pdf_bytes = contract.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/contract_pdf_view.html', {'pdf_data': pdf_data, 'contract': contract})

@login_required(login_url='projectmanagement:login')
def swo_pdf_view(request, swo_id):
    swo = get_object_or_404(SWO, pk=swo_id)
    pdf_bytes = swo.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/contract_pdf_view.html', {'pdf_data': pdf_data, 'SWO': swo})

@login_required(login_url='projectmanagement:login')
def co_pdf_view(request, co_id):
    co = get_object_or_404(ChangeOrder, pk=co_id)
    pdf_bytes = co.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/co_pdf_view.html', {'pdf_data': pdf_data, 'co': co})

@login_required(login_url='projectmanagement:login')
def po_pdf_view(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    pdf_bytes = po.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/po_pdf_view.html', {'pdf_data': pdf_data, 'po': po})

@login_required(login_url='projectmanagement:login')
def dco_pdf_view(request, dco_id):
    dco = get_object_or_404(DeductiveChangeOrder, pk=dco_id)
    pdf_bytes = dco.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/dco_pdf_view.html', {'pdf_data': pdf_data, 'dco': dco})

@login_required(login_url='projectmanagement:login')
def exhibit_pdf_view(request, exhibit_id):
    exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
    pdf_bytes = exhibit.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'contracts/exhibit_pdf_view.html', {'pdf_data': pdf_data, 'exhibit': exhibit})

@login_required(login_url='projectmanagement:login')
def new_exhibit(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    exhibit = Exhibit()

    exhibit.date = datetime.now().strftime('%Y-%m-%d')

    try:
        sub = get_object_or_404(Subcontractor, pk=sub_id)
    except:
        sub = get_object_or_404(Vendor, pk=sub_id)

    exhibits = Exhibit.objects.order_by("-date").filter(project_id=project).filter(sub_id=sub)
    exhibit.name = "Exhibit " + chr(len(exhibits) + 65)
    exhibit.sub_id = sub
    exhibit.project_id = project
    exhibit.save()

    groups = Group.objects.filter(project_id=project)
    subgroups = Subgroup.objects.filter(group_id__in=groups)
    total_groups = len(groups) + len(subgroups)

    groups_json = json.dumps(
        [{'id': group.id, 'subgroups': list(subgroups.filter(group_id=group.id).values('id', 'name'))} for group in
         groups])

    if request.method == 'POST':
        line_items = process_form_data(request)
        for line_item in line_items:
            line_item.project_id = project
            line_item.exhibit_id = exhibit
            try:
                line_item.sub_id = sub
                line_item.vendor_id = None
            except:
                line_item.vendor_id = sub
                line_item.sub_id = None
            line_item.save()

        exhibit = create_exhibit(exhibit, line_items, project, sub)

        return redirect('projectmanagement:contract_view', project_id=project.id, sub_id=sub.id)

    return render(request, 'contracts/new_exhibit.html', {'project': project, 'sub': sub, 'groups': groups, 'subgroups': subgroups, 'groups_json': groups_json, 'total_groups': total_groups})


def process_form_data(request):
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
            line_item = ExhibitLineItem()
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
            line_item.project_id_id = 1
            line_item.sub_id_id = 1
            line_item.vendor_id_id = 1
            line_item.scope = row['scope']
            line_item.qty = row['qty']
            line_item.unit_price = row['unitPrice']
            line_item.total = float(line_item.qty) * float(line_item.unit_price)

            line_items.append(line_item)

    return line_items

@login_required(login_url='projectmanagement:login')
def delete_exhibit(request, exhibit_id):
    exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
    project = exhibit.project_id
    sub = exhibit.sub_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        try:
            if os.path.exists(exhibit.pdf.path):
                time.sleep(3)
                os.remove(exhibit.pdf.path)

        except:
            print("Could not delete exhibit, or file does not exist")
        exhibit.delete()

    return redirect('projectmanagement:contract_view', project_id=project.id, sub_id=sub.id)

@login_required(login_url='projectmanagement:login')
def sub_select(request, project_id):
    subs = Subcontractor.objects.order_by("name")
    project = get_object_or_404(Project, pk=project_id)

    return render(request, 'contracts/sub_select.html', {'subs': subs, 'project': project})



