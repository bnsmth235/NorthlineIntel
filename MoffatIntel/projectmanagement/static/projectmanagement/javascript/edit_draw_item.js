let contractTotalSum = 0;
let contractTotalPaidSum = 0;
document.addEventListener('DOMContentLoaded', function() {
    const subcontractor = document.getElementById('sub').value;
    const projectId = document.getElementById('projectId').textContent;
    fetch(`/projectmanagement/get_exhibits/${subcontractor}/${projectId}`)
        .then(response => response.json())
        .then(exhibits => {
            exhibits.foreach(exhibit => {
                contractTotalSum += exhibit.contract_sum;

                fetch(`/projectmanagement/get_exhibit_line_items/${exhibit.id}`)
                    .then(response => response.json())
                    .then(lineItems => {
                        lineItems.forEach(lineItem => {
                            contractTotalPaidSum += lineItem.paid_sum;
                        });
                    })
            });
        });
    document.getElementById('total_sum').textContent = contractTotalSum;
    document.getElementById('total_paid').textContent = contractTotalPaidSum;
    document.getElementById('remaining_amount').textContent = contractTotalSum - contractTotalPaidSum;
});

const input = document.getElementById('percent_complete');
input.addEventListener('input', function() {
    let value = parseFloat(input.value);
    if (value < input.min) {
        input.value = input.min;
    } else if (value > 100) {
        input.value = '100';
    }

    document.getElementById('draw_amount').value = input.value;
    document.getElementById('draw_amount').textContent = input.value;
});