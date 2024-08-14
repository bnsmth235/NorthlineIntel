let sumContractTotal = 0;
let sumTotalPaid = 0;
let sumDrawAmount = 0;
let sumAmountRemaining = 0;

const currencyFormatter = new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
});

// For percentage formatting
const percentFormatter = new Intl.NumberFormat('en-US', {
    style: 'percent',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
});

//wait until dom is loaded
document.addEventListener('DOMContentLoaded', function() {
    const submitButton = document.getElementById('submitDraw');
    submitButton.addEventListener('click', function() {
      var myModal = new bootstrap.Modal(document.getElementById('submitDrawModal'), {});
      myModal.show();
      populateModalContent()
    });
});

function populateModalContent(){
    if(canDrawBeSubmitted()){
        document.querySelector('.modal-body').textContent = 'Are you sure you want to submit this draw?';
        const submitButton = document.getElementById('modalSubmitDraw');
        submitButton.addEventListener('click', function() {
            window.location.href = `/projectmanagement/submit_draw/${document.getElementById('drawId').textContent}`;
        });
    }
    else{
        document.querySelector('.modal-body').textContent = 'Each line item must have a check and a signed lien release before the draw can be submitted.'
        const submitButton = document.getElementById('modalSubmitDraw');
        submitButton.disabled = true;
    }
}

// Fetch data from your server
document.addEventListener('DOMContentLoaded', async function() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    })
    // Get the draw ID
    const drawId = document.getElementById('drawId').textContent;
    const response = await fetch('/projectmanagement/get_draw_data/' + drawId);
    const data = await response.json();

    // Get a reference to the table body
    const tbody = document.querySelector('.table tbody');

    // Loop through the draw items
    for (let item of data.draw_items) {
        console.log(item)
        // Find the corresponding subcontractor
        const sub = data.subs.find(sub => sub.id === item.sub_id);

        const amountRemaining = item.contract_total - item.total_paid - item.draw_amount;
        const type =  amountRemaining > 0 ? 'C' : 'F';

        sumContractTotal += item.contract_total;
        sumTotalPaid += item.total_paid;
        sumDrawAmount += item.draw_amount;
        sumAmountRemaining += amountRemaining;

        let lr = await getLrForDrawItem(item, type);
        try{
            lr = lr.lr
        }catch (e) {
            lr = null;
        }

        let check = await getCheckForDrawItem(item);
        try{
            check = check.check
        } catch (e) {
            check = null;
        }

        // Create a new table row
        const row = document.createElement('tr');

        // Create table cells for each property and append them to the row
        const divisionCodeCell = document.createElement('td');
        divisionCodeCell.textContent = sub.csi;
        row.appendChild(divisionCodeCell);

        const w9Cell = document.createElement('td');
        w9Cell.textContent = sub.w9;
        row.appendChild(w9Cell);

        const subcontractorCell = document.createElement('td');
        subcontractorCell.textContent = sub.name;
        row.appendChild(subcontractorCell);

        const contractTotalCell = document.createElement('td');
        contractTotalCell.textContent = currencyFormatter.format(item.contract_total.toFixed(2));
        contractTotalCell.style.textAlign = 'right';
        row.appendChild(contractTotalCell);

        const totalPaidCell = document.createElement('td');
        totalPaidCell.textContent = currencyFormatter.format(item.total_paid.toFixed(2));
        totalPaidCell.style.textAlign = 'right';
        row.appendChild(totalPaidCell);

        const percentCompleteCell = document.createElement('td');
        percentCompleteCell.textContent = percentFormatter.format(((item.total_paid + item.draw_amount) / item.contract_total).toFixed(2));
        percentCompleteCell.style.textAlign = 'right';
        row.appendChild(percentCompleteCell);

        const drawAmountCell = document.createElement('td');
        drawAmountCell.textContent = currencyFormatter.format(item.draw_amount.toFixed(2));
        drawAmountCell.style.textAlign = 'right';
        row.appendChild(drawAmountCell);

        const amountRemainingCell = document.createElement('td');
        amountRemainingCell.textContent = currencyFormatter.format(amountRemaining.toFixed(2));
        amountRemainingCell.style.textAlign = 'right';
        row.appendChild(amountRemainingCell);

        const descriptionCell = document.createElement('td');
        descriptionCell.textContent = item.description;
        row.appendChild(descriptionCell);

        const lrTypeCell = document.createElement('td');
        lrTypeCell.textContent = amountRemaining > 0 ? 'Conditional' : 'Final';
        row.appendChild(lrTypeCell);

        const lrImageCell = document.createElement('td');
        const lrImage = document.createElement('img');
        if(lr.signed) {
            lrImage.src = pdfIconUrl;
            lrImage.className = 'lr-image-signed';
        } else {
            lrImage.src = unsignedUrl;
            lrImage.setAttribute('data-bs-toggle', 'tooltip');
            lrImage.setAttribute('data-bs-placement', 'top');
            lrImage.setAttribute('title', 'Lien Release is not signed');
        }
        lrImage.style.height = '23px';
        lrImage.style.width = 'auto';
        lrImage.style.height = '23px';
        lrImage.style.width = 'auto';
        const lrLink = document.createElement('a');
        lrLink.href = "/projectmanagement/lr_view/" + lr.id;
        lrLink.appendChild(lrImage);
        lrImageCell.appendChild(lrLink);
        row.appendChild(lrImageCell);

        if(check){
            const checkNumberCell = document.createElement('td');
            checkNumberCell.textContent = check.check_num;
            row.appendChild(checkNumberCell);

            const checkDateCell = document.createElement('td');
            const formattedDate = new Date(check.check_date).toLocaleDateString();
            checkDateCell.textContent = formattedDate;
            row.appendChild(checkDateCell);

            const checkImageCell = document.createElement('td');
            const checkImage = document.createElement('img');
            const checkLink = document.createElement('a');

            if(check.pdf){
                checkImage.src = pdfIconUrl;
                checkImage.className = 'check-image';
                checkLink.href = "#";
            }else {
                checkImage.src = pdfIconRedUrl;
                checkImage.setAttribute('data-bs-toggle', 'tooltip');
                checkImage.setAttribute('data-bs-placement', 'top');
                checkImage.setAttribute('title', 'Check is not uploaded');
                checkLink.href = "#";
            }

            checkImage.style.height = '23px';
            checkImage.style.width = 'auto';
            checkLink.appendChild(checkImage);
            checkImageCell.appendChild(checkLink);
            row.appendChild(checkImageCell);
        } else {
            const addCheckCell = document.createElement('td');
            addCheckCell.colSpan = 3;
            addCheckCell.style.alignContent = 'center';
            const addCheckButton = document.createElement('button');
            addCheckButton.textContent = '+ Add Check';
            addCheckButton.className = 'add-button-small';
            addCheckButton.onclick = function() {
                window.location.href = `/projectmanagement/new_check/${item.id}`;
            };
            addCheckCell.appendChild(addCheckButton);
            row.appendChild(addCheckCell);
        }

        const editCell = document.createElement('td');
        const editImage = document.createElement('img');
        editImage.src = editIconUrl;
        editImage.style.height = '20px';
        editImage.style.width = 'auto';
        const editLink = document.createElement('a');
        editLink.href = `/projectmanagement/edit_draw_summary_item/${item.id}`;
        editLink.appendChild(editImage);
        editCell.appendChild(editLink);
        row.appendChild(editCell);

        const deleteCell = document.createElement('td');
        const deleteImage = document.createElement('img');
        deleteImage.src = deleteIconUrl;
        deleteImage.style.height = '20px';
        deleteImage.style.width = 'auto';
        const deleteLink = document.createElement('a');
        deleteLink.href = `#`;
        deleteLink.appendChild(deleteImage);
        deleteCell.appendChild(deleteLink);
        row.appendChild(deleteCell);

        // Append the row to the table body
        tbody.appendChild(row);
    }

    addTotalRow();
});

function addTotalRow() {
    // Create a total row
    const tbody = document.querySelector('.table tbody');
    const totalRow = document.createElement('tr');

    // Add cells to the total row
    const totalLabelCell = document.createElement('td');
    totalLabelCell.textContent = 'Totals:';
    totalLabelCell.colSpan = 3;
    totalLabelCell.style.fontWeight = 'bold';
    totalLabelCell.style.textAlign = 'right';
    totalRow.appendChild(totalLabelCell);

    // Add cells for the sums
    const totalContractTotalCell = document.createElement('td');
    totalContractTotalCell.textContent = currencyFormatter.format(sumContractTotal.toFixed(2));
    totalContractTotalCell.style.textAlign = 'right';
    totalRow.appendChild(totalContractTotalCell);

    const totalPaidCell = document.createElement('td');
    totalPaidCell.textContent = currencyFormatter.format(sumTotalPaid.toFixed(2));
    totalPaidCell.style.textAlign = 'right';
    totalRow.appendChild(totalPaidCell);

    // Skip the percentage cell
    const percentCompleteCell = document.createElement('td');
    percentCompleteCell.textContent = percentFormatter.format(((sumTotalPaid + sumDrawAmount) / sumContractTotal).toFixed(2));
    percentCompleteCell.style.textAlign = 'right';
    totalRow.appendChild(percentCompleteCell);

    const totalDrawAmountCell = document.createElement('td');
    totalDrawAmountCell.textContent = currencyFormatter.format(sumDrawAmount.toFixed(2));
    totalDrawAmountCell.style.textAlign = 'right';
    totalRow.appendChild(totalDrawAmountCell);

    const totalAmountRemainingCell = document.createElement('td');
    totalAmountRemainingCell.textContent = currencyFormatter.format(sumAmountRemaining.toFixed(2));
    totalAmountRemainingCell.style.textAlign = 'right';
    totalRow.appendChild(totalAmountRemainingCell);

    const spacer = document.createElement('td');
    spacer.colSpan = 8;
    totalRow.appendChild(spacer);

    // Append the total row to the table body
    tbody.appendChild(totalRow);
}

async function getExhibitsForSub(sub) {
    const projectId = document.getElementById('projectId').textContent;
    const response = await fetch(`/projectmanagement/get_exhibits/${sub.name}/${projectId}`);
    const exhibits = await response.json();
    for (let exhibit of exhibits) {
        const itemResponse = await fetch('/projectmanagement/get_exhibit_line_items/' + exhibit.id);
        const items = await itemResponse.json();
        exhibit['line_items'] = items;
    }
    return exhibits;
}

async function getLrForDrawItem(draw_item, type) {
    const response = await fetch(`/projectmanagement/get_lr_for_draw_item/${draw_item.id}/${type}`);
    return await response.json();
}

async function getCheckForDrawItem(draw_item) {
    const response = await fetch(`/projectmanagement/get_check_for_draw_item/${draw_item.id}`);
    return await response.json();
}

function getContractTotal(exhibits){
    let total = 0.00;
    exhibits.forEach(exhibit => {
        exhibit.line_items.forEach(item => {
            total += item.total;
        });
    });

    return total;
}

function getTotalPaid(exhibits){
    let total = 0.00;
    exhibits.forEach(exhibit => {
        exhibit.line_items.forEach(item => {
            total += item.total_paid;
        });
    });

    return total;
}

function canDrawBeSubmitted(){
    // Each line item must have a check and a signed lien release
    const checkImages = document.querySelectorAll('.check-image');
    const lrImages = document.querySelectorAll('.lr-image-signed');
    const drawItems = document.querySelectorAll('.table tbody tr');

    return checkImages.length === lrImages.length && lrImages.length === drawItems.length;
}

