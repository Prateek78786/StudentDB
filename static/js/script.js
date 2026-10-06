/**
 * Attendance Management System
 * Main JavaScript file for enhancing functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips and popovers if available
    initializeBootstrapComponents();
    
    // Set up form enhancements
    enhanceForms();
    
    // Add table enhancements
    enhanceTables();
    
    // Add attendance marking enhancements
    enhanceAttendanceMarking();
    
    // Setup Flash Message Auto-dismissal
    setupFlashMessages();
    
    // Print report formatting
    setupPrintReport();
});

/**
 * Initialize Bootstrap components
 */
function initializeBootstrapComponents() {
    // Initialize tooltips if Bootstrap 5 is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
        
        // Initialize popovers
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }
}

/**
 * Form enhancements
 */
function enhanceForms() {
    // Date picker default to today
    const dateInputs = document.querySelectorAll('input[type="date"]');
    dateInputs.forEach(function(input) {
        if (!input.value) {
            const today = new Date().toISOString().split('T')[0];
            input.value = today;
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                highlightInvalidFields(form);
            }
            form.classList.add('was-validated');
        });
    });
    
    // Auto-submit on course select (for analysis page)
    const courseSelects = document.querySelectorAll('select#course_id[onchange="this.form.submit()"]');
    courseSelects.forEach(function(select) {
        select.addEventListener('change', function() {
            this.form.submit();
        });
    });
}

/**
 * Highlight invalid form fields
 */
function highlightInvalidFields(form) {
    const invalidFields = form.querySelectorAll(':invalid');
    invalidFields.forEach(function(field) {
        field.classList.add('is-invalid');
        
        // Add feedback message if not already present
        const parent = field.parentElement;
        if (!parent.querySelector('.invalid-feedback')) {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.textContent = field.validationMessage || 'This field is required';
            parent.appendChild(feedback);
        }
    });
}

/**
 * Table enhancements
 */
function enhanceTables() {
    // Add sorting functionality to tables
    const tables = document.querySelectorAll('.table-responsive .table');
    tables.forEach(function(table) {
        const headers = table.querySelectorAll('th');
        headers.forEach(function(header, index) {
            if (!header.classList.contains('no-sort')) {
                header.style.cursor = 'pointer';
                header.dataset.bsToggle = 'tooltip';
                header.title = 'Click to sort';
                header.addEventListener('click', function() {
                    sortTable(table, index);
                });
            }
        });
    });

    // Add row highlighting on hover
    const tableRows = document.querySelectorAll('.table tbody tr');
    tableRows.forEach(function(row) {
        row.addEventListener('mouseenter', function() {
            this.style.backgroundColor = 'rgba(37, 99, 235, 0.1)';
        });
        row.addEventListener('mouseleave', function() {
            this.style.backgroundColor = '';
        });
    });
}

/**
 * Sort table by column
 */
function sortTable(table, colIndex) {
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    const header = table.querySelectorAll('th')[colIndex];
    
    // Toggle sort direction
    const ascending = !header.classList.contains('asc');
    
    // Clear all sort indicators
    table.querySelectorAll('th').forEach(th => {
        th.classList.remove('asc', 'desc');
    });
    
    // Set sort indicator
    header.classList.add(ascending ? 'asc' : 'desc');
    
    // Sort rows
    rows.sort((a, b) => {
        const aValue = a.querySelectorAll('td')[colIndex].textContent.trim();
        const bValue = b.querySelectorAll('td')[colIndex].textContent.trim();
        
        // Check if the values are numbers
        const aNum = parseFloat(aValue.replace('%', ''));
        const bNum = parseFloat(bValue.replace('%', ''));
        
        if (!isNaN(aNum) && !isNaN(bNum)) {
            return ascending ? aNum - bNum : bNum - aNum;
        }
        
        // Sort as strings
        return ascending 
            ? aValue.localeCompare(bValue) 
            : bValue.localeCompare(aValue);
    });
    
    // Reappend rows in new order
    rows.forEach(row => tbody.appendChild(row));
}

/**
 * Attendance marking enhancements
 */
function enhanceAttendanceMarking() {
    // Check for attendance marking page
    const attendanceForm = document.querySelector('form[action*="teacher_attendance"]');
    if (!attendanceForm) return;
    
    // Add select all/none buttons if we have checkboxes
    const checkboxes = attendanceForm.querySelectorAll('input[type="checkbox"][name="present"]');
    if (checkboxes.length > 0) {
        const tableContainer = attendanceForm.querySelector('.table-responsive');
        if (tableContainer) {
            // Create button container
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'mb-3';
            
            // Select All button
            const selectAllBtn = document.createElement('button');
            selectAllBtn.type = 'button';
            selectAllBtn.className = 'btn btn-sm btn-outline-primary me-2';
            selectAllBtn.textContent = 'Select All';
            selectAllBtn.addEventListener('click', function() {
                checkboxes.forEach(cb => cb.checked = true);
            });
            
            // Select None button
            const selectNoneBtn = document.createElement('button');
            selectNoneBtn.type = 'button';
            selectNoneBtn.className = 'btn btn-sm btn-outline-secondary';
            selectNoneBtn.textContent = 'Select None';
            selectNoneBtn.addEventListener('click', function() {
                checkboxes.forEach(cb => cb.checked = false);
            });
            
            // Add buttons to container
            buttonContainer.appendChild(selectAllBtn);
            buttonContainer.appendChild(selectNoneBtn);
            
            // Insert before table
            tableContainer.parentNode.insertBefore(buttonContainer, tableContainer);
        }
        
        // Add ability to click anywhere in row to toggle checkbox
        const rows = attendanceForm.querySelectorAll('tbody tr');
        rows.forEach(function(row) {
            row.style.cursor = 'pointer';
            row.addEventListener('click', function(e) {
                // Don't toggle if clicking on the checkbox itself
                if (e.target.type !== 'checkbox') {
                    const checkbox = this.querySelector('input[type="checkbox"]');
                    checkbox.checked = !checkbox.checked;
                }
            });
        });
    }
}

/**
 * Setup Flash Messages Auto-dismissal
 */
function setupFlashMessages() {
    const flashMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
    flashMessages.forEach(function(alert) {
        // Auto dismiss after 5 seconds
        setTimeout(function() {
            fadeOut(alert);
        }, 5000);
        
        // Add dismiss button if not already present
        if (!alert.querySelector('.btn-close')) {
            const closeButton = document.createElement('button');
            closeButton.type = 'button';
            closeButton.className = 'btn-close';
            closeButton.setAttribute('aria-label', 'Close');
            closeButton.addEventListener('click', function() {
                fadeOut(alert);
            });
            alert.appendChild(closeButton);
            alert.style.display = 'flex';
            alert.style.justifyContent = 'space-between';
            alert.style.alignItems = 'center';
        }
    });
}

/**
 * Fade out element and remove it
 */
function fadeOut(element) {
    let opacity = 1;
    const timer = setInterval(function() {
        if (opacity <= 0.1) {
            clearInterval(timer);
            element.style.display = 'none';
            element.parentNode.removeChild(element);
        }
        element.style.opacity = opacity;
        opacity -= 0.1;
    }, 50);
}

/**
 * Setup print report formatting
 */
function setupPrintReport() {
    // Check if on analysis page with print button
    const printButton = document.querySelector('button[onclick="window.print()"]');
    if (!printButton) return;
    
    printButton.addEventListener('click', function(e) {
        // Add a print-specific header with the date
        const reportHeader = document.createElement('div');
        reportHeader.className = 'print-header d-none';
        
        const currentDate = new Date().toLocaleDateString();
        const courseName = document.querySelector('.card-header h5').textContent;
        
        reportHeader.innerHTML = `
            <h1 class="text-center">Attendance Report</h1>
            <h3 class="text-center">${courseName}</h3>
            <p class="text-center">Generated on ${currentDate}</p>
            <hr>
        `;
        
        // Add to document before printing
        const contentContainer = document.querySelector('.container.mt-4');
        contentContainer.insertBefore(reportHeader, contentContainer.firstChild);
        
        // Remove class that hides it in normal view
        reportHeader.classList.remove('d-none');
        
        // Print
        window.print();
        
        // After printing, remove the header
        setTimeout(function() {
            reportHeader.remove();
        }, 500);
    });
}

/**
 * Toggle Dark/Light mode (Optional)
 * This is an additional feature that could be added with a button in the UI
 */
function toggleDarkMode() {
    document.body.classList.toggle('dark-mode');
    
    // Save preference to localStorage
    const isDarkMode = document.body.classList.contains('dark-mode');
    localStorage.setItem('darkMode', isDarkMode ? 'enabled' : 'disabled');
}

// Check for saved dark mode preference on load
const savedDarkMode = localStorage.getItem('darkMode');
if (savedDarkMode === 'enabled') {
    document.body.classList.add('dark-mode');
}

// Add dark mode toggle button when applicable
// This can be uncommented and a button can be added to the UI
/*
const darkModeToggle = document.getElementById('dark-mode-toggle');
if (darkModeToggle) {
    darkModeToggle.addEventListener('click', toggleDarkMode);
}
*/