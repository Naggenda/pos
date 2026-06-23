// Configuration
const API_BASE_URL = 'http://localhost:5000/api';
let cart = [];
let selectedTransactionId = null;
let currentUser = null;

// Session Timeout Configuration (10 minutes = 600000 ms)
const SESSION_TIMEOUT_MS = 10 * 60 * 1000; // 10 minutes
let inactivityTimer = null;
let warningTimer = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthentication();
    setupNavigation();
    loadDashboard();
    loadProducts();
    testEfrisConnection();
    setupInactivityTimeout();
});

// Authentication Check
function checkAuthentication() {
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    
    if (!token) {
        // Redirect to login
        window.location.href = 'login.html';
        return;
    }
    
    // Verify token
    fetch(`${API_BASE_URL}/auth/verify-token`, {
        headers: {
            'Authorization': `Bearer ${token}`
        }
    })
    .then(response => {
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (data && data.valid) {
            currentUser = {
                id: data.user_id,
                role: data.role,
                username: localStorage.getItem('username') || sessionStorage.getItem('username')
            };
            updateUserInfo();
        }
    })
    .catch(error => {
        console.error('Error verifying token:', error);
    });
}

function updateUserInfo() {
    const userInfoElement = document.querySelector('.user-info');
    if (userInfoElement && currentUser) {
        userInfoElement.textContent = `${currentUser.username} (${currentUser.role})`;
    }
}

function getAuthHeaders() {
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
    };
}

// Navigation Setup
function setupNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const section = this.getAttribute('data-section');
            navigateToSection(section);
        });
    });
}

function navigateToSection(section) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
    
    // Show selected section
    const selectedSection = document.getElementById(section);
    if (selectedSection) {
        selectedSection.classList.add('active');
    }
    
    // Update nav links
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
    });
    document.querySelector(`[data-section="${section}"]`).classList.add('active');
    
    // Update section title
    const titles = {
        dashboard: 'Dashboard',
        sales: 'Point of Sale',
        products: 'Products Management',
        transactions: 'Sales Transactions',
        efris: 'EFRIS Integration'
    };
    document.getElementById('section-title').textContent = titles[section] || 'Dashboard';
    
    // Load section-specific data
    if (section === 'transactions') {
        loadTransactions();
    } else if (section === 'products') {
        loadProductsTable();
    }
}

// Dashboard Functions
async function loadDashboard() {
    try {
        const response = await fetch(`${API_BASE_URL}/dashboard/summary`, {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        
        const data = await response.json();
        
        document.getElementById('stat-sales').textContent = data.total_sales;
        document.getElementById('stat-revenue').textContent = `UGX ${formatNumber(data.total_revenue)}`;
        document.getElementById('stat-tax').textContent = `UGX ${formatNumber(data.total_tax)}`;
        document.getElementById('stat-efris').textContent = data.efris_submitted;
        document.getElementById('stat-lowstock').textContent = data.low_stock_count;
        document.getElementById('stat-failed').textContent = data.efris_failed;
    } catch (error) {
        console.error('Error loading dashboard:', error);
        showNotification('Error loading dashboard', 'error');
    }
}

// Products Functions
async function loadProducts() {
    try {
        const response = await fetch(`${API_BASE_URL}/products`, {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        
        const products = await response.json();
        
        const productsList = document.getElementById('products-list');
        productsList.innerHTML = '';
        
        products.forEach(product => {
            const card = document.createElement('div');
            card.className = 'product-card';
            card.innerHTML = `
                <h5>${product.name}</h5>
                <p>SKU: ${product.sku}</p>
                <p>Stock: ${product.quantity}</p>
                <div class="product-price">UGX ${formatNumber(product.price)}</div>
            `;
            card.addEventListener('click', () => addToCart(product));
            productsList.appendChild(card);
        });, {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        
    } catch (error) {
        console.error('Error loading products:', error);
        showNotification('Error loading products', 'error');
    }
}

async function loadProductsTable() {
    try {
        const response = await fetch(`${API_BASE_URL}/products`);
        const products = await response.json();
        
        const tbody = document.getElementById('products-tbody');
        tbody.innerHTML = '';
        
        products.forEach(product => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${product.name}</td>
                <td>${product.sku}</td>
                <td>${product.category || '-'}</td>
                <td>UGX ${formatNumber(product.price)}</td>
                <td>${product.quantity}</td>
                <td>${product.tax_rate}%</td>
                <td>
                    <button class="btn btn-secondary" onclick="editProduct('${product.id}')">Edit</button>
                    <button class="btn btn-danger" onclick="deleteProduct('${product.id}')">Delete</button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading products table:', error);
        showNotification('Error loading products', 'error');
    }
}

function showAddProductForm() {
    document.getElementById('add-product-form').style.display = 'block';
}

function hideAddProductForm() {
    document.getElementById('add-product-form').style.display = 'none';
    document.getElementById('product-name').value = '';
    document.getElementById('product-sku').value = '';
    document.getElementById('product-category').value = '';
    if (currentUser.role !== 'ADMIN' && currentUser.role !== 'MANAGER') {
        showNotification('You do not have permission to add products', 'error');
        return;
    }
    
    const productData = {
        name: document.getElementById('product-name').value,
        sku: document.getElementById('product-sku').value,
        category: document.getElementById('product-category').value,
        price: parseFloat(document.getElementById('product-price').value),
        quantity: parseInt(document.getElementById('product-quantity').value),
        tax_rate: parseFloat(document.getElementById('product-tax').value) / 100,
        description: document.getElementById('product-description').value
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/products`, {
            method: 'POST',
            headers: getAuthHeaders(),
            body: JSON.stringify(productData)
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        
        if (response.ok) {
            showNotification('Product added successfully', 'success');
            hideAddProductForm();
            loadProducts();
            loadProductsTable();
        } else {
            const error = await response.json();
            showNotification(error.error || 'Error adding product', 'error');
        }
    } catch (error) {
        console.error('Error saving product:', error);
        showNotification('Error saving product', 'error');
    }
}

async function deleteProduct(productId) {
    if (currentUser.role !== 'ADMIN' && currentUser.role !== 'MANAGER') {
        showNotification('You do not have permission to delete products', 'error');
        return;
    }
    
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'DELETE',
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
}

async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/products/${productId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            showNotification('Product deleted successfully', 'success');
            loadProducts();
            loadProductsTable();
        } else {
            showNotification('Error deleting product', 'error');
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        showNotification('Error deleting product', 'error');
    }
}

// Cart Functions
function addToCart(product) {
    const existingItem = cart.find(item => item.product_id === product.id);
    
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            product_id: product.id,
            product_name: product.name,
            unit_price: product.price,
            tax_rate: product.tax_rate,
            quantity: 1
        });
    }
    
    updateInvoice();
    showNotification(`${product.name} added to cart`, 'info');
}

function removeFromCart(index) {
    cart.splice(index, 1);
    updateInvoice();
}

function updateInvoice() {
    const invoiceItems = document.getElementById('invoice-items');
    
    if (cart.length === 0) {
        invoiceItems.innerHTML = '<p class="empty-message">No items added</p>';
        document.getElementById('subtotal').textContent = 'UGX 0';
        document.getElementById('tax-amount').textContent = 'UGX 0';
        document.getElementById('total-amount').textContent = 'UGX 0';
        return;
    }
    
    invoiceItems.innerHTML = '';
    let subtotal = 0;
    let totalTax = 0;
    
    cart.forEach((item, index) => {
        const itemSubtotal = item.quantity * item.unit_price;
        const itemTax = itemSubtotal * item.tax_rate;
        
        const itemDiv = document.createElement('div');
        itemDiv.className = 'invoice-item';
        itemDiv.innerHTML = `
            <div class="invoice-item-info">
                <div class="invoice-item-name">${item.product_name}</div>
                <div class="invoice-item-qty">Qty: 
                    <input type="number" value="${item.quantity}" min="1" style="width: 50px; padding: 2px;" 
                           onchange="updateItemQuantity(${index}, this.value)">
                </div>
            </div>
            <div class="invoice-item-price">UGX ${formatNumber(itemSubtotal)}</div>
            <button class="invoice-item-remove" onclick="removeFromCart(${index})">✕</button>
        `;
        invoiceItems.appendChild(itemDiv);
        
        subtotal += itemSubtotal;
        totalTax += itemTax;
    });
    
    const discount = parseFloat(document.getElementById('discount').value) || 0;
    const total = subtotal - discount;
    
    document.getElementById('subtotal').textContent = `UGX ${formatNumber(subtotal)}`;
    document.getElementById('tax-amount').textContent = `UGX ${formatNumber(totalTax)}`;
    document.getElementById('total-amount').textContent = `UGX ${formatNumber(total)}`;
}

function updateItemQuantity(index, newQuantity) {
    cart[index].quantity = parseInt(newQuantity) || 1;
    updateInvoice();
}

function clearCart() {
    if (confirm('Are you sure you want to clear the cart?')) {
        cart = [];
        updateInvoice();
        showNotification('Cart cleared', 'info');
    }
}

async function completeSale() {
    if (cart.length =getAuthHeaders(),
            body: JSON.stringify(saleData)
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
    const discount = parseFloat(document.getElementById('discount').value) || 0;
    const paymentMethod = document.getElementById('payment-method').value;
    
    let subtotal = 0;
    let totalTax = 0;
    
    cart.forEach(item => {
        const itemSubtotal = item.quantity * item.unit_price;
        const itemTax = itemSubtotal * item.tax_rate;
        subtotal += itemSubtotal;
        totalTax += itemTax;
    });
    
    const saleData = {
        items: cart,
        discount_amount: discount,
        payment_method: paymentMethod,
        total_amount: subtotal,
        tax_amount: totalTax,
        net_amount: subtotal - discount
    };
    
    try {
        const response = await fetch(`${API_BASE_URL}/sales`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(saleData)
        });
        
        if (response.ok) {
            const sale = await response.json();
            showNotification(`Sale completed! Receipt: ${sale.receipt_number}`, 'success');
            
            // Submit to EFRIS automatically
            submitSaleToEfris(sale.id);
            
            // Clear cart
            cart = [];
            updateInvoice();
            loadDashboard();
            
            // Print receipt option
            if (confirm('Do you want to , {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        int the receipt?')) {
                printReceipt(sale);
            }
        } else {
            const error = await response.json();
            showNotification(error.error || 'Error completing sale', 'error');
        }
    } catch (error) {
        console.error('Error completing sale:', error);
        showNotification('Error completing sale', 'error');
    }
}

// Transactions Functions
async function loadTransactions() {
    try {
        const status = document.getElementById('filter-status').value;
        const date = document.getElementById('filter-date').value;
        
        let url = `${API_BASE_URL}/sales`;
        const params = [];
        if (status) params.push(`status=${status}`);
        if (date) params.push(`date_from=${date}`);
        if (params.length) url += '?' + params.join('&');
        
        const response = await fetch(url);
        const sales = await response.json();
        
        const tbody = document.getElementById('transactions-tbody');
        tbody.innerHTML = '';
        
        sales.forEach(sale => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${sale.receipt_number}</td>
                <td>${new Date(sale.created_at).toLocaleDateString()}</td>
                <td>UGX ${formatNumber(sale.total_amount)}</td>
                <td>UGX ${formatNumber(sale.tax_amount)}</td>
                <td>${sale.payment_method}</td>
                <td>
                    <span class="status-badge ${sale.efris_status.toLowerCase()}">
                        ${sale.efris_status}
                    </span>
                </td>
                <td>
                    <button class="btn btn-secondary" onclick="viewTransactionDetails('${sale.id}')">View</button>
                    ${sale.efris_status === 'PENDING' ? 
                        `<button class="btn btn-primary" onclick="submitTransactionToEfris('${sale.id}')">Submit EFRIS</button>` 
                        : ''}, {
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        }
        
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading transactions:', error);
        showNotification('Error loading transactions', 'error');
    }
}

async function viewTransactionDetails(saleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/sales/${saleId}`);
        const sale = await response.json();
        
        selectedTransactionId = saleId;
        
        let itemsHtml = '<table style="width: 100%; margin-bottom: 20px;">';
        itemsHtml += '<tr><th>Product</th><th>Qty</th><th>Price</th><th>Tax</th><th>Total</th></tr>';
        
        sale.items.forEach(item => {
            itemsHtml += `
                <tr>
                    <td>${item.product_name}</td>
                    <td>${item.quantity}</td>
                    <td>UGX ${formatNumber(item.unit_price)}</td>
                    <td>UGX ${formatNumber(item.tax_amount)}</td>
                    <td>UGX ${formatNumber(item.subtotal)}</td>
                </tr>
            `;
        });
        
        itemsHtml += '</table>';
        
        const detailsDiv = document.getElementById('transaction-details');
        detailsDiv.innerHTML = `
            <div style="margin-bottom: 20px;">
                <p><strong>Receipt Number:</strong> ${sale.receipt_number}</p>
                <p><strong>Date:</strong> ${new Date(sale.created_at).toLocaleString()}</p>
                <p><strong>Payment Method:</strong> ${sale.payment_method}</p>
                <p><strong>EFRIS Status:</strong> <span class="status-badge ${sale.efris_status.toLowerCase()}">${sale.efris_status}</span></p>
                ${sale.efris_receipt_code ? `<p><strong>Receipt Code:</strong> ${sale.efris_receipt_code}</p>` : ''}
            </div>
            ${itemsHtml}
            <div>
                <p><strong>Subtotal:</strong> UGX ${formatNumber(sale.total_amount)}</p>
                <p><strong>Tax:</strong> UGX ${formatNumber(sale.tax_amount)}</p>
                <p><strong>Discount:</strong> UGX ${formatNumber(sale.discount_amount)}</p>
                <p style="font-size: 16px; font-weight: bold; color: #2563eb;">
                    <strong>Net Amount:</strong> UGX ${formatNumber(sale.net_amount)}
                </p>,
            headers: getAuthHeaders()
        });
        
        if (response.status === 401) {
            clearAuthentication();
            window.location.href = 'login.html';
            return;
        } </div>
        `;
        
        // Show/hide EFRIS submit button
        const efrisBtn = document.getElementById('submit-efris-btn');
        if (sale.efris_status === 'PENDING') {
            efrisBtn.style.display = 'block';
        } else {
            efrisBtn.style.display = 'none';
        }
        
        openTransactionModal();
    } catch (error) {
        console.error('Error viewing transaction:', error);
        showNotification('Error loading transaction details', 'error');
    }
}

async function submitSaleToEfris(saleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/sales/${saleId}/submit-efris`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification(`Successfully submitted to EFRIS. Receipt Code: ${result.receipt_code}`, 'success');
            loadTransactions();
        } else {
            showNotification(`EFRIS submission failed: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error submitting to EFRIS:', error);
        showNotification('Error submitting to EFRIS', 'error');
    }
}

async function submitTransactionToEfris(saleId = null) {
    const id = saleId || selectedTransactionId;
    if (!id) {
        showNotification('No transaction selected', 'error');
        return;
    }
    
    await submitSaleToEfris(id);
    closeTransactionModal();
}

// EFRIS Functions
async function testEfrisConnection() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`, {
            headers: getAuthHeaders()
        });
        if (response.ok) {
            document.getElementById('efris-connection').textContent = '✓ Connected';
            document.getElementById('efris-connection').className = 'status-connected';
        } else {
            document.getElementById('efris-connection').textContent = '✗ Connection Failed';
            document.getElementById('efris-connection').className = 'status-error';
        }
    } catch (error) {
        document.getElementById('efris-connection').textContent = '✗ Connection Failed';
        document.getElementById('efris-connection').className = 'status-error';
    }
}

// Modal Functions
function openTransactionModal() {
    document.getElementById('transaction-modal').classList.add('active');
}

function closeTransactionModal() {
    document.getElementById('transaction-modal').classList.remove('active');
    selectedTransactionId = null;
}

// Utility Functions
function formatNumber(num) {
    return new Intl.NumberFormat('en-US').format(num);
}

function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification show ${type}`;
    
    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

function printReceipt(sale) {
    let receiptHtml = `
        <html>
        <head>
            <title>Receipt ${sale.receipt_number}</title>
            <style>
                body { font-family: monospace; max-width: 400px; margin: 0 auto; padding: 20px; }
                h3 { text-align: center; }
                .divider { text-align: center; margin: 10px 0; }
                table { width: 100%; }
                .summary { margin: 20px 0; }
                .total { font-weight: bold; font-size: 18px; }
            </style>
        </head>
        <body>
            <h3>POS Receipt</h3>
            <div class="divider">==============================</div>
            <p><strong>Receipt #:</strong> ${sale.receipt_number}</p>
            <p><strong>Date:</strong> ${new Date(sale.created_at).toLocaleString()}</p>
            <p><strong>Payment:</strong> ${sale.payment_method}</p>
            <div class="divider">==============================</div>
            
        // Get token
        const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        
        // Call logout endpoint
        if (token) {
            fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: getAuthHeaders()
            }).catch(error => console.error('Logout error:', error));
        }
        
        // Clear authentication
        clearAuthentication();
        
        // Redirect to login
        window.location.href = 'login.html';
    }
}

function clearAuthentication() {
    localStorage.removeItem('authToken');
    localStorage.removeItem('userRole');
    localStorage.removeItem('username');
    sessionStorage.removeItem('authToken');
    sessionStorage.removeItem('userRole');
    sessionStorage.removeItem('username');
    currentUser = null;;
    
    sale.items.forEach(item => {
        receiptHtml += `
            <tr>
                <td>${item.product_name}</td>
                <td>${item.quantity}</td>
                <td>UGX ${formatNumber(item.unit_price)}</td>
                <td>UGX ${formatNumber(item.subtotal)}</td>
            </tr>
        `;
    });
    
    receiptHtml += `
            </table>
            <div class="summary">
                <p><strong>Subtotal:</strong> UGX ${formatNumber(sale.total_amount)}</p>
                <p><strong>Tax (18%):</strong> UGX ${formatNumber(sale.tax_amount)}</p>
                <p><strong>Discount:</strong> UGX ${formatNumber(sale.discount_amount)}</p>
                <p class="total"><strong>TOTAL:</strong> UGX ${formatNumber(sale.net_amount)}</p>
            </div>
            <div class="divider">==============================</div>
            <p style="text-align: center; font-size: 12px;">Thank you for your purchase!</p>
            ${sale.efris_receipt_code ? `<p style="text-align: center; font-size: 10px;">EFRIS Code: ${sale.efris_receipt_code}</p>` : ''}
        </body>
        </html>
    `;
    
    const printWindow = window.open('', '', 'height=400,width=600');
    printWindow.document.write(receiptHtml);
    printWindow.document.close();
    setTimeout(() => printWindow.print(), 250);
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        // Get token
        const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
        
        // Call logout endpoint
        if (token) {
            fetch(`${API_BASE_URL}/auth/logout`, {
                method: 'POST',
                headers: getAuthHeaders()
            }).catch(error => console.error('Logout error:', error));
        }
        
        // Clear authentication
        clearAuthentication();
        
        // Redirect to login
        window.location.href = 'login.html';
    }
}

// Session Inactivity Timeout Functions
function setupInactivityTimeout() {
    // Track activity events
    document.addEventListener('mousedown', resetInactivityTimer);
    document.addEventListener('keydown', resetInactivityTimer);
    document.addEventListener('touchstart', resetInactivityTimer);
    document.addEventListener('click', resetInactivityTimer);
    
    // Start the inactivity timer
    resetInactivityTimer();
}

function resetInactivityTimer() {
    // Clear existing timers
    if (inactivityTimer) clearTimeout(inactivityTimer);
    if (warningTimer) clearTimeout(warningTimer);
    
    // Set warning timer (9 minutes - show warning 1 minute before logout)
    warningTimer = setTimeout(function() {
        showInactivityWarning();
    }, SESSION_TIMEOUT_MS - 60000);
    
    // Set logout timer (10 minutes)
    inactivityTimer = setTimeout(function() {
        handleInactivityLogout();
    }, SESSION_TIMEOUT_MS);
}

function showInactivityWarning() {
    // Check if user is still on the page
    if (document.hidden) return;
    
    // Show warning dialog
    const warning = document.createElement('div');
    warning.className = 'inactivity-warning';
    warning.innerHTML = `
        <div class="warning-content">
            <h3>⏱️ Session Timeout Warning</h3>
            <p>Your session will expire in <strong>1 minute</strong> due to inactivity.</p>
            <p>Click "Stay Logged In" to continue working.</p>
            <div class="warning-actions">
                <button class="btn btn-primary" onclick="resetInactivityTimer(); this.parentElement.parentElement.parentElement.remove();">
                    Stay Logged In
                </button>
                <button class="btn btn-secondary" onclick="performLogout();">
                    Logout Now
                </button>
            </div>
        </div>
    `;
    document.body.appendChild(warning);
}

function handleInactivityLogout() {
    // Perform logout due to inactivity
    performLogout('Your session has expired due to inactivity. Please login again.');
}

function performLogout(message) {
    // Get token
    const token = localStorage.getItem('authToken') || sessionStorage.getItem('authToken');
    
    // Call logout endpoint
    if (token) {
        fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            headers: getAuthHeaders()
        }).catch(error => console.error('Logout error:', error));
    }
    
    // Clear authentication
    clearAuthentication();
    
    // Show message if provided
    if (message) {
        localStorage.setItem('logoutMessage', message);
    }
    
    // Redirect to login
    window.location.href = 'login.html';
}

// Search products
document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('product-search');
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterProducts, 300));
    }
});

function filterProducts(e) {
    const searchTerm = e.target.value.toLowerCase();
    const cards = document.querySelectorAll('.product-card');
    
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        card.style.display = text.includes(searchTerm) ? 'block' : 'none';
    });
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}
