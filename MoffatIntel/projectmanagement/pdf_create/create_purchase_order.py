import os
from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime
from fpdf import FPDF
from ..models import Draw, PurchaseOrder

def create_purchase_order(project, vendor, rows):
    draws = Draw.objects.filter(project_id=project)
    file_name = project.name + " " + vendor.name + " " + str(datetime.now().strftime("%B-%d-%Y"))

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
    pdf.set_title(project.name + " " + vendor.name + " " + str(datetime.now().strftime("%B-%d-%Y")))
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
    pdf.cell(pdf.w - 20, 10, "PURCHASE ORDER", 1, 0, align="C")
    pdf.ln(15)

    pdf.set_font("Arial", size=10)

    # Define table data

    table_data = [
        ["MOFFAT CONSTRUCTION", ""],
        ["a Moffat Company", "          Purchase Order No.:   " + "PO" + str(datetime.now().strftime("%y")) + str(
        "{:03d}".format(len(PurchaseOrder.objects.all()) + 1))],
        ["519 W. STATE STREET SUITE #202", "          Date:   " + str(datetime.now().strftime("%B-%d-%Y"))],
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
    pdf.multi_cell((pdf.w - 20) * .125, 5, "Draw: " + str(len(draws)) + "\nDate: " + str(datetime.now().strftime("%m-%d-%Y")), 1, "L", True)
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
        ["Date:          " + str(datetime.now().strftime("%B-%d-%Y")), "Date: "]
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
    po.order_number = "PO" + str(datetime.now().strftime("%y")) + str(
        "{:03d}".format(len(PurchaseOrder.objects.all()) + 1))
    po.date = datetime.now()
    po.vendor_id = vendor
    po.project_id = project
    po.pdf.save(file_name, file_data)
    po.total = subtotal

    # Delete the temporary file
    os.remove(ex_file_path)

    project.date = datetime.now()
    project.save()
    po.save()
    print("***********Check Final**********")
    return po
