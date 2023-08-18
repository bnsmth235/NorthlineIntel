import os
from django.conf import settings
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from datetime import datetime
from fpdf import FPDF
from ..models import Contract, DeductiveChangeOrder, ChangeOrder

def create_change_order(POST, type, rows):
    contract = get_object_or_404(Contract, pk=POST.get('contract'))
    project = contract.project_id
    sub = contract.sub_id

    file_name = type + " " + str(datetime.now().strftime("%B-%d-%Y"))

    if os.path.exists(file_name + ".pdf"):
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
    pdf.image(os.path.join(settings.BASE_DIR, 'projectmanagement\static\\projectmanagement\images\logo_onlyM.png'),
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
    ex_file_path = os.path.join(settings.STATIC_ROOT, "deductive_change_orders", file_name)
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
