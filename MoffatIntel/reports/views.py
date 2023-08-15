import json
import os
import time
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
from .models import *




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

DIVISION_CHOICES = [
    ("1", "General Requirement"),
    ("2", "Site Works"),
    ("3", "Concrete"),
    ("4", "Masonry"),
    ("5", "Metals"),
    ("6", "Wood and Plastics"),
    ("7", "Thermal and Moisture Protection"),
    ("8", "Doors and Windows"),
    ("9", "Finishes"),
    ("10", "Specialties"),
    ("11", "Equipment"),
    ("12", "Furnishings"),
    ("13", "Special Construction"),
    ("14", "Conveying Systems"),
    ("15", "Mechanical/Plumbing"),
    ("16", "Electrical"),
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
def edit_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = get_object_or_404(Project, pk=estimate.project_id)
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
        category = request.POST.get('category')
        total = request.POST.get('total')

        if not date or not sub or not csi or not category or not total:
            context.update({'error_message': "Please enter the subcontractor name. (Less than 50 characters)"})
            return render(request, 'reports/edit_estimate.html', context)

        estimate.date = date
        estimate.sub_id = get_object_or_404(Subcontractor, pk=sub)
        estimate.csi = csi
        estimate.category = category
        estimate.total = total

        if 'pdf' in request.FILES:
            estimate.pdf = request.FILES['pdf']
            if not estimate.pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Invoice PDF"})
                return render(request, 'reports/edit_invoice.html', context)

        estimate.save()




@login_required(login_url='reports:login')
def edit_sub(request, sub_id):
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        w9 = request.POST.get('w9')
        csi = request.POST.get('csi')
        category = request.POST.get('category')

        context = {
            'sub': sub,
            'name': name,
            'address': address,
            'phone': phone,
            'email': email,
            'w9': w9,
            'csi': csi,
            'category': category,
        }

        if not name:
            context.update({'error_message': "Please enter the subcontractor name. (Less than 50 characters)"})
            return render(request, 'reports/edit_sub.html', context)

        if not address and not phone and not email:
            context.update({'error_message': "Please enter at least one form of contact"})
            return render(request, 'reports/edit_sub.html', context)

        if not csi:
            context.update({'error_message': "Select a CSI division"})
            return render(request, 'reports/edit_sub.html', context)

        if not category:
            context.update({'error_message': "Select a category"})
            return render(request, 'reports/edit_sub.html', context)

        sub.name = name
        sub.address = address
        sub.phone = phone
        sub.email = email
        sub.w9 = w9
        sub.csi = csi
        sub.category = category

        sub.save()

        return redirect('reports:all_subs')

    return render(request, 'reports/edit_sub.html', {'sub': sub})


@login_required(login_url='reports:login')
def edit_vendor(request, vendor_id):
    vendor = get_object_or_404(Vendor, pk=vendor_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        cname = request.POST.get('cname')
        cphone = request.POST.get('cphone')
        cemail = request.POST.get('cemail')
        if not name:
            return render(request, 'reports/edit_vendor.html', {'error_message': "Please enter the vendor name. (Less than 50 characters)", 'vendor': vendor})

        if not address and not cphone and not cemail:
            return render(request, 'reports/edit_vendor.html', {'error_message': "Please enter at least one form of contact", 'vendor': vendor})

        vendor.name = name
        vendor.addresss = address
        vendor.cname = cname
        vendor.cphone = cphone
        vendor.cemail = cemail

        vendor.save()

        return redirect('reports:all_vendors')

    return render(request, 'reports/edit_vendor.html', {'vendor': vendor})


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
def delete_vendor(request, vendor_id):
    if request.method == 'POST':
        username = request.POST.get('username')
        print("Attempting to delete")

        if username == request.user.username:
            vendor = get_object_or_404(Vendor, pk=vendor_id)
            vendor.delete()
            print("Vendor deleted")
        else:
            print("Username incorrect")

    return redirect('reports:all_vendors')

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
def all_vendors(request):
    vendors = Vendor.objects.order_by("name")
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('address')
        cname = request.POST.get('cname')
        cphone = request.POST.get('cphone')
        cemail = request.POST.get('cemail')

        context = {
            'vendors': vendors,
            'name': name,
            'address': address,
            'cname': cname,
            'cphone': cphone,
            'cemail': cemail,
        }
        if not name:
            context.update({'error_message': "Please enter the vendor name. (Less than 50 characters)"})
            return render(request, 'reports/all_vendors.html', context)

        if not address and not cname and not cphone and not cemail:
            context.update({'error_message': "Please enter at least one form of contact"})
            return render(request, 'reports/all_vendors.html', context)

        vendor = Vendor()
        vendor.name = name
        vendor.address = address
        vendor.cname = cname
        vendor.cphone = cphone
        vendor.cemail = cemail
        vendor.save()

        return redirect(reverse('reports:all_vendors'))

    return render(request, 'reports/all_vendors.html', {'vendors': vendors})

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
        date = datetime.datetime.now()
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

                project.date = datetime.datetime.now()
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
    exhibit.date = datetime.datetime.now().strftime('%Y-%m-%d')
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
    pdf.image(os.path.join(settings.BASE_DIR, 'reports\static\\reports\images\logo_onlyM.png'),
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
        ["General Contractor", ""]
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
    ex_file_path = os.path.join(settings.STATIC_ROOT, "exhibits", file_name)

    pdf.output(ex_file_path)
    with open(ex_file_path, 'rb') as file:
        file_content = file.read()

    file_data = ContentFile(file_content)

    exhibit.pdf.save(file_name, file_data)
    print(exhibit.pdf.path)

    # Delete the temporary file
    os.remove(ex_file_path)

    project.date = datetime.datetime.now()
    project.save()
    exhibit.save()
    print("***********Check Final**********")
    return exhibit


@login_required(login_url='reports:login')
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
            return render(request, 'reports/new_check.html', context)

        check = Check()
        check.date = datetime.datetime.now()
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
                return render(request, 'reports/new_check.html', context)

        # Handle lien release PDF
        if 'lien_release_pdf' in request.FILES:
            check.lien_release_pdf = request.FILES['lien_release_pdf']
            if not check.lien_release_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'reports/new_check.html', context)

        else:
            check.signed = False

        project.edited_by = request.user.username
        project.date = datetime.datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.datetime.now()
        draw.save()

        invoice.date = datetime.datetime.now()
        invoice.save()

        check.save()

        return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'reports/new_check.html', context)


@login_required(login_url='reports:login')
def new_invoice(request, project_id, draw_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    subs = Subcontractor.objects.order_by('name')

    context = {
        'subs': subs,
        'project': project,
        'draw': draw,
        'method_choices': METHOD_OPTIONS,
    }

    if request.method == 'POST':
        invoice_date = request.POST.get('invoice_date')
        invoice_num = request.POST.get('invoice_num')
        csi = request.POST.get('csi')
        category = request.POST.get('category')
        method = request.POST.get('method')
        sub_name = request.POST.get('sub')
        sub = get_object_or_404(Subcontractor, name=sub_name)
        invoice_total = request.POST.get('invoice_total')
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
            return render(request, 'reports/new_invoice.html', context)

        invoice = Invoice()
        invoice.draw_id = draw
        invoice.invoice_date = invoice_date
        invoice.invoice_num = invoice_num
        invoice.csi = csi
        invoice.category = category
        invoice.method = method
        invoice.sub_id = sub
        invoice.invoice_total = invoice_total
        invoice.description = description
        invoice.w9 = w9

        # Handle invoice PDF
        if 'invoice_pdf' in request.FILES:
            invoice.invoice_pdf = request.FILES['invoice_pdf']
            if not invoice.invoice_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Invoice PDF"})
                return render(request, 'reports/new_invoice.html', context)

        # Save invoice and related objects
        project.edited_by = request.user.username
        project.date = datetime.datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.datetime.now()
        draw.save()

        invoice.save()

        return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'reports/new_invoice.html', context)


@login_required(login_url='reports:login')
def new_draw(request, project_id):
    project = get_object_or_404(Project, pk=project_id)

    project.date = datetime.datetime.now()
    project.edited_by = request.user.username

    cur_draw = Draw(date=datetime.datetime.now(), project_id=project, edited_by=request.user.username)

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
    sub = get_object_or_404(Subcontractor, pk=invoice.sub_id.id)
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
        print("***********************")
        print(status)
        print("***********************")
        date = datetime.datetime.now()
        edited_by = request.user.username

        if not name or not address or not city or not state or not zip:
            return render(request, 'reports/edit_project.html', {'error_message': "Please fill out all fields",
                                                                 'project': project,
                                                                 'state_options': STATE_OPTIONS,
                                                                 'status_options': STATUS_OPTIONS})

        if (int(zip) < 0 or int(zip) > 99999) and zip != "":
            return render(request, 'reports/edit_project.html', {'error_message': "Zip code incorrect",
                                                                 'project': project,
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
def all_estimates(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    estimates = Estimate.objects.filter(project_id = project).order_by('csi')

    context = {
        'project': project,
        'estimates': estimates,
        'divisions': DIVISION_CHOICES,
    }

    return render(request, 'reports/all_estimates.html', context)


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
            plan.date = datetime.datetime.now()
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
            time.sleep(3)
            os.remove(file_path)
            document.delete()
            print("Plan deleted")

        return redirect('reports:all_plans', project_id=project_id)  # Redirect to a success page

    return render(request, 'reports/all_plans.html', {'error_message': "Document could not be deleted."})


@login_required(login_url='reports:login')
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
            return render(request, 'reports/edit_check.html', context)

        check.date = datetime.datetime.now()
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
                return render(request, 'reports/edit_check.html', context)

        # Handle lien release PDF
        if 'lien_release_pdf' in request.FILES:
            invoice.lien_release_pdf = request.FILES['lien_release_pdf']
            if not invoice.lien_release_pdf.file.content_type.startswith('application/pdf'):
                context.update({'error_message': "Only PDFs are allowed for the Lien Release PDF"})
                return render(request, 'reports/edit_check.html', context)

        else:
            check.signed = None

        # Save invoice and related objects
        project.edited_by = request.user.username
        project.date = datetime.datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.datetime.now()
        draw.save()

        invoice.date = datetime.datetime.now()

        check.save()

        return redirect('reports:draw_view', project_id=project.id, draw_id=draw.id)  # Redirect to a success page

    return render(request, 'reports/edit_check.html', context)
@login_required(login_url='reports:login')
def edit_invoice(request, project_id, draw_id, invoice_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    sub = get_object_or_404(Subcontractor, pk=invoice.sub_id.id)
    subs = Subcontractor.objects.order_by('name')

    context = {
        'subs': subs,
        'subselect': sub,
        'project': project,
        'invoice': invoice,
        'draw': draw,
        'method_choices': METHOD_OPTIONS,
    }

    if request.method == 'POST':
        invoice_date = request.POST.get('invoice_date')
        invoice_num = request.POST.get('invoice_num')
        csi = request.POST.get('csi')
        category = request.POST.get('category')
        method = request.POST.get('method')
        sub_name = request.POST.get('sub')
        sub = get_object_or_404(Subcontractor, name=sub_name)
        invoice_total = request.POST.get('invoice_total')
        description = request.POST.get('description')
        lien_release_type = request.POST.get('lien_release_type')

        if not invoice_date or not invoice_num or not csi or not category or not method or not sub or not invoice_total or not description:
            context.update({'error_message': "Please fill out all fields"})
            return render(request, 'reports/edit_invoice.html', context)

        invoice.invoice_date = invoice_date
        invoice.invoice_num = invoice_num
        invoice.csi = csi
        invoice.category = category
        invoice.category = category
        invoice.method = method
        invoice.sub = sub
        invoice.invoice_total = invoice_total
        invoice.description = description
        invoice.lien_release_type = lien_release_type
        invoice.w9 = sub.w9

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
        project.date = datetime.datetime.now()
        project.save()

        draw.edited_by = request.user.username
        draw.date = datetime.datetime.now()
        draw.save()

        invoice.save()

        return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'reports/edit_invoice.html', context)

@login_required(login_url='reports:login')
def draw_view(request, project_id, draw_id):
    project = get_object_or_404(Project, pk=project_id)
    draw = get_object_or_404(Draw, pk=draw_id)
    contracts = Contract.objects.order_by('-date').filter(project_id=project.id)
    draws = Draw.objects.order_by('-date').filter(project_id=project.id)
    invoices = Invoice.objects.order_by('-invoice_date').order_by('sub_id').filter(draw_id=draw.id)
    checks = Check.objects.order_by('-check_date').order_by('invoice_id')

    total_invoice_amount = invoices.aggregate(total=Sum('invoice_total'))['total']

    return render(request, 'reports/draw_view.html', {'draw': draw, 'draws': draws, 'invoices': invoices, 'total_invoice_amount':total_invoice_amount,'project': project, 'contracts': contracts, 'checks': checks})


@login_required(login_url='reports:login')
def contract_pdf_view(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    pdf_bytes = contract.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/contract_pdf_view.html', {'pdf_data': pdf_data, 'contract': contract})

@login_required(login_url='reports:login')
def estimate_pdf_view(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    pdf_bytes = estimate.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/estimate_pdf_view.html', {'pdf_data': pdf_data, 'estimate': estimate})


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
def po_pdf_view(request, po_id):
    po = get_object_or_404(PurchaseOrder, pk=po_id)
    pdf_bytes = po.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/contract_pdf_view.html', {'pdf_data': pdf_data, 'po': po})


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
    project.date = datetime.datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(exhibit.pdf.path):
            time.sleep(3)
            os.remove(exhibit.pdf.path)
            exhibit.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)

@login_required(login_url='reports:login')
def delete_contract(request, contract_id):
    contract = get_object_or_404(Contract, pk=contract_id)
    project = contract.project_id
    sub = contract.sub_id
    project.edited_by = request.user.username
    project.date = datetime.datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(contract.pdf.path):
            time.sleep(3)
            os.remove(contract.pdf.path)
            contract.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)

@login_required(login_url='reports:login')
def delete_swo(request, swo_id):
    swo = get_object_or_404(SWO, pk=swo_id)
    project = swo.project_id
    sub = swo.sub_id
    project.edited_by = request.user.username
    project.date = datetime.datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(swo.pdf.path):
            time.sleep(3)
            os.remove(swo.pdf.path)
            swo.delete()

    return redirect('reports:contract_view', project_id=project.id, sub_id=sub.id)


@login_required(login_url='reports:login')
def delete_estimate(request, estimate_id):
    estimate = get_object_or_404(Estimate, pk=estimate_id)
    project = estimate.project_id
    sub = estimate.sub_id
    project.edited_by = request.user.username
    project.date = datetime.datetime.now()
    project.save()

    username = request.POST.get('username')
    print("Attempting to delete")

    if username == request.user.username:
        if os.path.exists(estimate.pdf.path):
            time.sleep(3)
            os.remove(estimate.pdf.path)
            estimate.delete()

    return redirect('reports:all_estimates', project_id=project.id)


@login_required(login_url='reports:login')
def plan_view(request, plan_id, project_id):
    plan = get_object_or_404(Plan, pk=plan_id)
    pdf_bytes = plan.pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/plan_view.html', {'pdf_data': pdf_data, 'plan': plan})


@login_required(login_url='reports:login')
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

            project.date = datetime.datetime.now()
            draw.date = datetime.datetime.now()
            invoice.date = datetime.datetime.now()

            project.save()
            draw.save()
            invoice.save()
            check.delete()

        return redirect('reports:draw_view', project_id=project.id, draw_id=draw.id)  # Redirect to a success page

    return render(request, 'reports/draw_view.html', {'project': project, 'draw':draw, 'error_message': "Document could not be deleted."})


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
                    time.sleep(3)
                    os.remove(invoice.invoice_pdf.path)
                    invoice.invoice_pdf.delete()

            project.date = datetime.datetime.now()
            draw.date = datetime.datetime.now()
            project.save()
            draw.save()
            invoice.delete()
        return redirect('reports:draw_view', project_id=project_id, draw_id=draw_id)  # Redirect to a success page

    return render(request, 'reports/draw_view.html', {'project': project, 'draw':draw, 'error_message': "Document could not be deleted."})


@login_required(login_url='reports:login')
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
                    return render(request, 'reports/new_purchase_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'reports/new_purchase_order.html', context)

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

        return redirect('reports:purchase_orders', project_id=project.id)

    return render(request, 'reports/new_purchase_order.html', context)


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
                    return render(request, 'reports/new_deductive_change_order.html', context)

                try:
                    qty_value = int(qty_value)
                    unitprice_value = float(unitprice_value)
                    totalprice_value = float(totalprice_value)  # Convert totalprice to float
                except ValueError:
                    context.update({'error_message': "'Qty' and 'Unit Price' fields must be numbers."})
                    return render(request, 'reports/new_deductive_change_order.html', context)

                # Create a dictionary for the change order data
                co_data = {
                    'scope_value': scope_value,
                    'qty_value': qty_value,
                    'unitprice_value': unitprice_value,
                    'totalprice_value': totalprice_value,
                }

                rows.append(co_data)

        dco = create_change_order(request.POST, "Deductive Change Order", rows)

        return redirect('reports:deductive_change_orders', project_id=project.id, sub_id=sub.id)

    return render(request, 'reports/new_deductive_change_order.html', context)


@login_required(login_url='reports:login')
def change_orders(request, project_id, sub_id):
    project = get_object_or_404(Project, pk=project_id)
    sub = get_object_or_404(Subcontractor, pk=sub_id)
    cos = ChangeOrder.objects.order_by('-date').filter(project_id=project).filter(sub_id=sub)

    return render(request, 'reports/change_orders.html', {'project': project, 'sub': sub, 'cos': cos})


@login_required(login_url='reports:login')
def purchase_orders(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    pos = PurchaseOrder.objects.order_by('-date').order_by('vendor_id').filter(project_id=project)

    return render(request, 'reports/purchase_orders.html', {'project': project, 'pos': pos})


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
            time.sleep(3)
            os.remove(file_path)
            co.delete()

    return redirect('reports:change_orders', project_id=get_object_or_404(Project, pk=co.project_id), sub_id=get_object_or_404(Subcontractor, pk=co.sub_id))

@login_required(login_url='reports:login')
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

    return redirect('reports:deductive_change_orders', project.id, sub.id)

@login_required(login_url='reports:login')
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

    return redirect('reports:purchase_orders', project_id=project.id)


def create_purchase_order(project, vendor, rows):
    draws = Draw.objects.filter(project_id=project)
    file_name = project.name + " " + vendor.name + " " + str(datetime.datetime.now().strftime("%B-%d-%Y"))

    if os.path.exists(file_name + ".pdf"):
        counter = 1
        while os.path.exists(file_name + "(" + str(counter) + ")" + ".pdf"):
            counter += 1
        file_name += "(" + str(counter) + ")"

    file_name += ".pdf"
    abrv = ""
    for word in project.name.split():
        abrv += word[0].upper()

    pdf = FPDF()

    # Set up the PDF document
    pdf.set_title(project.name + " " + vendor.name + " " + str(datetime.datetime.now().strftime("%B-%d-%Y")))
    pdf.set_author("Moffat Construction")
    pdf.set_font("Arial", size=10)

    # Set margins (3/4 inch margins)
    margin = 20
    pdf.set_auto_page_break(auto=True, margin=margin)

    # Add a new page
    pdf.add_page()

    # Add image at the top center
    pdf.image(os.path.join(settings.BASE_DIR, 'reports\static\\reports\images\logo_onlyM.png'),
              x=(pdf.w - 20) / 2, y=10, w=20, h=20)
    pdf.ln(23)

    pdf.set_font("Arial", style="B", size=16)
    pdf.set_line_width(.75)
    pdf.cell(pdf.w - 20, 10, "PURCHASE ORDER", 1, 0, align="C")
    pdf.ln(15)

    pdf.set_font("Arial", size=10)

    # Define table data

    table_data = [
        ["MOFFAT CONSTRUCTION", ""],
        ["a Moffat Company", "          Purchase Order No.:   " + "PO" + str(datetime.datetime.now().strftime("%y")) + str(
        "{:03d}".format(len(PurchaseOrder.objects.all()) + 1))],
        ["519 W. STATE STREET SUITE #202", "          Date:   " + str(datetime.datetime.now().strftime("%B-%d-%Y"))],
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
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 5, cell_data, 0, 0, "C")
            elif col == 1:
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 5, cell_data, 0, 0, "L")
            else:
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
        ["BUYER", "SELLER"],
        ["Moffat Construction", "Vendor: " + vendor.name],
        ["Address: 519 West State St., Pleasant Grove, UT 84062", "Address: " + vendor.address],
        ["Email: g60moffat@gmail.com; william@moffatcompany.com", "Contact Name: " + vendor.cname],
        ["Phone: c. 804.851.0606 o. 801.769.0745", "Contact Phone: " + vendor.cphone],
        ["", "Contact Email: " + vendor.cemail]
    ]

    col_width = pdf.w / 2 - 10
    # Loop through rows and columns to create table
    for row in table_data:
        for col, cell_data in enumerate(row):
            if "SELLER" in cell_data or "BUYER" in cell_data:
                pdf.set_fill_color(211)
                pdf.set_font("Arial", style="B", size=10)
                pdf.cell(pdf.w / 2 - 10, 5, cell_data, 1, 0, "C")
            else:
                # Add cell without borders
                pdf.cell(pdf.w / 2 - 10, 5, cell_data, 1, 0, "L")

            # Reset font and text color
            pdf.set_font("Arial", size=9)
            pdf.set_fill_color(256)
            pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    pdf.ln(5)

    table_data = [
        ["DELIVER TO / WORK PERFORMED AT:", "SCHEDULE"],
        [
            "Project Name: " + project.name + "\nAddress: " + project.address + "\nCity, State, Zip: " + project.city + ", " + project.state + ", " + str(
                project.zip), "\n\n\n"],
    ]

    # Set initial position
    x = pdf.get_x()
    y = pdf.get_y()

    # Loop through rows and columns to create table
    for row in table_data:
        for col, cell_data in enumerate(row):
            if "DELIVER" in cell_data or "SCHEDULE" in cell_data:
                pdf.set_font("Arial", style="B", size=10)
                pdf.set_xy(x + (col * col_width), y)  # Set the position of the cell
                pdf.set_fill_color(211)
                pdf.multi_cell(col_width, 5, cell_data, 1, "C")
            else:
                # Add cell without borders
                pdf.set_xy(x + (col * col_width), y)  # Set the position of the cell
                pdf.multi_cell(col_width, 5, cell_data, 1, "L")

            # Reset font and text color
            pdf.set_font("Arial", size=10)
            pdf.set_text_color(0)
            pdf.set_fill_color(256)


        # Update the y-coordinate for the next row
        y += pdf.font_size + 1.5 # Adjust the value (2) as needed for spacing between rows


    # Add gap
    pdf.ln(8)
    pdf.set_fill_color(217, 225, 242)
    pdf.cell(pdf.w - 20, 5, "SCOPE OF WORK - MATERIALS", 1, 0, "C", True)
    pdf.set_fill_color(256)
    pdf.ln(5)

    pdf.set_font('Arial', size=10)
    pdf.multi_cell((pdf.w - 20), 5, "This document, including any plans and specifications, if any, and all attached hereto are made a part hereof,"
         " shall constitute the Agreement. All labor, transportation, delivery fees, equipment, industry standards shall"
         " apply in all aspects for the the Seller to perform for fulfillment of this Purchase Order.", 1, "L", True)
    pdf.ln(5)

    pdf.set_xy(pdf.w * .875 - 7.5, pdf.get_y())
    pdf.multi_cell((pdf.w - 20) * .125, 5, "Draw: " + str(len(draws)) + "\nDate: " + str(datetime.datetime.now().strftime("%m-%d-%Y")), 1, "L", True)
    pdf.cell((pdf.w - 20) * .05, 5, 'No.', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .45, 5, 'Scope of Work', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .1, 5, 'Qty', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .125, 5, 'Unit Price', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .15, 5, 'Total', 1, 0, 'C', True)
    pdf.cell((pdf.w - 20) * .125, 5, 'Earned Value', 1, 1, 'C', True)

    subtotal = 0.00
    # Iterate over rows for the current group
    for index, row in enumerate(rows):
        scope = row['scope_value']
        qty = row['qty_value']
        unit_price = row['unitprice_value']
        total_price = row['totalprice_value']

        pdf.set_fill_color(255 if index % 2 == 0 else 240)
        pdf.set_font('Arial', size=10)
        pdf.cell((pdf.w - 20) * .05, 5, str(index + 1), 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .45, 5, scope, 1, 0, 'L', True)
        pdf.cell((pdf.w - 20) * .1, 5, " $" + "{:.2f}".format(unit_price), 1, 0, 'L', True)
        pdf.cell((pdf.w - 20) * .125, 5, str(qty), 1, 0, 'C', True)
        pdf.cell((pdf.w - 20) * .15, 5, " $" + "{:.2f}".format(total_price), 1, 0, 'L', True)
        pdf.cell((pdf.w - 20) * .125, 5, "", 1, 1, 'C', True)
        subtotal += total_price

    pdf.set_fill_color(217, 225, 242)
    pdf.set_font('Arial', style='B', size=10)
    pdf.cell((pdf.w - 20) * .725, 5, "TOTAL PURCHASE ORDER AMOUNT: ", 1, 0, 'R', True)
    pdf.cell((pdf.w - 20) * .15, 5, " $" + "{:.2f}".format(subtotal), 1, 0, 'L', True)
    pdf.set_fill_color(242, 235, 23)
    pdf.cell((pdf.w - 20) * .125, 5, '', 1, 1, 'C', True)

    if pdf.get_y() + 65 > pdf.page_break_trigger:
        pdf.add_page()

    pdf.ln(15)

    pdf.set_fill_color(211)
    pdf.cell(pdf.w - 20, 5, "Signatures", 1, 1, "C", True)
    pdf.set_fill_color(256)
    table_data = [
        ["Moffat Construction", vendor.name],
        ["Signature:", "Signature:"],
        ["Print Name:          Gregory Moffat", "Print Name:"],
        ["Date:          " + str(datetime.datetime.now().strftime("%B-%d-%Y")), "Date: "]
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
            elif "Print Name" in cell_data:
                pdf.set_font("Arial", size=8)
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 12, cell_data, 1, 0, "L")
            else:
                # Add cell without borders
                pdf.set_font("Arial", size=8)
                pdf.set_xy(x + (col * col_width), pdf.get_y())
                pdf.cell(col_width, 8, cell_data, 1, 0, "L")

                # Reset font and text color
                pdf.set_font("Arial", size=10)
                pdf.set_text_color(0)

        # Move to next row
        pdf.ln()

    # Generate the full file path
    ex_file_path = os.path.join(settings.STATIC_ROOT, "purchase_orders", file_name)
    pdf.output(ex_file_path)
    with open(ex_file_path, 'rb') as file:
        file_content = file.read()

    file_data = ContentFile(file_content)

    po = PurchaseOrder()
    po.name = file_name
    po.order_number = "PO" + str(datetime.datetime.now().strftime("%y")) + str(
        "{:03d}".format(len(PurchaseOrder.objects.all()) + 1))
    po.date = datetime.datetime.now()
    po.vendor_id = vendor
    po.project_id = project
    po.pdf.save(file_name, file_data)
    po.total = subtotal

    # Delete the temporary file
    os.remove(ex_file_path)

    project.date = datetime.datetime.now()
    project.save()
    po.save()
    print("***********Check Final**********")
    return po



def create_change_order(POST, type, rows):
    contract = get_object_or_404(Contract, pk=POST.get('contract'))
    project = contract.project_id
    sub = contract.sub_id

    file_name = type + " " + str(datetime.datetime.now().strftime("%B-%d-%Y"))

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
        dco.date = datetime.datetime.now()
        dco.order_number = abrv + " DCO " + str(datetime.datetime.now().strftime("%y")) + str(
            "{:03d}".format(len(DeductiveChangeOrder.objects.all()) + 1))
        obj = dco

    elif type == "Change Order":
        co = ChangeOrder()
        co.project_id = project
        co.sub_id = sub
        co.date = datetime.datetime.now()
        co.order_number = abrv + " CO " + str(datetime.datetime.now().strftime("%y")) + str(
            "{:03d}".format(len(DeductiveChangeOrder.objects.all()) + 1))
        obj = co

    pdf = FPDF()

    # Set up the PDF document
    pdf.set_title(project.name + " " + sub.name + " " + type + " " + str(datetime.datetime.now().strftime("%B-%d-%Y")))
    pdf.set_author("Moffat Construction")
    pdf.set_font("Arial", size=10)

    # Set margins (3/4 inch margins)
    margin = 20
    pdf.set_auto_page_break(auto=True, margin=margin)

    # Add a new page
    pdf.add_page()

    # Add image at the top center
    pdf.image(os.path.join(settings.BASE_DIR, 'reports\static\\reports\images\logo_onlyM.png'),
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
        ["Date", str(datetime.datetime.now().strftime("%B-%d-%Y"))],
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
    ex_file_path = os.path.join(settings.STATIC_ROOT, "deductive_change_orders", file_name)
    pdf.output(ex_file_path)
    with open(ex_file_path, 'rb') as file:
        file_content = file.read()

    file_data = ContentFile(file_content)

    obj.pdf.save(file_name, file_data)

    # Delete the temporary file
    os.remove(ex_file_path)

    project.date = datetime.datetime.now()
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
        if form_type == 'swo':
            swo = SWO()
            swo.date = datetime.datetime.now()
            swo.total = request.POST.get('total')
            swo.sub_id = sub
            swo.project_id = project

            if 'swo_pdf' in request.FILES:
                swo.pdf = request.FILES['swo_pdf']
                if not swo.pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the SWO PDF"})
                    return render(request, 'reports/contract_view.html', context)

            try:
                swo.total = float(swo.total)
                if swo.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'reports/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'reports/contract_view.html', context)

            swo.save()
            return redirect('reports:contract_view', project_id, sub_id)

        if form_type == 'exhibit':
            exhibit = Exhibit()
            exhibit.date = datetime.datetime.now()
            exhibit.total = request.POST.get('total')
            exhibit.sub_id = sub
            exhibit.project_id = project

            if 'exhibit_pdf' in request.FILES:
                exhibit.pdf = request.FILES['exhibit_pdf']
                if not exhibit.pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the Exhibit PDF"})
                    return render(request, 'reports/contract_view.html', context)

            try:
                exhibit.total = float(exhibit.total)
                if exhibit.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'reports/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'reports/contract_view.html', context)

            exhibit.save()
            return redirect('reports:contract_view', project_id, sub_id)

        if form_type == 'contract':
            contract = Contract()
            contract.date = datetime.datetime.now()
            contract.total = request.POST.get('total')
            contract.sub_id = sub
            contract.project_id = project

            if 'contract_pdf' in request.FILES:
                contract.pdf = request.FILES['contract_pdf']
                if not contract.pdf.file.content_type.startswith('application/pdf'):
                    context.update({'error_message': "Only PDFs are allowed for the Contract PDF"})
                    return render(request, 'reports/contract_view.html', context)

            try:
                contract.total = float(contract.total)
                if contract.total <= 0:
                    context.update({'error_message': "Total must be a positive number and not 0"})
                    return render(request, 'reports/contract_view.html', context)
            except:
                context.update({'error_message': "Total must be a number"})
                return render(request, 'reports/contract_view.html', context)

            contract.save()
            return redirect('reports:contract_view', project_id, sub_id)

    return render(request, 'reports/contract_view.html', context)


@login_required(login_url='reports:login')
def invoice_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    pdf_bytes = invoice.invoice_pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/invoice_view.html', {'pdf_data': pdf_data, 'invoice': invoice})


@login_required(login_url='reports:login')
def check_view(request, check_id):
    check = get_object_or_404(Check, pk=check_id)
    pdf_bytes = check.check_pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/check_view.html', {'pdf_data': pdf_data, 'check': check})

@login_required(login_url='reports:login')
def lr_view(request, check_id):
    check = get_object_or_404(Check, pk=check_id)
    pdf_bytes = check.lien_release_pdf.read()
    pdf_data = base64.b64encode(pdf_bytes).decode('utf-8')
    return render(request, 'reports/check_view.html', {'pdf_data': pdf_data, 'check': check})


