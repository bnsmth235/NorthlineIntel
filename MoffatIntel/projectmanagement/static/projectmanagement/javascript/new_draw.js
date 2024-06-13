let checkedSubcontractors = [];
let subcontractorPages = [];
let currentPageIndex = 0;

document.querySelector('form').addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        console.log("preventing default");
        event.preventDefault();
        return false;
    }
});

function stepTwo() {
    // if subcontractorPages, then remove exhibitInputsX from the DOM
    if (subcontractorPages.length > 0) {
        subcontractorPages.forEach((page, index) => {
            const exhibitInputDiv = document.getElementById('exhibitInputs' + index);
            exhibitInputDiv.remove();
        });
    }
    subcontractorPages = [];
    currentPageIndex = 0;
    checkedSubcontractors = [];

    const subcontractors = Array.from(document.querySelectorAll('#subcontractorList input[type="checkbox"]'));

    subcontractors.forEach(sub => {
        if (sub.checked) {
            checkedSubcontractors.push(sub.value);
        }
    });

    const exhibitDiv = document.getElementById('exhibitInputs');
    subcontractorPages = checkedSubcontractors.map((subcontractor, index) => {
        const page = exhibitDiv.cloneNode(true);
        page.id = 'exhibitInputs' + index; // Change the id of the cloned element
        page.style.display = index === 0 ? 'flex' : 'none'; // Only show the first page initially
        const title = page.querySelector('#subName');
        title.textContent = subcontractor;
        // Add the exhibit inputs for this subcontractor to the page
        document.getElementById('step2').appendChild(page);
        return page;
    });

    // Fetch exhibit objects and generate input fields
    fetchExhibitsAndGenerateInputs(checkedSubcontractors)
        .then(() => {
            // Hide step 1 and show step 2
            document.getElementById('step1').style.display = 'none';
            document.getElementById('step2').style.display = 'flex';

            exhibitDiv.style.display = 'none'; // Hide the original exhibitDiv

        });
}

function fetchExhibitsAndGenerateInputs(subcontractors) {
    const promises = subcontractors.map((subcontractor, index) => {
        // Get project id from url
        const projectId = window.location.pathname.split('/')[3];
        return fetch(`/projectmanagement/get_exhibits/${subcontractor}/${projectId}`)
            .then(response => response.json())
            .then(exhibits => {
                const tableBody = subcontractorPages[index].querySelector('tbody'); // Get the tbody of the correct page

                const exhibitPromises = exhibits.map(exhibit => {
                    // Create a row for the exhibit
                    const exhibitRow = document.createElement('tr');
                    const exhibitCell = document.createElement('td');
                    exhibitCell.textContent = exhibit.name;
                    exhibitCell.colSpan = '6';
                    exhibitRow.appendChild(exhibitCell);
                    tableBody.appendChild(exhibitRow);

                    return fetch(`/projectmanagement/get_exhibit_line_items/${exhibit.id}`)
                        .then(response => response.json())
                        .then(lineItems => {
                            lineItems.forEach(lineItem => {
                                // Create a row for the line item
                                const lineItemRow = document.createElement('tr');
                                const spacer = document.createElement('td');
                                lineItemRow.appendChild(spacer);
                                const scopeCell = document.createElement('td');
                                scopeCell.textContent = lineItem.scope;
                                lineItemRow.appendChild(scopeCell);

                                const totalCell = document.createElement('td');
                                totalCell.textContent = `$${parseFloat(lineItem.total).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                                lineItemRow.appendChild(totalCell);

                                const totalPaidCell = document.createElement('td');
                                totalPaidCell.textContent = `$${parseFloat(lineItem.total_paid).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
                                lineItemRow.appendChild(totalPaidCell);

                                const inputCell = document.createElement('td');
                                const input = document.createElement('input');
                                input.type = 'number';
                                input.min = (lineItem.total_paid / lineItem.total).toFixed(3) * 100; // Set the min value to the percentage already paid
                                input.max = '100';
                                input.step = '.01';
                                input.value = (lineItem.total_paid / lineItem.total).toFixed(3) * 100;
                                input.dataset.subcontractor = subcontractor;
                                input.dataset.lineItemId = lineItem.id;
                                input.dataset.lineItemValue = lineItem.total; // Store the line item amount in a data attribute
                                inputCell.appendChild(input);

                                const percentSign = document.createElement('strong'); // Create a new span element
                                percentSign.textContent = ' %'; // Set its text content to "%"

                                inputCell.appendChild(percentSign); // Append it to the inputCell

                                lineItemRow.appendChild(inputCell);

                                const payoutCell = document.createElement('td'); // Create a cell for the Draw Amount
                                payoutCell.classList.add('payout'); // Add a class to the cell for easy selection later
                                lineItemRow.appendChild(payoutCell); // Append the cell to the row

                                tableBody.appendChild(lineItemRow);

                                input.addEventListener('change', function() {
                                    let value = parseFloat(input.value);
                                    if (value < input.min) {
                                        input.value = input.min;
                                    } else if (value > 100) {
                                        input.value = '100';
                                    }
                                    calculateAndDisplayPayouts(subcontractorPages[index]);
                                });

                                input.addEventListener('keydown', function(event) {
                                    if (event.key === 'Enter') {
                                        event.preventDefault();
                                        const inputs = Array.from(subcontractorPages[index].querySelectorAll('input'));
                                        const nextInputIndex = inputs.indexOf(input) + 1;
                                        if (nextInputIndex < inputs.length) {
                                            inputs[nextInputIndex].focus();
                                        }
                                    }
                                });

                                input.addEventListener('focus', function() {
                                    input.select();
                                });
                            });
                        });
                });

                return Promise.all(exhibitPromises).then(() => {
                    generateTotalRow(subcontractorPages[index]);
                    calculateAndDisplayPayouts(subcontractorPages[index]); // Calculate and display the totals
                });
            });
    });

    return Promise.all(promises);
}

document.querySelector('.add-button').addEventListener('click', function() {
    // Hide the current page
    subcontractorPages[currentPageIndex].style.display = 'none';
    currentPageIndex++;

    if (currentPageIndex < subcontractorPages.length) {
        // Show the next page
        subcontractorPages[currentPageIndex].style.display = 'block';
    } else {
        // If there are no more pages, proceed to step 3
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step3').style.display = 'block';
    }
});

function stepTwoBack(){
    if(currentPageIndex > 0) {
        // Hide the current page
        subcontractorPages[currentPageIndex].style.display = 'none';
        currentPageIndex--;
        // Show the next page
        subcontractorPages[currentPageIndex].style.display = 'flex';
    }else{
        // Hide step 2 and show step 1
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step1').style.display = 'flex';
    }

}

function stepThreeBack(){
    // Hide step 3 and show step 2
    document.getElementById('step3').style.display = 'none';
    document.getElementById('step2').style.display = 'flex';

}

function collectStepTwoData() {
    const data = subcontractorPages.map(page => {
        const subcontractorName = page.querySelector('#subName').textContent;
        const totalSum = parseFloat(page.querySelector('.total-sum').textContent.replace('$', '').replace(',', ''));
        const totalPaid = parseFloat(page.querySelector('.total-paid').textContent.replace('$', '').replace(',', ''));
        const drawAmountSum = parseFloat(page.querySelector('.draw-amount-sum').textContent.replace('$', '').replace(',', ''));
        const remainingAmount = totalSum - drawAmountSum;
        const exhibitInputs = Array.from(page.querySelectorAll('input'));
        const lineItems = exhibitInputs.map(input => {
            return {
                lineItemId: input.dataset.lineItemId,
                lineItemValue: parseFloat(input.dataset.lineItemValue),
                percentComplete: parseFloat(input.value)
            };
        });

        return {
            subcontractorName,
            totalSum,
            totalPaid,
            drawAmountSum,
            remainingAmount,
            lineItems
        };
    });

    return JSON.stringify(data);
}

function nextPageOrStepThree() {
    if(currentPageIndex < subcontractorPages.length - 1) {
        // Hide the current page
        subcontractorPages[currentPageIndex].style.display = 'none';
        currentPageIndex++;

        // Show the next page
        subcontractorPages[currentPageIndex].style.display = 'flex';
    }else{
        // Hide step 2 and show step 3
        document.getElementById('step2').style.display = 'none';
        document.getElementById('step3').style.display = 'flex';

        const stepTwoData = collectStepTwoData();

        stepThree(stepTwoData);
    }
}

async function stepThree(stepTwoData) {
    const datas = JSON.parse(stepTwoData);
    console.log(datas)
    let totalContractAmount = 0;
    let totalDrawAmount = 0;
    let totalPreviousPaymentAmount = 0;
    let totalRemainingAmount = 0;

    // Get the tbody of the table
    const tableBody = document.querySelector('#step3 tbody');
    tableBody.innerHTML = ''; // Clear the tbody

    for (const sub of datas) {
        const subcontractorName = sub.subcontractorName;
        const response = await fetch(`/projectmanagement/get_sub_data/${subcontractorName}`);
        const subObject = await response.json();

        const totalSum = sub.totalSum;
        const totalPaid = sub.totalPaid;
        const drawAmountSum = sub.drawAmountSum;
        const remainingAmount = sub.remainingAmount;
        // Calculate percent complete based on line items
        let percentComplete = (totalPaid + totalDrawAmount) / totalSum * 100;

        totalContractAmount += totalSum;
        totalDrawAmount += drawAmountSum;
        totalPreviousPaymentAmount += totalPaid;
        totalRemainingAmount += remainingAmount;

        // Create a new row for this subcontractor's payout info
        const payoutRow = document.createElement('tr');

        // Add the Division Code
        const divisionCodeCell = document.createElement('td');
        divisionCodeCell.textContent = subObject.csi || "Division Code"; // Replace with actual data if available
        payoutRow.appendChild(divisionCodeCell);

        // Add the subcontractor's name
        const nameCell = document.createElement('td');
        nameCell.textContent = subcontractorName;
        payoutRow.appendChild(nameCell);

        // Add the contract amount
        const contractAmountCell = document.createElement('td');
        contractAmountCell.textContent = `$${totalSum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        payoutRow.appendChild(contractAmountCell);

        // Add the total paid
        const totalPaidCell = document.createElement('td');
        totalPaidCell.textContent = `$${totalPreviousPaymentAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        payoutRow.appendChild(totalPaidCell);

        // Add the % Complete
        const percentCompleteCell = document.createElement('td');
        percentCompleteCell.textContent = `${percentComplete.toFixed(2)}%`;
        payoutRow.appendChild(percentCompleteCell);

        // Add the draw amount
        const drawAmountCell = document.createElement('td');
        drawAmountCell.textContent = `$${drawAmountSum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        payoutRow.appendChild(drawAmountCell);

        // Add the remaining amount
        const remainingAmountCell = document.createElement('td');
        remainingAmountCell.textContent = `$${remainingAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        payoutRow.appendChild(remainingAmountCell);

        const descriptionCell = document.createElement('td');
        descriptionCell.textContent = subObject.description || "Description"; // Replace with actual data if available
        payoutRow.appendChild(descriptionCell);

        const lrTypeCell = document.createElement('td');
        lrTypeCell.textContent = subObject.lrType || "LR Type"; // Replace with actual data if available
        payoutRow.appendChild(lrTypeCell);

        const w9Cell = document.createElement('td');
        w9Cell.textContent = subObject.w9
        payoutRow.appendChild(w9Cell);

        tableBody.appendChild(payoutRow);
    }

    // Update the totals row
    const totalsRow = document.createElement('tr');

    const totalDivisionCell = document.createElement('td');
    totalDivisionCell.textContent = "Totals:";
    totalDivisionCell.colSpan = '2';
    totalDivisionCell.style.fontWeight = 'bold';
    totalDivisionCell.style.textAlign = 'right';
    totalsRow.appendChild(totalDivisionCell);

    const totalContractCell = document.createElement('td');
    totalContractCell.textContent = `$${totalContractAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    totalsRow.appendChild(totalContractCell);

    const totalPaidCell = document.createElement('td');
    totalPaidCell.textContent = `$${totalPreviousPaymentAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    totalsRow.appendChild(totalPaidCell);

    const totalPercentCell = document.createElement('td');
    totalPercentCell.textContent = `${((totalPreviousPaymentAmount + totalDrawAmount) / totalContractAmount * 100).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}%`;
    totalsRow.appendChild(totalPercentCell);

    const totalDrawCell = document.createElement('td');
    totalDrawCell.textContent = `$${totalDrawAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    totalsRow.appendChild(totalDrawCell);

    const totalRemainingCell = document.createElement('td');
    totalRemainingCell.textContent = `$${totalRemainingAmount.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    totalsRow.appendChild(totalRemainingCell);


    const spacer = document.createElement('td');
    spacer.colSpan = '3';
    totalsRow.appendChild(spacer);

    tableBody.appendChild(totalsRow);
}

function calculateAndDisplayPayouts(page) {
    const exhibitInputs = Array.from(page.querySelectorAll('input'));

    let totalSum = 0;
    let drawAmountSum = 0;
    let totalPaidSum = 0;
    let percentCompleteSum = 0;

    exhibitInputs.forEach(input => {
        let percentComplete = parseFloat(input.value);
        if (isNaN(percentComplete)) { // Check if the input value is a number
            percentComplete = 0; // If not, set it to 0
        }
        const lineItemValue = parseFloat(input.dataset.lineItemValue); // Retrieve the line item amount from the data attribute
        const totalPaid = parseFloat(input.parentNode.previousSibling.textContent.replace('$', '')); // Retrieve the total paid value from the previous cell
        let payout = percentComplete / 100 * lineItemValue - totalPaid;

        if (payout < 0) { // Check if the payout is less than 0
            payout = 0; // If it is, set it to 0
        }

        totalSum += lineItemValue;
        drawAmountSum += payout;
        totalPaidSum += totalPaid;
        percentCompleteSum = ((totalPaidSum + drawAmountSum) / totalSum * 100);

        const payoutCell = input.parentNode.nextSibling; // Get the next sibling of the input's parent (td), which is the Draw Amount cell
        payoutCell.textContent = ` $${payout.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`; // Update the text content of the Draw Amount cell
    });

    const sumRow = page.querySelector('.sum-row'); // Get the sum row

    // Update the text content of the sum cells
    sumRow.querySelector('.total-sum').textContent = `$${totalSum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    sumRow.querySelector('.total-paid').textContent = `$${totalPaidSum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    sumRow.querySelector('.percent-complete').textContent = `${percentCompleteSum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}%`;
    sumRow.querySelector('.draw-amount-sum').textContent = `$${drawAmountSum.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
}

function generateTotalRow(page) {
    let sumRow = document.createElement('tr');
    sumRow.classList.add('sum-row'); // Add a class to the row for easy selection later

    const totalLabel = document.createElement('td');
    totalLabel.colSpan = '2';
    totalLabel.textContent = 'Totals:';
    totalLabel.style.fontWeight = 'bold';
    totalLabel.style.textAlign = 'right';
    sumRow.appendChild(totalLabel);

    const totalSumCell = document.createElement('td');
    totalSumCell.classList.add('total-sum'); // Add a class to the cell for easy selection later
    sumRow.appendChild(totalSumCell);

    const totalPaidCell = document.createElement('td');
    totalPaidCell.classList.add('total-paid'); // Add a class to the cell for easy selection later
    sumRow.appendChild(totalPaidCell);

    const percentCompleteCell = document.createElement('td');
    percentCompleteCell.classList.add('percent-complete'); // Add a class to the cell for easy selection later
    sumRow.appendChild(percentCompleteCell);

    const drawAmountSumCell = document.createElement('td');
    drawAmountSumCell.classList.add('draw-amount-sum'); // Add a class to the cell for easy selection later
    sumRow.appendChild(drawAmountSumCell);

    const tableFooter = page.querySelector('tfoot');
    if (!tableFooter) {
        const table = page.querySelector('table');
        table.appendChild(document.createElement('tfoot')).appendChild(sumRow);
    } else {
        tableFooter.appendChild(sumRow);
    }
}

function compileTableData() {
    const inputElement = document.getElementById('json-data');
    const tableBody = document.querySelector('#step3 tbody');
    const rows = Array.from(tableBody.querySelectorAll('tr')).filter(row => !row.classList.contains('sum-row'));
    const data = rows.map(row => {
        const cells = Array.from(row.querySelectorAll('td'));
        if(cells.length === 10) {
            return {
                divisionCode: cells[0].textContent,
                subcontractorName: cells[1].textContent,
                totalSum: parseFloat(cells[2].textContent.replace('$', '')),
                totalPaid: parseFloat(cells[3].textContent.replace('$', '')),
                percentComplete: parseFloat(cells[4].textContent.replace('%', '')),
                drawAmountSum: parseFloat(cells[5].textContent.replace('$', '')),
                remainingAmount: parseFloat(cells[6].textContent.replace('$', '')),
                description: cells[7].textContent,
                lrType: cells[8].textContent,
                w9: cells[9].textContent
            };
        }
    });
     inputElement.value = JSON.stringify(data);
}

function submitForm() {
    const tableData = compileTableData(); // Compile the table data into JSON
    const projectid = document.getElementById('project_id').textContent;
    console.log(tableData);
    // Send the table data as a POST request to the new_draw URL
    fetch(`/projectmanagement/new_draw/${projectid}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            // Include the CSRF token in the request header
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: tableData
    }).then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        // Handle the response here
    }).catch(error => {
        console.error('There has been a problem with your fetch operation:', error);
    });
}