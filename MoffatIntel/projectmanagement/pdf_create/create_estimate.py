import os
import tempfile

from django.conf import settings
from django.core.files.base import ContentFile
from datetime import datetime
from fpdf import FPDF
from ..models import Estimate, EstimateLineItem

def create_estimate(line_items, project, sub):
    estimates = Estimate.objects.order_by("-date").filter(project_id=project).filter(sub_id=sub)

    estimate = Estimate()
    estimate.name = "Estimate " + chr(len(estimates) + 65)
    estimate.date = datetime.now().strftime('%Y-%m-%d')
    estimate.sub_id = sub
    estimate.project_id = project

    group_data = []
    total_total = 0.00

    # Loop through line_items to organize data into groups
    for line_item in line_items:
        # Create a dictionary to represent the current row
        row_data = {
            'scope': line_item.scope,
            'qty': line_item.qty,
            'unit_price': line_item.unit_price,
            'total_price': line_item.total
        }

        # Determine the group name based on the group_id
        if line_item.group_id:
            group_name = line_item.group_id.name
        else:
            group_name = 'Other'

        # Check if the group already exists in group_data
        existing_group = next((group for group in group_data if group['group_name'] == group_name), None)

        if existing_group:
            # Append the row to the existing group's rows list
            existing_group['rows'].append(row_data)
        else:
            # Create a new group and add the current row to its rows list
            group_data.append({
                'group_name': group_name,
                'rows': [row_data]
            })

    file_name = estimate.name + " " + str(estimate.date)

    if os.path.exists(file_name + ".pdf"):
        print("***********Check 4**********")
        counter = 1
        while os.path.exists(file_name + "(" + str(counter) + ")" + ".pdf"):
            counter += 1
        file_name += "(" + str(counter) + ")"

    file_name += ".pdf"

    pdf = FPDF()

    # Set up the PDF document
    pdf.set_title("Scope & Values - Estimate")
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

    pdf.set_font("Arial", style="B", size=10)
    pdf.set_line_width(.75)
    pdf.cell(pdf.w - 20, 5, f"SCOPE & VALUES - EXHIBIT {chr(len(estimates) + 65)}", 1, 0, align="C")
    pdf.ln(10)

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
            pdf.cell((pdf.w - 20) * .2, 5, "$" + "{:.2f}".format(total_price), 1, 1, 'L', True)
            group_subtotal += float(total_price)

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

    estimate.total = total_total

    # Generate the full file path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    temp_file_path = temp_file.name

    pdf.output(temp_file_path)
    with open(temp_file_path, 'rb') as file:
        file_content = file.read()

    file_data = ContentFile(file_content)

    estimate.pdf.save(file_name, file_data)

    # Delete the temporary file
    temp_file.close()
    os.remove(temp_file_path)

    project.date = datetime.now()
    project.save()
    estimate.save()

    return estimate