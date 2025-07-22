// Main JavaScript for Ralph Wilson Catalog

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Search functionality
    initializeSearch();
    
    // Product card animations
    initializeProductCards();
    
    // Filter functionality
    initializeFilters();
    
    // Admin functions
    initializeAdmin();
});

function initializeSearch() {
    const searchInput = document.querySelector('input[name="search"]');
    if (!searchInput) return;
    
    let searchTimeout;
    
    searchInput.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        const query = this.value.trim();
        
        if (query.length < 2) {
            hideSuggestions();
            return;
        }
        
        searchTimeout = setTimeout(() => {
            fetchSearchSuggestions(query);
        }, 300);
    });
    
    // Hide suggestions when clicking outside
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.search-container')) {
            hideSuggestions();
        }
    });
}

function fetchSearchSuggestions(query) {
    fetch(`/api/search?q=${encodeURIComponent(query)}&limit=5`)
        .then(response => response.json())
        .then(data => {
            showSuggestions(data.products);
        })
        .catch(error => {
            console.error('Error fetching suggestions:', error);
        });
}

function showSuggestions(products) {
    const searchContainer = document.querySelector('.search-container');
    if (!searchContainer) return;
    
    let suggestionsDiv = searchContainer.querySelector('.search-suggestions');
    if (!suggestionsDiv) {
        suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'search-suggestions';
        searchContainer.appendChild(suggestionsDiv);
    }
    
    if (products.length === 0) {
        hideSuggestions();
        return;
    }
    
    suggestionsDiv.innerHTML = products.map(product => `
        <div class="search-suggestion" onclick="selectSuggestion('${product.name}')">
            <strong>${product.name}</strong>
            <br>
            <small class="text-muted">${product.category}</small>
        </div>
    `).join('');
    
    suggestionsDiv.style.display = 'block';
}

function hideSuggestions() {
    const suggestionsDiv = document.querySelector('.search-suggestions');
    if (suggestionsDiv) {
        suggestionsDiv.style.display = 'none';
    }
}

function selectSuggestion(productName) {
    const searchInput = document.querySelector('input[name="search"]');
    if (searchInput) {
        searchInput.value = productName;
        searchInput.form.submit();
    }
    hideSuggestions();
}

function initializeProductCards() {
    const productCards = document.querySelectorAll('.product-card, .category-card');
    
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
            this.style.transition = 'transform 0.3s ease';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

function initializeFilters() {
    const filterForm = document.querySelector('.filter-sidebar form');
    if (!filterForm) return;
    
    // Auto-submit on select change
    const selectElements = filterForm.querySelectorAll('select');
    selectElements.forEach(select => {
        select.addEventListener('change', function() {
            filterForm.submit();
        });
    });
    
    // Clear filters
    const clearButton = filterForm.querySelector('.btn-outline-secondary');
    if (clearButton) {
        clearButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Clear all form inputs
            filterForm.querySelectorAll('input, select').forEach(input => {
                if (input.type === 'text') {
                    input.value = '';
                } else if (input.tagName === 'SELECT') {
                    input.selectedIndex = 0;
                }
            });
            
            // Submit form
            filterForm.submit();
        });
    }
}

function initializeAdmin() {
    // Scraping progress
    const scrapeBtn = document.getElementById('scrapeBtn');
    if (scrapeBtn) {
        scrapeBtn.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Iniciando...';
            
            // Re-enable after 5 seconds
            setTimeout(() => {
                this.disabled = false;
                this.innerHTML = '<i class="fas fa-play"></i> Iniciar Scraping';
            }, 5000);
        });
    }
    
    // Auto-refresh for running scraping
    if (window.location.pathname === '/admin') {
        const statusBadges = document.querySelectorAll('.badge');
        const isRunning = Array.from(statusBadges).some(badge => 
            badge.textContent.includes('Ejecutándose')
        );
        
        if (isRunning) {
            setTimeout(() => {
                window.location.reload();
            }, 30000); // Refresh every 30 seconds
        }
    }
}

// Image modal functionality
function openImageModal(imageSrc, imageAlt) {
    if (!imageSrc) return;
    
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.8);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1050;
        cursor: pointer;
    `;
    
    const img = document.createElement('img');
    img.src = imageSrc;
    img.alt = imageAlt || '';
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        border-radius: 10px;
    `;
    
    modal.appendChild(img);
    document.body.appendChild(modal);
    
    modal.addEventListener('click', function() {
        document.body.removeChild(modal);
    });
    
    // Close on Escape key
    document.addEventListener('keydown', function escapeHandler(e) {
        if (e.key === 'Escape') {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
            document.removeEventListener('keydown', escapeHandler);
        }
    });
}

// Utility functions
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (document.body.contains(alertDiv)) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert('Copiado al portapapeles', 'success');
    }).catch(() => {
        showAlert('Error al copiar', 'danger');
    });
}

// Export functions for global use
window.openImageModal = openImageModal;
window.showAlert = showAlert;
window.copyToClipboard = copyToClipboard;
