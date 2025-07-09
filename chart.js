document.addEventListener('DOMContentLoaded', function() {
    const expenseChartCanvas = document.getElementById('expenseChart').getContext('2d');
    const budgetChartCanvas = document.getElementById('budgetComparisonChart').getContext('2d');

    let expenseChart, budgetChart; // Store chart instances

    function loadExpenses() {
        fetch('/get-expenses')
            .then(response => response.json())
            .then(data => {
                updateCharts(data.expenses, data.budget || []);
            })
            .catch(error => console.error('Error loading expenses:', error));
    }

    function updateCharts(expenses, budget) {
        // Destroy previous charts if they exist
        if (expenseChart instanceof Chart) {
            expenseChart.destroy();
        }
        if (budgetChart instanceof Chart) {
            budgetChart.destroy();
        }

        // Group expenses by category
        const categories = [...new Set(expenses.map(e => e.category))];
        const amounts = categories.map(cat => 
            expenses.filter(e => e.category === cat).reduce((sum, e) => sum + e.amount, 0)
        );

        // 🎯 **Pie Chart (Expense Distribution)**
        expenseChart = new Chart(expenseChartCanvas, {
            type: 'pie',
            data: {
                labels: categories,
                datasets: [{
                    data: amounts,
                    backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff', '#ff9f40'],
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { enabled: true }
                }
            }
        });

        // 🎯 **Bar Chart (Budget vs. Actual Spending)**
        const planned = budget.map(b => b.amount || 0);
        const actual = categories.map(cat => amounts[categories.indexOf(cat)] || 0);

        budgetChart = new Chart(budgetChartCanvas, {
            type: 'bar',
            data: {
                labels: categories,
                datasets: [
                    { label: 'Planned Budget', data: planned, backgroundColor: 'blue' },
                    { label: 'Actual Expenses', data: actual, backgroundColor: 'red' }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: { beginAtZero: true }
                },
                plugins: {
                    legend: { position: 'top' },
                    tooltip: { enabled: true }
                }
            }
        });
    }

    loadExpenses();
});
