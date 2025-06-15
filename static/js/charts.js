document.addEventListener('DOMContentLoaded', async () => {
    // Chart.js default configuration
    Chart.defaults.font.family = 'Poppins, sans-serif';
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
    
    // Get theme colors
    const getThemeColors = () => {
        const style = getComputedStyle(document.body);
        return {
            textPrimary: style.getPropertyValue('--text-primary'),
            textSecondary: style.getPropertyValue('--text-secondary'),
            accent: style.getPropertyValue('--accent'),
            bgSecondary: style.getPropertyValue('--bg-secondary'),
            success: style.getPropertyValue('--success'),
            warning: style.getPropertyValue('--warning'),
            error: style.getPropertyValue('--error'),
            info: style.getPropertyValue('--info')
        };
    };
    
    // Chart color palette
    const chartColors = [
        '#d9c7a7', '#5a8a64', '#e6a23c', '#409eff', '#c25450',
        '#7b68ee', '#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4'
    ];
    
    let categoryChart, monthlyChart, volumeChart;
    let currentPage = 1;
    
    // Load all data
    async function loadDashboardData() {
        try {
            // Load statistics
            const statsResponse = await fetch('/api/stats');
            const stats = await statsResponse.json();
            
            // Update summary cards
            updateSummaryCards(stats);
            
            // Load category distribution
            const categoryResponse = await fetch('/api/category-distribution');
            const categoryData = await categoryResponse.json();
            
            // Load monthly stats
            const monthlyResponse = await fetch('/api/monthly-stats');
            const monthlyData = await monthlyResponse.json();
            
            // Create charts
            createCategoryChart(categoryData);
            createMonthlyChart(monthlyData);
            createVolumeChart(stats.categories);
            createCategoryBreakdown(stats.categories);
            
            // Load transactions
            loadTransactions(currentPage);
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }
    
    // Update summary cards
    function updateSummaryCards(stats) {
        document.getElementById('total-transactions').textContent = stats.total_transactions.toLocaleString();
        document.getElementById('total-amount').textContent = formatCurrency(stats.total_amount);
        document.getElementById('total-fees').textContent = formatCurrency(stats.total_fees);
        
        const avgTransaction = stats.total_transactions > 0 
            ? stats.total_amount / stats.total_transactions 
            : 0;
        document.getElementById('avg-transaction').textContent = formatCurrency(avgTransaction);
    }
    
    // Format currency
    function formatCurrency(amount) {
        return amount.toLocaleString('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        }) + ' RWF';
    }
    
    // Create category pie chart
    function createCategoryChart(data) {
        const ctx = document.getElementById('categoryChart').getContext('2d');
        const colors = getThemeColors();
        
        if (categoryChart) {
            categoryChart.destroy();
        }
        
        if (!data || data.length === 0) {
            ctx.fillStyle = colors.textSecondary;
            ctx.font = '16px Poppins';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        categoryChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.category),
                datasets: [{
                    data: data.map(d => d.count),
                    backgroundColor: chartColors,
                    borderColor: colors.bgSecondary,
                    borderWidth: 2
                }]
            },
            options: {
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: colors.textPrimary,
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Create monthly trend chart
    function createMonthlyChart(data) {
        const ctx = document.getElementById('monthlyChart').getContext('2d');
        const colors = getThemeColors();
        
        if (monthlyChart) {
            monthlyChart.destroy();
        }
        
        if (!data || data.length === 0) {
            ctx.fillStyle = colors.textSecondary;
            ctx.font = '16px Poppins';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
        const labels = data.map(d => `${monthNames[d.month - 1]} ${d.year}`);
        
        monthlyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Transaction Amount',
                    data: data.map(d => d.total_amount),
                    borderColor: colors.accent,
                    backgroundColor: colors.accent + '20',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Transaction Count',
                    data: data.map(d => d.count * 1000), // Scale for visibility
                    borderColor: colors.success,
                    backgroundColor: colors.success + '20',
                    borderWidth: 3,
                    tension: 0.4,
                    fill: true,
                    yAxisID: 'y1'
                }]
            },
            options: {
                plugins: {
                    legend: {
                        labels: {
                            color: colors.textPrimary
                        }
                    }
                },
                scales: {
                    x: {
                        grid: {
                            color: colors.bgSecondary
                        },
                        ticks: {
                            color: colors.textSecondary
                        }
                    },
                    y: {
                        position: 'left',
                        grid: {
                            color: colors.bgSecondary
                        },
                        ticks: {
                            color: colors.textSecondary,
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    },
                    y1: {
                        position: 'right',
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: colors.textSecondary,
                            callback: function(value) {
                                return (value / 1000).toFixed(0);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Create volume bar chart
    function createVolumeChart(categories) {
        const ctx = document.getElementById('volumeChart').getContext('2d');
        const colors = getThemeColors();
        
        if (volumeChart) {
            volumeChart.destroy();
        }
        
        if (!categories || Object.keys(categories).length === 0) {
            ctx.fillStyle = colors.textSecondary;
            ctx.font = '16px Poppins';
            ctx.textAlign = 'center';
            ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
            return;
        }
        
        const categoryNames = Object.keys(categories).map(cat => 
            cat.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
        );
        const amounts = Object.values(categories).map(cat => cat.amount);
        
        volumeChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: categoryNames,
                datasets: [{
                    label: 'Total Amount',
                    data: amounts,
                    backgroundColor: colors.accent,
                    borderColor: colors.accent,
                    borderWidth: 1
                }]
            },
            options: {
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: colors.textSecondary,
                            maxRotation: 45,
                            minRotation: 45
                        }
                    },
                    y: {
                        grid: {
                            color: colors.bgSecondary
                        },
                        ticks: {
                            color: colors.textSecondary,
                            callback: function(value) {
                                return formatCurrency(value);
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Create category breakdown list
    function createCategoryBreakdown(categories) {
        const container = document.getElementById('category-breakdown');
        container.innerHTML = '';
        
        if (!categories || Object.keys(categories).length === 0) {
            container.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No data available</p>';
            return;
        }
        
        Object.entries(categories).forEach(([category, data]) => {
            const categoryName = category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
            
            const item = document.createElement('div');
            item.className = 'category-item';
            item.innerHTML = `
                <span class="category-name">${categoryName}</span>
                <div class="category-stats">
                    <span class="category-count">${data.count}</span>
                    <span class="category-amount">${formatCurrency(data.amount)}</span>
                </div>
            `;
            
            container.appendChild(item);
        });
    }
    
    // Load transactions
    async function loadTransactions(page) {
        try {
            const response = await fetch(`/api/transactions?page=${page}&per_page=10`);
            const data = await response.json();
            
            const tbody = document.getElementById('transactions-tbody');
            tbody.innerHTML = '';
            
            if (!data.transactions || data.transactions.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: var(--text-secondary);">No transactions found</td></tr>';
                return;
            }
            
            data.transactions.forEach(transaction => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${formatDate(transaction.date)}</td>
                    <td>${formatCategory(transaction.category)}</td>
                    <td>${transaction.recipient_name || '-'}</td>
                    <td>${formatCurrency(transaction.amount)}</td>
                    <td>${formatCurrency(transaction.fee)}</td>
                    <td>${transaction.balance ? formatCurrency(transaction.balance) : '-'}</td>
                `;
                tbody.appendChild(row);
            });
            
            // Update pagination
            updatePagination(data.current_page, data.pages);
            
        } catch (error) {
            console.error('Error loading transactions:', error);
        }
    }
    
    // Update pagination
    function updatePagination(current, total) {
        const pagination = document.getElementById('pagination');
        pagination.innerHTML = '';
        
        if (total <= 1) return;
        
        // Previous button
        const prevBtn = document.createElement('button');
        prevBtn.innerHTML = '<i class="fas fa-chevron-left"></i>';
        prevBtn.disabled = current === 1;
        prevBtn.onclick = () => loadTransactions(current - 1);
        pagination.appendChild(prevBtn);
        
        // Page numbers
        const maxVisible = 5;
        let start = Math.max(1, current - Math.floor(maxVisible / 2));
        let end = Math.min(total, start + maxVisible - 1);
        
        if (end - start < maxVisible - 1) {
            start = Math.max(1, end - maxVisible + 1);
        }
        
        for (let i = start; i <= end; i++) {
            const pageBtn = document.createElement('button');
            pageBtn.textContent = i;
            pageBtn.className = i === current ? 'active' : '';
            pageBtn.onclick = () => loadTransactions(i);
            pagination.appendChild(pageBtn);
        }
        
        // Next button
        const nextBtn = document.createElement('button');
        nextBtn.innerHTML = '<i class="fas fa-chevron-right"></i>';
        nextBtn.disabled = current === total;
        nextBtn.onclick = () => loadTransactions(current + 1);
        pagination.appendChild(nextBtn);
    }
    
    // Format date
    function formatDate(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    // Format category
    function formatCategory(category) {
        if (!category) return '-';
        return category.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    // Export functionality
    document.getElementById('export-btn').addEventListener('click', async () => {
        try {
            window.open('/api/export-csv', '_blank');
        } catch (error) {
            console.error('Error exporting data:', error);
        }
    });
    
    // Clear data functionality
    document.getElementById('clear-data-btn').addEventListener('click', async () => {
        if (confirm('Are you sure you want to clear all transaction data? This action cannot be undone.')) {
            try {
                const response = await fetch('/api/clear-data', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    alert('Data cleared successfully');
                    location.reload();
                } else {
                    alert('Error clearing data: ' + data.error);
                }
            } catch (error) {
                alert('Error clearing data: ' + error.message);
            }
        }
    });
    
    // Update charts on theme change
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            if (mutation.attributeName === 'class') {
                setTimeout(() => {
                    loadDashboardData();
                }, 300);
            }
        });
    });
    
    observer.observe(document.body, {
        attributes: true,
        attributeFilter: ['class']
    });
    
    // Initial load
    loadDashboardData();
});