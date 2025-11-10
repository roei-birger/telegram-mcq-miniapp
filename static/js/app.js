/**
 * MCQ Bot Web App JavaScript
 * Client-side functionality for the web interface
 */

// Wait for DOM to load
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    console.log('MCQ Bot Web App initialized');
    
    // Add fade-in animation to main content
    const mainContent = document.querySelector('main');
    if (mainContent) {
        mainContent.classList.add('fade-in');
    }
    
    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeBtn = alert.querySelector('.btn-close');
            if (closeBtn && alert.classList.contains('show')) {
                closeBtn.click();
            }
        }, 5000);
    });
    
    // Add smooth scroll to anchor links
    setupSmoothScroll();
    
    // Setup file drag and drop if on upload page
    setupFileDragDrop();
    
    // Setup keyboard shortcuts
    setupKeyboardShortcuts();
}

/**
 * Setup smooth scrolling for anchor links
 */
function setupSmoothScroll() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(function(link) {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            const target = document.querySelector(href);
            
            if (target) {
                e.preventDefault();
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Setup drag and drop functionality for file upload
 */
function setupFileDragDrop() {
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('files');
    
    if (!uploadForm || !fileInput) return;
    
    const dropZone = uploadForm.parentElement;
    
    // Add drag and drop styling
    dropZone.style.transition = 'all 0.3s ease';
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop zone when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    dropZone.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        dropZone.style.backgroundColor = '#e3f2fd';
        dropZone.style.borderColor = '#2196f3';
        dropZone.style.transform = 'scale(1.02)';
    }
    
    function unhighlight(e) {
        dropZone.style.backgroundColor = '';
        dropZone.style.borderColor = '';
        dropZone.style.transform = '';
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        fileInput.files = files;
        fileInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

/**
 * Setup keyboard shortcuts
 */
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter to submit forms
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const activeForm = document.activeElement.closest('form');
            if (activeForm) {
                const submitBtn = activeForm.querySelector('button[type="submit"]');
                if (submitBtn) {
                    submitBtn.click();
                }
            }
        }
        
        // Escape to close modals or go back
        if (e.key === 'Escape') {
            const backBtn = document.querySelector('a[href*="back"], .btn-secondary');
            if (backBtn) {
                backBtn.click();
            }
        }
    });
}

/**
 * Utility Functions
 */

/**
 * Format file size for display
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Get file type icon class
 * @param {string} filename - Name of the file
 * @returns {string} CSS class for file icon
 */
function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    
    const iconMap = {
        'pdf': 'fas fa-file-pdf text-danger',
        'docx': 'fas fa-file-word text-primary',
        'doc': 'fas fa-file-word text-primary',
        'txt': 'fas fa-file-alt text-secondary',
        'default': 'fas fa-file text-muted'
    };
    
    return iconMap[ext] || iconMap['default'];
}

/**
 * Show loading state on element
 * @param {HTMLElement} element - Element to show loading on
 * @param {string} text - Loading text (optional)
 */
function showLoading(element, text = 'טוען...') {
    if (!element) return;
    
    element.disabled = true;
    element.classList.add('loading');
    
    const originalText = element.innerHTML;
    element.dataset.originalText = originalText;
    
    element.innerHTML = `<i class="fas fa-spinner fa-spin me-2"></i>${text}`;
}

/**
 * Hide loading state on element
 * @param {HTMLElement} element - Element to hide loading from
 */
function hideLoading(element) {
    if (!element) return;
    
    element.disabled = false;
    element.classList.remove('loading');
    
    if (element.dataset.originalText) {
        element.innerHTML = element.dataset.originalText;
        delete element.dataset.originalText;
    }
}

/**
 * Show toast notification
 * @param {string} message - Message to show
 * @param {string} type - Type of notification (success, error, info, warning)
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    toast.style.cssText = 'top: 20px; left: 50%; transform: translateX(-50%); z-index: 9999; min-width: 300px;';
    
    const iconMap = {
        'success': 'fas fa-check-circle',
        'error': 'fas fa-exclamation-triangle',
        'warning': 'fas fa-exclamation-triangle',
        'info': 'fas fa-info-circle'
    };
    
    const icon = iconMap[type] || iconMap['info'];
    
    toast.innerHTML = `
        <i class="${icon} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentNode) {
            toast.remove();
        }
    }, 5000);
}

/**
 * Validate file before upload
 * @param {File} file - File to validate
 * @returns {object} Validation result
 */
function validateFile(file) {
    const maxSize = 15 * 1024 * 1024; // 15MB
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
    const allowedExtensions = ['.pdf', '.docx', '.txt'];
    
    // Check file size
    if (file.size > maxSize) {
        return {
            valid: false,
            error: `הקובץ "${file.name}" גדול מדי. גודל מקסימלי: 15MB`
        };
    }
    
    // Check file extension
    const extension = '.' + file.name.split('.').pop().toLowerCase();
    if (!allowedExtensions.includes(extension)) {
        return {
            valid: false,
            error: `סוג קובץ לא נתמך: ${file.name}. סוגים נתמכים: PDF, DOCX, TXT`
        };
    }
    
    return { valid: true };
}

/**
 * Handle network errors gracefully
 */
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e);
});

window.addEventListener('unhandledrejection', function(e) {
    console.error('Unhandled promise rejection:', e);
});

/**
 * Performance monitoring
 */
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(function() {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                console.log('Page load time:', Math.round(perfData.loadEventEnd - perfData.loadEventStart), 'ms');
            }
        }, 0);
    });
}

// Expose utility functions globally
window.MCQBot = {
    formatFileSize,
    getFileIcon,
    showLoading,
    hideLoading,
    showToast,
    validateFile
};