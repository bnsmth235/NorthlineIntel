import json
import os
from io import BytesIO

from PyPDF2.generic import NameObject
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Sum
from django.shortcuts import render, redirect, resolve_url, get_object_or_404
from django.contrib.auth import authenticate, logout, login
import base64
import PyPDF2
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import datetime
from django.core.files.uploadedfile import UploadedFile
from fpdf import FPDF
from .forms import DocumentForm, InvoiceForm
from .models import Project, Proposal, Plan, PurchaseOrder, Contract, ChangeOrder, Draw, DeductiveChangeOrder, SWO, Exhibit, Invoice, Subcontractor




STATE_OPTIONS = [
    ("AL", "Alabama"),
    ("AK", "Alaska"),
    ("AZ", "Arizona"),
    ("AR", "Arkansas"),
    ("CA", "California"),
    ("CO", "Colorado"),
    ("CT", "Connecticut"),
    ("DE", "Delaware"),
    ("FL", "Florida"),
    ("GA", "Georgia"),
    ("HI", "Hawaii"),
    ("ID", "Idaho"),
    ("IL", "Illinois"),
    ("IN", "Indiana"),
    ("IA", "Iowa"),
    ("KS", "Kansas"),
    ("KY", "Kentucky"),
    ("LA", "Louisiana"),
    ("ME", "Maine"),
    ("MD", "Maryland"),
    ("MA", "Massachusetts"),
    ("MI", "Michigan"),
    ("MN", "Minnesota"),
    ("MS", "Mississippi"),
    ("MO", "Missouri"),
    ("MT", "Montana"),
    ("NE", "Nebraska"),
    ("NV", "Nevada"),
    ("NH", "New Hampshire"),
    ("NJ", "New Jersey"),
    ("NM", "New Mexico"),
    ("NY", "New York"),
    ("NC", "North Carolina"),
    ("ND", "North Dakota"),
    ("OH", "Ohio"),
    ("OK", "Oklahoma"),
    ("OR", "Oregon"),
    ("PA", "Pennsylvania"),
    ("RI", "Rhode Island"),
    ("SC", "South Carolina"),
    ("SD", "South Dakota"),
    ("TN", "Tennessee"),
    ("TX", "Texas"),
    ("UT", "Utah"),
    ("VT", "Vermont"),
    ("VA", "Virginia"),
    ("WA", "Washington"),
    ("WV", "West Virginia"),
    ("WI", "Wisconsin"),
    ("WY", "Wyoming"),
]

STATUS_OPTIONS = [("I", "In Progress"), ("C", "Completed"), ("O", "On Hold")]

METHOD_OPTIONS = [("I", "Invoice"), ("E", "Exhibit"), ("P", "Purchase Order")]

LIEN_RELEASE_OPTIONS = [("F", "Final"), ("C", "Conditional"), ("N", "N/A")]


@ensure_csrf_cookie
def index(request):
    username = ""
    password = ""
    user = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            refresh = request.POST.get('refresh', None)
            if refresh:
                return redirect(request.path)
            else:
                redirect_url = request.POST.get('next', None)
                if redirect_url:
                    return redirect(resolve_url(redirect_url))
                else:
                    return redirect('reports:home')
        else:
            if (username == "" and password == ""):
                return render(request, 'reports/login.html', {'error_message': "Please input login credentials"})
            else:
                return render(request, 'reports/login.html',
                              {'error_message': "The provided credentials are incorrect"})
    else:
        return render(request, 'reports/login.html')


def log_out(request):
    logout(request)
    return render(request, 'reports/login.html')


@login_required(login_url='reports:login')
def input_data(request):
    return render(request, 'reports/input_data.html')


@login_required(login_url='reports:login')
def edit_sub(request, sub_id):
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        w9 = request.POST.get('w9')
        if not name:
            return render(request, 'reports/edit_sub.html', {'error_message': "Please enter the subcontractor name. (Less than 50 characters)", 'sub': sub})

        if not address and not phone and not email:
            return render(request, 'reports/all_subs.html', {'error_message': "Please enter at least one form of contact", 'sub': sub})

        sub.name = name
        sub.addresss = address
        sub.phone = phone
        sub.email = email
        sub.w9 = w9

        sub.save()

        return redirect('reports:all_subs')

    return render(request, 'reports/edit_sub.html', {'sub': sub})


@login_required(login_url='reports:login')
def delete_sub(request, sub_id):
    if request.method == 'POST':
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            sub = get_object_or_404(Subcontractor, pk=sub_id)
            sub.delete()
            print("Subcontractor deleted")
        else:
            print("Username incorrect")

    return redirect('reports:all_subs')


@login_required(login_url='reports:login')
def sub_select(request, project_id):
    subs = Subcontractor.objects.order_by("name")
    project = get_object_or_404(Project, pk=project_id)

    return render(request, 'reports/sub_select.html', {'subs': subs, 'project': project})

@login_required(login_url='reports:login')
def all_subs(request):
    subs = Subcontractor.objects.order_by("name")
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        w9 = request.POST.get('w9')

        context = {
            'subs': subs,
            'name': name,
            'address': address,
            'phone': phone,
            'email': email,
            'w9': w9
        }
        if not name:
            context.update({'error_message': "Please enter the subcontractor name. (Less than 50 characters)"})
            return render(request, 'reports/all_subs.html', context)

        if not address and not phone and not email:
            context.update({'error_message': "Please enter at least one form of contact"})
            return render(request, 'reports/all_subs.html', context)

        sub = Subcontractor()
        sub.name = name
        sub.address = address
        sub.phone = phone
        sub.email = email
        sub.w9 = w9
        sub.save()

        return redirect(reverse('reports:all_subs'))

    return render(request, 'reports/all_subs.html', {'subs': subs})


@login_required(login_url='reports:login')
def home(request):
    recent_projects = Project.objects.order_by('-date', '-status')[:5]
    context = {'recent_projects': recent_projects}
    return render(request, 'reports/home.html', context)


@login_required(login_url='reports:login')
def all(request):
    projects = Project.objects.order_by('-date', '-status')
    context = {'projects': projects}
    return render(request, 'reports/all_proj.html', context)


@login_required(login_url='reports:login')
def new_proj(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        date = datetime.now()
        edited_by = request.user.username
        status = "I"

        if not name or not address or not city or not state or not zip:
            return render(request, 'reports/new_proj.html', {'error_message': "Please fill out all fields",
                                                             'state_options': STATE_OPTIONS})

        if int(zip) < 10000 and zip != "":
            return render(request, 'reports/new_proj.html', {'error_message': "Zip code incorrect",
                                                             'state_options': STATE_OPTIONS})

        project = Project(name=name, date=date, edited_by=edited_by, status=status,
                           address=address, city=city, state=state, zip=zip)
        project.save()
        print("Project " + project.name + " has been saved")

        return redirect('reports:home')

    return render(request, 'reports/new_proj.html', {"state_options": STATE_OPTIONS})

@login_required(login_url='reports:login')
def new_exhibit(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)

    if request.method == 'POST':
        exhibit = create_exhibit(request.POST, project, sub)
        print(exhibit.pdf.path)
        return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)

    print("*********Didn't work :(**************")
    return render(request, 'reports/new_exhibit.html', {'project': project, 'sub': sub})

def check_space(self, required_height):
    if self.get_y() + required_height > self.page_break_trigger:
        self.add_page()

@login_required(login_url='reports:login')
def new_contract(request):
    projects = Project.objects.order_by('name')
    subs = Subcontractor.objects.order_by('name')

    context = {'projects': projects, 'subs': subs}

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
            return render(request, 'reports/new_contract.html', context)

        if listed_in_exhibit == listed_in_subcontract:
            context.update({'error_message': "Please fill out all fields as specified (sub/exhibit)"})
            return render(request, 'reports/new_contract.html', context)

        if (offsite_disposal + onsite_dumpster + onsite_dumpster_sub_pay) != 1:
            context.update({'error_message': "Please fill out all fields as specified (disposal)"})
            return render(request, 'reports/new_contract.html', context)

        if not project in projects or not sub in subs:
            context.update({'error_message': "Please pick an existing Project and Subcontractor"})
            return render(request, 'reports/new_contract.html', context)

        try:
            contract_total = float(contract_total)
            if contract_total < 0:
                raise
        except:
            context.update({'error_message': "Contract total must be a positive number"})
            return render(request, 'reports/new_contract.html', context)

        swo = SWO()
        swo.date = contract_date
        swo.total = contract_total
        swo.sub_id = sub
        swo.description = description[:196]+"..."
        swo.project_id = project

        file_path = os.path.join(settings.STATIC_ROOT, 'reports\pdf_templates\contract_template.pdf')

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
                print(fields)

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

        return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)

    return render(request, 'reports/new_contract.html', context)

def create_exhibit(POST, project, sub):
    print("************METHOD CALLED************")
    exhibits = Exhibit.objects.order_by("-date").filter(project_id=project).filter(sub_id=sub)

    exhibit = Exhibit()
    exhibit.name = "Exhibit " + chr(len(exhibits) + 65)
    exhibit.date = datetime.date.today()
    exhibit.sub_id = sub
    exhibit.project_id = project

    group_data = []
    total_total = 0.00

    for group_index, group in enumerate(POST.getlist('groupTitle[]')):
        print("**********Check 1***********")
        group_name = POST.getlist("groupTitle[]")[group_index]

        rows = []
        row_index = 0

        while f"scope[{group_index}][0]" in POST:
            print("***********Check 2**********")
            while f"scope[{group_index}][{row_index}]" in POST:
                print("***********Check 3**********")
                scope = POST.get(f"scope[{group_index}][{row_index}]")
                qty = POST.get(f"qty[{group_index}][{row_index}]")
                unit_price = POST.get(f"unitprice[{group_index}][{row_index}]")
                total_price = POST.get(f"totalprice[{group_index}][{row_index}]")

                rows.append({
                    'scope': scope,
                    'qty': qty,
                    'unit_price': unit_price,
                    'total_price': total_price
                })
                row_index += 1

            group_index += 1

        group_data.append({
            'group_name': group_name,
            'rows': rows
        })

    file_name = exhibit.name + " " + str(exhibit.date)

    if os.path.exists(file_name + ".pdf"):
        print("***********Check 4**********")
        counter = 1
        while os.path.exists(file_name + "(" + str(counter) + ")" + ".pdf"):
            counter += 1
        file_name += "(" + str(counter) + ")"

    file_name += ".pdf"

    pdf = FPDF()

    # Set up the PDF document
    pdf.set_title("Scope & Values - Exhibit")
    pdf.set_author("Moffat Construction")
    pdf.set_font("Arial", size=10)

    # Set margins (3/4 inch margins)
    margin = 20
    pdf.set_auto_page_break(auto=True, margin=margin)

    # Add a new page
    pdf.add_page()

    # Add image at the top center
    pdf.image(os.path.join(settings.STATIC_ROOT, 'reports\images\logo_onlyM.png'),
              x=(pdf.w - 20) / 2, y=10, w=20, h=20)
    pdf.ln(23)

    pdf.set_font("Arial", style="B", size=10)
    pdf.set_line_width(.75)
    pdf.cell(pdf.w - 20, 5, f"SCOPE & VALUES - EXHIBIT {chr(len(exhibits) + 65)}", 1, 0, align="C")
    pdf.ln(10)
    x = (pdf.w - (pdf.w / 3)) / 2

    pdf.set_font("Arial", size=10)

    # Define table data
    table_data = [
        ["MOFFAT CONSTRUCTION", "Contract No.:"],
        ["a Moffat Company", "Contract Date:"],
        ["519 W. STATE STREET SUITE #202", "Subproject:"],
        ["PLEASANT GROVE, UTAH 84062", ""]
    ]

    # Set column widths
    col_width = pdf.w / 3

    # Calculate total table width
    table_width = col_width * 2

    # Calculate x position to center the table
    x = (pdf.w - table_width) / 2
    pdf.set_line_width(.25)
    # Loop through rows and columns to create table
    for row in table_data:
        print("***********Check 5**********")
        for col, cell_data in enumerate(row):
            # Apply formatting for "a Moffat Company" cell
            if "a Moffat Company" in cell_data:
                pdf.set_font("Arial", style="I", size=10)
                pdf.set_text_color(255, 0, 0)

            # Add cell without borders
            pdf.set_xy(x + (col * col_width), pdf.get_y())
            pdf.cell(col_width, 5, cell_data, 0, 0, "C")

            # Reset font and text color
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    # Add gap
    pdf.ln(3)

    table_data = [
        ["Trade:", "Schedule"],
        [sub.name, "Start Date:"],
        [sub.address, "End Date:                                         Duration:"],
        ["Project: " + project.name, "Start Date Punch List Fixes:"],
        ["Address: " + project.address, "End Date Punch List Fixes:              Duration:"],
        ["City, State, Zip: " + project.city + ", " + project.state + ", " + str(project.zip),
         "Final Sign Off:"]
    ]

    # Set column widths
    col_width = pdf.w / 2 - 10

    # Calculate total table width
    table_width = col_width * 2

    # Calculate x position to center the table
    x = (pdf.w - table_width) / 2

    # Loop through rows and columns to create table
    for row in table_data:
        print("***********Check 6**********")
        for col, cell_data in enumerate(row):
            if col == 0 and sub.name in cell_data or sub.address in cell_data or "Schedule" in cell_data:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.set_font("Arial", style="B", size=10)
                pdf.cell(col_width, 5, cell_data, 1, 0, "C")
            else:
                # Add cell without borders
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 5, cell_data, 1, 0, "L")

            # Reset font and text color
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    pdf.ln(3)

    # Add cell with light gray background
    pdf.set_fill_color(192)
    pdf.cell(pdf.w - 20, 5, "SCOPE & VALUES", 1, 1, "C", True)

    # Add gap
    pdf.ln(3)

    for group in group_data:
        print("***********Check 7**********")
        group_subtotal = 0.00
        pdf.set_fill_color(217, 225, 242)
        pdf.set_font('Arial', style='B', size=10)
        pdf.cell(pdf.w - 20, 5, group['group_name'], 1, 1, "C", True)

        pdf.set_fill_color(255)
        pdf.set_font('Arial', size=10)
        pdf.cell((pdf.w - 20) * .075, 5, 'No.', 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .475, 5, 'Scope of Work', 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .15, 5, 'Unit Price', 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .1, 5, 'Qty', 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .2, 5, 'Total', 1, 1, 'C', True)

        # Iterate over rows for the current group
        for index, row in enumerate(group['rows']):
            scope = row['scope']
            qty = row['qty']
            unit_price = row['unit_price']
            total_price = row['total_price']

            pdf.set_fill_color(255 if index % 2 == 0 else 240)
            pdf.set_font('Arial', size=10)
            pdf.cell((pdf.w - 20) * .075, 5, str(index + 1), 1, 0, 'C', True)
            pdf.cell((pdf.w - 20) * .475, 5, scope, 1, 0, 'L', True)
            pdf.cell((pdf.w - 20) * .15, 5, "$" + unit_price, 1, 0, 'L', True)
            pdf.cell((pdf.w - 20) * .1, 5, qty, 1, 0, 'C', True)
            pdf.cell((pdf.w - 20) * .2, 5, "$" + total_price, 1, 1, 'L', True)
            group_subtotal += float(total_price[0:])

        # Add a break after each group
        pdf.set_fill_color(217, 225, 242)
        pdf.set_font('Arial', style='B', size=10)
        pdf.cell((pdf.w - 20) * .8, 5, group_name + " Subtotal: ", 1, 0, 'R', True)
        pdf.cell((pdf.w - 20) * .2, 5, " $" + str(group_subtotal), 1, 1, 'L', True)
        total_total += group_subtotal
        pdf.ln(5)

    # Add table with two columns and eight rows for signatures

    pdf.set_fill_color(192)
    pdf.set_font('Arial', style='B', size=10)
    pdf.cell((pdf.w - 20) * .8, 5, group_name + " Total Contracted Amount: ", 1, 0, 'R', True)
    pdf.cell((pdf.w - 20) * .2, 5, " $" + str(total_total), 1, 1, 'L', True)

    pdf.ln(15)

    if pdf.get_y() + 65 > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_fill_color(255)
    pdf.cell(pdf.w - 20, 5, "Signatures", 1, 1, "C", True)

    table_data = [
        ["Moffat Construction", sub.name],
        ["Signature", "Signature"],
        ["Date", "Date"],
        ["Printed Name", "Printed Name"],
        ["Greg Moffat", ""],
        ["Title/Position", "Title/Position"],
        ["", ""]
    ]

    # Loop through rows and columns to create table
    for row in table_data:
        for col, cell_data in enumerate(row):
            if table_data.index(row) == 0:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.set_font("Arial", size=8)
                pdf.cell(col_width, 5, cell_data, 1, 0, "C")
            elif "Signature" in cell_data:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.set_font("Arial", size=8)
                pdf.cell(col_width, 12, cell_data + " \n\n\n\n\n\n\n", 1, 0, "L")
            elif cell_data == "" or cell_data == "Greg Moffat":
                pdf.set_font("Arial", size=12)
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 12, cell_data, 1, 0, "C")
            else:
                # Add cell without borders
                pdf.set_font("Arial", size=8)
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 5, cell_data, 1, 0, "L")

            # Reset font and text color
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    exhibit.total = total_total

    # Generate the full file path
    ex_file_path = os.path.join(settings.STATIC_ROOT, file_name)
    pdf.output(ex_file_path)
    with open(ex_file_path, 'rb') as file:
        file_content = file.read()

    file_data = ContentFile(file_content)

    exhibit.pdf.save(file_name, file_data)
    print(exhibit.pdf.path)

    # Delete the temporary file
    os.remove(ex_file_path)

    project.date = datetime.now()
    project.save()
    exhibit.save()
    print("***********Check Final**********")
    return exhibit


@login_required(login_url='reports:login')
def new_invoice(request, project_id, draw_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    subs = Subcontractor.objects.order_by('name')
    invoice_form = InvoiceForm(request.POST, request.FILES)

    context = {
        'subs': subs,
        'project': project,
        'form': invoice_form,
        'draw': draw,
        'method_choices': METHOD_OPTIONS,
        'lien_release_type_choices': LIEN_RELEASE_OPTIONS
    }

    if request.method == 'POST':
        invoice_date = request.POST.get('invoice_date')
        invoice_num = request.POST.get('invoice_num')
        division_code = request.POST.get('division_code')
        method = request.POST.get('method')
        sub_name = request.POST.get('sub')
        sub = get_object_or_404(Subcontractor, name=sub_name)

        invoice_total = request.POST.get('invoice_total')

        description = request.POST.get('description')
        lien_release_type = request.POST.get('lien_release_type')
        w9 = sub.w9
        signed = bool(request.POST.get('signed', False))

        context.update({
            'invoice_date': invoice_date,
            'invoice_num': invoice_num,
            'division_code': division_code,
            'methodselect': method,
            'subselect': sub,
            'invoice_total': invoice_total,
            'lrtypeselect': lien_release_type,
            'description': description
        })

        if not invoice_date or not invoice_num or not division_code or not method or not sub or not invoice_total or not description or not lien_release_type:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'reports/new_invoice.html', context)

        if invoice_form.is_valid():
            invoice = Invoice()
            invoice.draw_id = draw
            invoice.invoice_date = invoice_date
            invoice.invoice_num = invoice_num
            invoice.division_code = division_code
            invoice.method = method
            invoice.sub_id = sub
            invoice.invoice_total = invoice_total
            invoice.description = description
            invoice.lien_release_type = lien_release_type
            invoice.w9 = w9
            invoice.signed = signed

            # Handle invoice PDF
            if 'invoice_pdf' in request.FILES:
                invoice.invoice_pdf = request.FILES['invoice_pdf']
                if not invoice.invoice_pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the Invoice PDF"})
                    return render(request, 'reports/new_invoice.html', context)

            # Handle lien release PDF
            if 'lien_release_pdf' in request.FILES:
                invoice.lien_release_pdf = request.FILES['lien_release_pdf']
                if not invoice.lien_release_pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                    return render(request, 'reports/new_invoice.html', context)

            else:
                invoice.signed = False;

            # Save invoice and related objects
            project.edited_by = request.user.username
            project.date = datetime.now()
            project.save()

            draw.edited_by = request.user.username
            draw.date = datetime.now()
            draw.save()

            invoice.save()

            return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page
        else:
            print(invoice_form.errors)
            context.update({'error_message': "File upload failed"})
            return render(request, 'reports/new_invoice.html', context)

    return render(request, 'reports/new_invoice.html', context)


@login_required(login_url='reports:login')
def new_draw(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    project.date = datetime.now()
    project.edited_by = request.user.username

    cur_draw = Draw(date=datetime.now(), project_id=project, edited_by=request.user.username)

    cur_draw.save()
    project.save()

    return redirect('reports:all_draws', project_id=project_id)


@login_required(login_url='reports:login')
def todo(request):
    invoices = Invoice.objects.order_by("-invoice_date").filter(signed=False)

    context = {
        'invoices': invoices
    }

    return render(request, 'reports/todo.html', context)



@login_required(login_url='reports:login')
def add_signature(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    draw = get_object_or_404(Draw, pk=invoice.draw_id.id)
    project = get_object_or_404(Project, pk=draw.project_id.id)

    return edit_invoice(request, project.id, draw.id, invoice_id)

@login_required(login_url='reports:login')
def all_draws(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    draws = Draw.objects.order_by('-date').filter(project_id=project.id)

    context = {'draws': draws, 'project': project}

    return render(request, 'reports/all_draws.html', context)


@login_required(login_url='reports:login')
def edit_proj(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        state = request.POST.get('state')
        zip = request.POST.get('zip')
        status = request.POST.get('status')
        date = datetime.now()
        edited_by = request.user.username

        if not name or not address or not city or not state or not zip:
            return render(request, 'reports/edit_project.html', {'error_message': "Please fill out all fields",
                                                                 'state_options': STATE_OPTIONS,
                                                                 'status_options': STATUS_OPTIONS})

        if int(zip) < 10000 and zip != "":
            return render(request, 'reports/edit_project.html', {'error_message': "Zip code incorrect",
                                                                 'state_options': STATE_OPTIONS,
                                                                 'status_options': STATUS_OPTIONS})

        project.name = name
        project.address = address
        project.city = city
        project.state = state
        project.zip = zip
        project.status = status
        project.date = date
        project.edited_by = edited_by
        project.save()

        return redirect('reports:home')

    project.address = [x.strip() for x in project.address.split(',')]
    return render(request, 'reports/edit_project.html', {'project': project,
                                                         'state_options': STATE_OPTIONS,
                                                         'status_options': STATUS_OPTIONS})


@login_required(login_url='reports:login')
def delete_proj(request, project_id):
    if request.method == 'POST':
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            project = get_object_or_404(Project, pk=project_id)
            project.delete()
            print("Project deleted")
        else:
            print("Username incorrect")

    return redirect('reports:home')


@login_required(login_url='reports:login')
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

    return redirect('reports:all_draws', project_id=project_id)


@login_required(login_url='reports:login')
def project_view(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, 'reports/project_view.html', {'project': project})


@login_required(login_url='reports:login')
def all_plans(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    form = DocumentForm(request.POST, request.FILES)

    plans = Plan.objects.order_by('-date').filter(project_id=project.id)

    context = {'plans': plans, 'project': project, 'form': form}

    return render(request, 'reports/all_plans.html', context)


@login_required(login_url='reports:login')
def upload_plan(request, project_id):
    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file: UploadedFile = request.FILES['pdf']
            if uploaded_file.content_type != 'application/pdf':
                return render(request, 'reports/all_plans.html', {'project': get_object_or_404(Project, pk=project_id), 'form': form, 'error_message': "Only PDF's allowed."})

            plan = form.save(commit=False)
            name = request.POST.get('name')
            if not name:
                return render(request, 'reports/all_plans.html',
                              {'project': get_object_or_404(Project, pk=project_id), 'form': form,
                               'error_message': "Please enter a name for the plan."})

            plan.name = name;
            plan.edited_by = request.user.username
            plan.date = datetime.now()
            plan.project_id = get_object_or_404(Project, pk=project_id)
            plan.save()
            form.save_m2m()

            return redirect('reports:all_plans', project_id=project_id)
        else:
            return render(request, 'reports/all_plans.html', {'project': get_object_or_404(Project, pk=project_id), 'form': form, 'error_message': "File upload failed."})
    else:
        form = DocumentForm()

    return render(request, 'reports/all_plans.html', {'project': get_object_or_404(Project, pk=project_id), 'form': form})


@login_required(login_url='reports:login')
def delete_plan(request, project_id):
    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        print("Attempting to delete plan "+ plan_id)
        # Delete the PDF file from storage
        document = get_object_or_404(Plan, pk=plan_id)
        file_path = document.pdf.path
        if os.path.exists(file_path):
            os.remove(file_path)
            document.delete()
            print("Plan deleted")

        return redirect('reports:all_plans', project_id=project_id)  # Redirect to a success page

    return render(request, 'reports/all_plans.html', {'error_message': "Document could not be deleted."})


@login_required(login_url='reports:login')
def edit_invoice(request, project_id, draw_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    subs = Subcontractor.objects.order_by('name')

    context = {
        'subs': subs,
        'project': project,
        'invoice': invoice,
        'draw': draw,
        'method_choices': METHOD_OPTIONS,
        'lien_release_type_choices': LIEN_RELEASE_OPTIONS
    }

    if request.method == 'POST':
        invoice_date = request.POST.get('invoice_date')
        invoice_num = request.POST.get('invoice_num')
        division_code = request.POST.get('division_code')
        method = request.POST.get('method')
        sub_name = request.POST.get('sub')
        sub = get_object_or_404(Subcontractor, name=sub_name)
        invoice_total = request.POST.get('invoice_total')
        description = request.POST.get('description')
        lien_release_type = request.POST.get('lien_release_type')
        w9 = request.POST.get('w9')
        signed = bool(request.POST.get('signed', False))

        if not invoice_date or not invoice_num or not division_code or not method or not sub or not invoice_total or not description or not lien_release_type or not w9:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'reports/edit_invoice.html', context)

        invoice.invoice_date = invoice_date
        invoice.invoice_num = invoice_num
        invoice.division_code = division_code
        invoice.method = method
        invoice.sub = sub
        invoice.invoice_total = invoice_total
        invoice.description = description
        invoice.lien_release_type = lien_release_type
        invoice.w9 = w9
        invoice.signed = signed

        # Handle invoice PDF
        if 'invoice_pdf' in request.FILES:
            invoice.invoice_pdf = request.FILES['invoice_pdf']
            if not invoice.invoice_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Invoice PDF"})
                return render(request, 'reports/edit_invoice.html', context)

        # Handle lien release PDF
        if 'lien_release_pdf' in request.FILES:
            invoice.lien_release_pdf = request.FILES['lien_release_pdf']
            if not invoice.lien_release_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'reports/edit_invoice.html', context)

        else:
            invoice.signed = None

        # Save invoice and related objects
        project.edited_by = request.user.username
        project.date = datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.now()
        draw.save()

        invoice.save()

        return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'reports/edit_invoice.html', context)

@login_required(login_url='reports:login')
def draw_view(request, project_id, draw_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    draws = Draw.objects.order_by('-date').filter(project_id=project.id)
    invoices = Invoice.objects.order_by('-invoice_date').order_by('sub_id').filter(draw_id=draw.id)

    total_invoice_amount = invoices.aggregate(total=Sum('invoice_total'))['total']

    return render(request, 'reports/draw_view.html', {'draw': draw, 'draws': draws, 'invoices': invoices, 'total_invoice_amount':total_invoice_amount,'project': project})


@login_required(login_url='reports:login')
def contract_pdf_view(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    pdf_bytes = contract.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/contract_pdf_view.html', {'pdf_data': pdf_data, 'contract': contract})

@login_required(login_url='reports:login')
def prop_pdf_view(request, prop_id):
    prop = get_object_or_404(Proposal, pk=prop_id)
    pdf_bytes = prop.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/prop_pdf_view.html', {'pdf_data': pdf_data, 'contract': prop})


@login_required(login_url='reports:login')
def swo_pdf_view(request, swo_id):
    swo = get_object_or_404(SWO, pk=swo_id)
    pdf_bytes = swo.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/contract_pdf_view.html', {'pdf_data': pdf_data, 'SWO': swo})


@login_required(login_url='reports:login')
def co_pdf_view(request, co_id):
    co = get_object_or_404(ChangeOrder, pk=co_id)
    pdf_bytes = co.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/contract_pdf_view.html', {'pdf_data': pdf_data, 'co': co})


@login_required(login_url='reports:login')
def dco_pdf_view(request, dco_id):
    dco = get_object_or_404(DeductiveChangeOrder, pk=dco_id)
    pdf_bytes = dco.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/contract_pdf_view.html', {'pdf_data': pdf_data, 'dco': dco})


@login_required(login_url='reports:login')
def exhibit_pdf_view(request, exhibit_id):
    exhibit = get_object_or_404(Exhibit, pk=exhibit_id)
    pdf_bytes = exhibit.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/exhibit_pdf_view.html', {'pdf_data': pdf_data, 'exhibit': exhibit})


@login_required(login_url='reports:login')
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
        if os.path.exists(exhibit.pdf.path):
            os.remove(exhibit.pdf.path)
            exhibit.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)

@login_required(login_url='reports:login')
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
            os.remove(contract.pdf.path)
            contract.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)

@login_required(login_url='reports:login')
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
            os.remove(swo.pdf.path)
            swo.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)


@login_required(login_url='reports:login')
def delete_prop(request, prop_id):
    prop = get_object_or_404(Proposal, pk=prop_id)
    project = prop.project_id
    sub = prop.sub_id
    project.edited_by = request.user.username
    project.date = datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(prop.pdf.path):
            os.remove(prop.pdf.path)
            prop.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)




@login_required(login_url='reports:login')
def plan_view(request, plan_id, project_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    pdf_bytes = plan.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/plan_view.html', {'pdf_data': pdf_data, 'plan': plan})



@login_required(login_url='reports:login')
def delete_invoice(request, project_id, draw_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    invoice = get_object_or_404(Invoice, pk=invoice_id)

    if request.method == 'POST':
        print("Attempting to delete invoice")
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            # Delete the PDF file from storage
            if invoice.invoice_pdf:
                if os.path.exists(invoice.invoice_pdf.path):
                    os.remove(invoice.invoice_pdf.path)
                    invoice.invoice_pdf.delete()
            if invoice.lien_release_pdf:
                if os.path.exists(invoice.lien_release_pdf.path):
                    os.remove(invoice.lien_release_pdf.path)
                    invoice.lien_release_pdf.delete()

            invoice.delete()
        return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'reports/draw_view.html', {'project': project, 'draw':draw, 'error_message': "Document could not be deleted."})

    project.date = datetime.now()
    draw.date = datetime.now()


@login_required(login_url='reports:login')
def purchase_orders(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    if request.method == 'POST':
        pass

    else:
        return render(request, 'reports/purchase_orders.html', {'project': project, 'sub': sub})

@login_required(login_url='reports:login')
def new_purchase_order(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    if request.method == 'POST':
        pass
    else:
        return render(request, 'reports/new_purchase_order.html', {'project': project, 'sub': sub})


@login_required(login_url='reports:login')
def deductive_change_orders(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    dcos = DeductiveChangeOrder.objects.order_by('-date').filter(project_id=project).filter(sub_id=sub)

    return render(request, 'reports/deductive_change_orders.html', {'project': project, 'sub': sub, 'dcos': dcos})


@login_required(login_url='reports:login')
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
        'contracts_data': contracts_data,  # Pass the serialized contracts data to the template
    }

    if request.method == 'POST':
        contract = get_object_or_404(Contract, pk=request.POST.get('contract'))
        project = get_object_or_404(Project, pk=contract.project_id.id)
        sub = get_object_or_404(Subcontractor, pk=contract.sub_id.id)
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
                totalprice_key = f'totalprice{scope_index}'

                qty_value = request.POST.get(qty_key)
                unitprice_value = request.POST.get(unitprice_key)
                totalprice_value = float(qty_value) * float(unitprice_value)

                if scope_value == "" or float(qty_value) <= 0 or float(unitprice_value) <= 0:
                    context.update({'error_message': "All fields need to be filled."})
                    return render(request, 'reports/new_change_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'reports/new_change_order.html', context)

                # Create a dictionary for the change order data
                co_data = {
                    'scope_value': scope_value,
                    'qty_value': qty_value,
                    'unitprice_value': unitprice_value,
                    'totalprice_value': totalprice_value,
                }

                rows.append(co_data)

        co = create_change_order(request.POST, "Deductive Change Order", rows)

        return redirect('reports:deductive_change_orders', project_id=project.id, sub_id=sub.id)

    return render(request, 'reports/new_deductive_change_order.html', context)


@login_required(login_url='reports:login')
def change_orders(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    cos = ChangeOrder.objects.order_by('-date').filter(project_id=project).filter(sub_id=sub)

    return render(request, 'reports/change_orders.html', {'project': project, 'sub': sub, 'cos': cos})


@login_required(login_url='reports:login')
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
                    return render(request, 'reports/new_change_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'reports/new_change_order.html', context)

                # Create a dictionary for the change order data
                co_data = {
                    'scope_value': scope_value,
                    'qty_value': qty_value,
                    'unitprice_value': unitprice_value,
                    'totalprice_value': totalprice_value,
                }

                rows.append(co_data)

        co = create_change_order(request.POST, "Change Order", rows)

        return redirect('reports:change_orders', project_id=project.id, sub_id=sub.id)

    return render(request, 'reports/new_change_order.html', context)


@login_required(login_url='reports:login')
def delete_change_order(request, co_id):
    co = get_object_or_404(ChangeOrder, pk=co_id)

    file_path = co.pdf.path
    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(file_path):
            os.remove(file_path)
            co.delete()

    return redirect('reports:change_orders', project_id=get_object_or_404(Project, pk=co.project_id), sub_id=get_object_or_404(Subcontractor, pk=co.sub_id))

@login_required(login_url='reports:login')
def delete_deductive_change_order(request, dco_id):
    dco = get_object_or_404(DeductiveChangeOrder, pk=dco_id)

    file_path = dco.pdf.path
    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(file_path):
            os.remove(file_path)
            dco.delete()

    return redirect('reports:deductive_change_orders')



def create_change_order(POST, type, rows):
    contract = get_object_or_404(Contract, pk=POST.get('contract'))
    project = contract.project_id
    sub = contract.sub_id

    file_name = project.name + " " + sub.name + " " + type + " " + str(datetime.now().strftime("%B-%d-%Y"))

    if os.path.exists(file_name + ".pdf"):
        print("***********Check 4**********")
        counter = 1
        while os.path.exists(file_name + "(" + str(counter) + ")" + ".pdf"):
            counter += 1
        file_name += "(" + str(counter) + ")"

    file_name += ".pdf"
    abrv = ""
    for word in project.name.split():
        abrv += word[0].upper()

    obj = None
    if type == "Deductive Change Order":
        dco = DeductiveChangeOrder()
        dco.project_id = project
        dco.sub_id = sub
        dco.date = datetime.now()
        dco.order_number = abrv + " DCO " + str(datetime.now().strftime("%y")) + str(
            "{:03d}".format(len(DeductiveChangeOrder.objects.all()) + 1))
        obj = dco

    elif type == "Change Order":
        co = ChangeOrder()
        co.project_id = project
        co.sub_id = sub
        co.date = datetime.now()
        co.order_number = abrv + " CO " + str(datetime.now().strftime("%y")) + str(
            "{:03d}".format(len(DeductiveChangeOrder.objects.all()) + 1))
        obj = co

    pdf = FPDF()

    # Set up the PDF document
    pdf.set_title(project.name + " " + sub.name + " " + type + " " + str(datetime.now().strftime("%B-%d-%Y")))
    pdf.set_author("Moffat Construction")
    pdf.set_font("Arial", size=10)

    # Set margins (3/4 inch margins)
    margin = 20
    pdf.set_auto_page_break(auto=True, margin=margin)

    # Add a new page
    pdf.add_page()

    # Add image at the top center
    pdf.image(os.path.join(settings.STATIC_ROOT, 'reports\images\logo_onlyM.png'),
              x=(pdf.w - 20) / 2, y=10, w=20, h=20)
    pdf.ln(23)

    pdf.set_font("Arial", style="B", size=16)
    pdf.set_line_width(.75)
    pdf.cell(pdf.w - 20, 10, type.upper()+" SUBCONTRACTOR", 1, 0, align="C")
    pdf.ln(15)

    pdf.set_font("Arial", size=10)

    # Define table data
    table_data = [
        [type + " No.", obj.order_number],
        ["Date", str(datetime.now().strftime("%B-%d-%Y"))],
    ]

    # Set column widths
    col_width = pdf.w / 4

    # Calculate x position to center the table
    x = 10
    pdf.set_line_width(.25)
    # Loop through rows and columns to create table
    for row in table_data:
        print("***********Check 5**********")
        for col, cell_data in enumerate(row):
            # Apply formatting for "a Moffat Company" cell
            if "a Moffat Company" in cell_data:
                pdf.set_font("Arial", style="I", size=10)
                pdf.set_text_color(255, 0, 0)

            # Add cell without borders
            pdf.set_xy(x + (col * col_width), pdf.get_y())
            pdf.cell(col_width, 5, cell_data, 1, 0, "L")

            # Reset font and text color
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    # Add gap
    pdf.ln(3)

    table_data = [
        ["General Contractor:", "Moffat Construction"],
        ["Trade:", ""],
        ["Subcontractor:", sub.name],
        ["Project: ", project.name],
        ["Address: ", project.address],
        ["City, State, Zip: ", project.city + ", " + project.state + ", " + str(project.zip)]
    ]

    # Loop through rows and columns to create table
    for row in table_data:
        for col, cell_data in enumerate(row):
            if col == 0 and sub.name in cell_data or sub.address in cell_data or "Schedule" in cell_data:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.set_font("Arial", style="B", size=10)
                pdf.cell(col_width, 5, cell_data, 1, 0, "C")
            else:
                # Add cell without borders
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 5, cell_data, 1, 0, "L")

            # Reset font and text color
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    pdf.ln(3)

    # Add cell with light gray background
    pdf.set_fill_color(192)
    pdf.cell((pdf.w-20)*.8, 5, "ORIGINAL CONTRACT AMOUNT", 1, 0, "C", True)
    pdf.cell((pdf.w-20)*.2, 5, "$"+"{:.2f}".format(contract.total), 1, 0, "C", True)


    # Add gap
    pdf.ln(8)

    pdf.cell(pdf.w - 20, 5, "SCOPE & VALUES" if type == "Change Order" else "SCOPE & VALUES REDUCED", 1, 0, "C", True)

    pdf.ln(5)

    pdf.set_fill_color(255)
    pdf.set_font('Arial', size=10)
    pdf.cell((pdf.w - 20) * .075, 5, 'No.', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .475, 5, 'Scope of Work', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .15, 5, 'Unit Price', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .1, 5, 'Qty', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .2, 5, 'Total', 1, 1, 'C', True)

    subtotal = 0.00
    # Iterate over rows for the current group
    for index, row in enumerate(rows):
        print(row)
        scope = row['scope_value']
        qty = row['qty_value']
        unit_price = row['unitprice_value']
        total_price = row['totalprice_value']

        pdf.set_fill_color(255 if index % 2 == 0 else 240)
        pdf.set_font('Arial', size=10)
        pdf.cell((pdf.w - 20) * .075, 5, str(index + 1), 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .475, 5, scope, 1, 0, 'L', True)
        pdf.cell((pdf.w - 20) * .15, 5, " $" + "{:.2f}".format(unit_price), 1, 0, 'L', True)
        pdf.cell((pdf.w - 20) * .1, 5, str(qty), 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .2, 5, " $" + "{:.2f}".format(total_price), 1, 1, 'L', True)
        subtotal += total_price

    # Add a break after each group
    pdf.set_fill_color(217, 225, 242)
    pdf.set_font('Arial', style='B', size=10)
    pdf.cell((pdf.w - 20) * .8, 5, type.upper() + " AMOUNT: ", 1, 0, 'R', True)
    pdf.cell((pdf.w - 20) * .2, 5, " $" + "{:.2f}".format(subtotal), 1, 1, 'L', True)
    pdf.ln(5)

    # Add table with two columns and eight rows for signatures

    pdf.set_fill_color(192)
    pdf.set_font('Arial', style='B', size=10)
    pdf.set_xy(pdf.w*.5 + 10, pdf.get_y())
    pdf.cell((pdf.w - 20) * .25, 5, "NEW CONTRACT AMOUNT", 1, 0, 'C', True)
    if type == "Change Order":
        pdf.cell((pdf.w - 20) * .2, 5, " $" + "{:.2f}".format(contract.total + subtotal), 1, 1, 'L', True)
    elif type == "Deductive Change Order":
        pdf.cell((pdf.w - 20) * .2, 5, " $" + "{:.2f}".format(contract.total - subtotal), 1, 1, 'L', True)

    pdf.ln(15)

    obj.total = subtotal

    if pdf.get_y() + 65 > pdf.page_break_trigger:
        pdf.add_page()

    pdf.set_fill_color(255)
    pdf.cell(pdf.w - 20, 5, "Signatures", 1, 1, "C", True)

    table_data = [
        ["Moffat Construction", sub.name],
        ["Signature", "Signature"],
        ["Date", "Date"]
    ]

    col_width = (pdf.w - 20) / 2

    # Loop through rows and columns to create table
    for row in table_data:
        for col, cell_data in enumerate(row):
            if table_data.index(row) == 0:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.set_font("Arial", size=8)
                pdf.cell(col_width, 5, cell_data, 1, 0, "C")
            elif "Signature" in cell_data:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.set_font("Arial", size=8)
                pdf.cell(col_width, 12, cell_data + " \n\n\n\n\n\n\n", 1, 0, "L")
            elif cell_data == "" or cell_data == "Greg Moffat":
                pdf.set_font("Arial", size=12)
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 12, cell_data, 1, 0, "C")
            else:
                # Add cell without borders
                pdf.set_font("Arial", size=8)
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 5, cell_data, 1, 0, "L")

                # Reset font and text color
                pdf.set_font("Arial", size=10)
                pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    # Generate the full file path
    ex_file_path = os.path.join(settings.STATIC_ROOT, file_name)
    pdf.output(ex_file_path)
    with open(ex_file_path, 'rb') as file:
        file_content = file.read()

    file_data = ContentFile(file_content)

    obj.pdf.save(file_name, file_data)

    # Delete the temporary file
    os.remove(ex_file_path)

    project.date = datetime.now()
    project.save()
    obj.save()
    print("***********Check Final**********")
    return obj





@login_required(login_url='reports:login')
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
        print(form_type)
        if form_type == 'contract':
            contract = Contract()
            contract.date = datetime.now()
            contract.total = request.POST.get('total')
            contract.sub_id = sub
            contract.project_id = project
            contract.pdf = request.POST.get('contract_pdf')

            try:
                contract.total = float(contract.total)
                if contract.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'reports/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'reports/contract_view.html', context)

            if not contract.pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the PDF"})
                return render(request, 'reports/contract_view.html', context)

    return render(request, 'reports/contract_view.html', context)


@login_required(login_url='reports:login')
def invoice_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    pdf_bytes = invoice.invoice_pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/invoice_view.html', {'pdf_data': pdf_data, 'invoice': invoice})



