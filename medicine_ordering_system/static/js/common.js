// Common JavaScript functions for OnCare Medicine Ordering System

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Update cart count
    updateCartCount();
    
    // Update notification count
    updateNotificationCount();
});

// Cart management functions
function addToCart(medicineId, quantity = 1) {
    $.ajax({
        url: '/orders/api/cart/add/',
        method: 'POST',
        data: {
            'medicine_id': medicineId,
            'quantity': quantity,
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Item added to cart successfully!');
                updateCartCount();
            } else {
                showAlert('danger', response.message || 'Failed to add item to cart');
            }
        },
        error: function() {
            showAlert('danger', 'An error occurred while adding item to cart');
        }
    });
}

function removeFromCart(medicineId) {
    $.ajax({
        url: '/orders/api/cart/remove/',
        method: 'POST',
        data: {
            'medicine_id': medicineId,
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                showAlert('success', 'Item removed from cart');
                updateCartCount();
                location.reload(); // Refresh to update cart display
            } else {
                showAlert('danger', response.message || 'Failed to remove item from cart');
            }
        },
        error: function() {
            showAlert('danger', 'An error occurred while removing item from cart');
        }
    });
}

function updateCartCount() {
    $.ajax({
        url: '/orders/api/cart/',
        method: 'GET',
        success: function(response) {
            $('#cart-count').text(response.total_items || 0);
        }
    });
}

function updateNotificationCount() {
    $.ajax({
        url: '/common/api/notifications/',
        method: 'GET',
        success: function(response) {
            $('#notification-count').text(response.unread_count || 0);
        }
    });
}

// Alert functions
function showAlert(type, message) {
    var alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    $('.container-fluid').prepend(alertHtml);
    
    // Auto-hide after 5 seconds
    setTimeout(function() {
        $('.alert').first().fadeOut('slow');
    }, 5000);
}

// Chart functions
function createLineChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: options.title || 'Chart'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

function createBarChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
            },
            title: {
                display: true,
                text: options.title || 'Chart'
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

function createPieChart(canvasId, data, options = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
            },
            title: {
                display: true,
                text: options.title || 'Chart'
            }
        }
    };
    
    return new Chart(ctx, {
        type: 'pie',
        data: data,
        options: { ...defaultOptions, ...options }
    });
}

// Analytics functions
function loadForecastChart(forecastId) {
    $.ajax({
        url: `/analytics/api/forecast/${forecastId}/data/`,
        method: 'GET',
        success: function(data) {
            const chartData = {
                labels: data.historical.dates,
                datasets: [
                    {
                        label: 'Historical Demand',
                        data: data.historical.values,
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    },
                    {
                        label: 'Forecasted Demand',
                        data: [...Array(data.historical.values.length).fill(null), ...data.forecast.values],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }
                ]
            };
            
            createLineChart('forecastChart', chartData, {
                title: 'Demand Forecast',
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        title: {
                            display: true,
                            text: 'Quantity'
                        }
                    }
                }
            });
        },
        error: function() {
            showAlert('danger', 'Failed to load forecast data');
        }
    });
}

function loadSalesTrendsChart(medicineId) {
    $.ajax({
        url: `/analytics/api/sales-trends/${medicineId}/`,
        method: 'GET',
        success: function(data) {
            const chartData = {
                labels: data.dates,
                datasets: [
                    {
                        label: 'Quantity Sold',
                        data: data.quantities,
                        borderColor: 'rgb(54, 162, 235)',
                        backgroundColor: 'rgba(54, 162, 235, 0.2)',
                        yAxisID: 'y'
                    },
                    {
                        label: 'Revenue',
                        data: data.revenues,
                        borderColor: 'rgb(255, 205, 86)',
                        backgroundColor: 'rgba(255, 205, 86, 0.2)',
                        yAxisID: 'y1'
                    }
                ]
            };
            
            const options = {
                title: 'Sales Trends',
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'Quantity'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: true,
                        position: 'right',
                        title: {
                            display: true,
                            text: 'Revenue ($)'
                        },
                        grid: {
                            drawOnChartArea: false,
                        },
                    }
                }
            };
            
            createLineChart('salesTrendsChart', chartData, options);
        },
        error: function() {
            showAlert('danger', 'Failed to load sales trends data');
        }
    });
}

// Form validation
function validateForm(formId) {
    const form = document.getElementById(formId);
    if (form.checkValidity() === false) {
        event.preventDefault();
        event.stopPropagation();
    }
    form.classList.add('was-validated');
}

// Search functionality
function initializeSearch() {
    $('.search-input').on('keyup', function() {
        const searchTerm = $(this).val().toLowerCase();
        const targetTable = $(this).data('target');
        
        $(`#${targetTable} tbody tr`).filter(function() {
            $(this).toggle($(this).text().toLowerCase().indexOf(searchTerm) > -1);
        });
    });
}

// Pagination
function loadPage(url, containerId) {
    $.ajax({
        url: url,
        method: 'GET',
        success: function(data) {
            $(`#${containerId}`).html(data);
        },
        error: function() {
            showAlert('danger', 'Failed to load page');
        }
    });
}

// Confirmation dialogs
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Loading states
function showLoading(elementId) {
    $(`#${elementId}`).html(`
        <div class="text-center">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
        </div>
    `);
}

function hideLoading(elementId) {
    $(`#${elementId}`).empty();
}

// Export functions
function exportToCSV(data, filename) {
    const csv = convertToCSV(data);
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    window.URL.revokeObjectURL(url);
}

function convertToCSV(data) {
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => row[header]).join(','))
    ].join('\n');
    return csvContent;
}

// Utility functions
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    return new Date(dateString).toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Initialize common functionality
$(document).ready(function() {
    initializeSearch();
    
    // Add fade-in animation to cards
    $('.card').addClass('fade-in-up');
    
    // Initialize data tables if present
    if ($.fn.DataTable) {
        $('.data-table').DataTable({
            responsive: true,
            pageLength: 25,
            order: [[0, 'desc']]
        });
    }
});


