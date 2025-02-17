let cart = [];

function addToCart(itemId) {
    fetch(`/menu-item/${itemId}`)
    .then(res => res.json())
    .then(item => {
        const existing = cart.find(i => i.id === item.id);
        if(existing) {
            existing.quantity++;
        } else {
            cart.push({...item, quantity: 1});
        }
        updateCartModal();
    });
}

function updateCartModal() {
    const cartItems = document.getElementById('cartItems');
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    cartItems.innerHTML = cart.map(item => `
        <div class="cart-item">
            <span>${item.name} x${item.quantity}</span>
            <span>$${(item.price * item.quantity).toFixed(2)}</span>
            <button onclick="removeItem(${item.id})">×</button>
        </div>
    `).join('');
    
    document.getElementById('cartTotal').textContent = total.toFixed(2);
    document.getElementById('cartModal').style.display = 'block';
}

function removeItem(itemId) {
    cart = cart.filter(item => item.id !== itemId);
    updateCartModal();
}

function showConfirmation() {
    const tableNumber = document.getElementById('tableNumber').value;
    if(!tableNumber) {
        alert('Please enter a table number');
        return;
    }
    
    document.getElementById('orderSummary').innerHTML = `
        <p>Table: ${tableNumber}</p>
        ${cart.map(item => `
            <p>${item.name} x${item.quantity} - $${(item.price * item.quantity).toFixed(2)}</p>
        `).join('')}
        <hr>
        <p>Total: $${cart.reduce((sum, item) => sum + (item.price * item.quantity), 0).toFixed(2)}</p>
    `;
    
    document.getElementById('confirmModal').style.display = 'block';
}

function placeOrder() {
    const tableNumber = document.getElementById('tableNumber').value;
    const total = cart.reduce((sum, item) => sum + (item.price * item.quantity), 0);
    
    fetch('/place_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            tableNumber: parseInt(tableNumber),
            total: total,
            cart: cart
        })
    })
    .then(response => response.json())
    .then(data => {
        if(data.success) {
            alert('Order placed successfully!');
            closeModals();
            cart = [];
        } else {
            alert('Error placing order');
        }
    });
}

function closeModals() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.style.display = 'none';
    });
}

// Close modals when clicking outside
window.onclick = function(event) {
    if(event.target.classList.contains('modal')) {
        closeModals();
    }
}

// Admin Dashboard Functions
function updateOrderStatus(orderId) {
    const status = document.querySelector(`select[data-order-id="${orderId}"]`).value;
    fetch('/update-status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            order_id: orderId,
            status: status
        })
    });
}

function editItem(itemId) {
    // Implement edit functionality
    fetch(`/menu-item/${itemId}`)
    .then(res => res.json())
    .then(item => {
        // Populate edit form
    });
}

function deleteItem(itemId) {
    if(confirm('Are you sure you want to delete this item?')) {
        fetch(`/delete-item/${itemId}`, { method: 'POST' })
        .then(() => location.reload());
    }
}