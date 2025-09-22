function addToCart(id, name, price, restaurantId) {
    fetch("/api/cart", {
        method: "post",
        body: JSON.stringify({
            "id": id,
            "name": name,
            "price": price,
            "restaurant_id": restaurantId
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        console.info(data)
        let d = document.getElementsByClassName('cart-counter')
        for (let i = 0; i < d.length; i++)
            d[i].innerText = data.total_quantity
    }) // promise
}

function updateCart(productId, obj) {
   fetch(`/api/cart/${productId}`, {
        method: "put",
        body: JSON.stringify({
            "quantity": obj.value
        }),
        headers: {
            'Content-Type': 'application/json'
        }
    }).then(res => res.json()).then(data => {
        let d = document.getElementsByClassName('cart-counter')
        for (let i = 0; i < d.length; i++)
            d[i].innerText = data.total_quantity

        let d2 = document.getElementsByClassName('cart-amount')
        for (let i = 0; i < d2.length; i++)
            d2[i].innerText = data.total_amount.toLocaleString("en-US")
    }).catch(err => console.info(err)) // promise
}

function deleteCart(productId) {
    if (confirm("Bạn chắc chắn xóa không?") == true) {
        fetch(`/api/cart/${productId}`, {
            method: "delete"
        }).then(res => res.json()).then(data => {
            let d = document.getElementsByClassName('cart-counter')
            for (let i = 0; i < d.length; i++)
                d[i].innerText = data.total_quantity

            let d2 = document.getElementsByClassName('cart-amount')
            for (let i = 0; i < d2.length; i++)
                d2[i].innerText = data.total_amount.toLocaleString("en-US")

            let c = document.getElementById(`cart${productId}`)
            c.style.display = "none"
        }).catch(err => console.info(err)) // promise
    }
}

function pay() {
    // Lấy phương thức thanh toán được chọn
    const paymentMethod = document.querySelector('input[name="payment_method"]:checked');
    
    if (!paymentMethod) {
        alert('Vui lòng chọn phương thức thanh toán!');
        return;
    }
    
    if (confirm("Bạn chắc chắn thanh toán không?") == true) {
        const requestData = {
            "payment_method": paymentMethod.value
        };
        
        fetch("/api/pay", {
            method: "post",
            body: JSON.stringify(requestData),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(res => {
            if (!res.ok) {
                throw new Error(`HTTP error! status: ${res.status}`);
            }
            return res.json();
        }).then(data => {
            if (data.status === 200) {
                // Hiển thị banner hủy trong 60 giây
                showCancelBanner(data.pending_id);
            } else {
                alert("Hệ thống đang bị lỗi!")
            }
        }).catch(err => {
            console.error('Payment error:', err);
            alert("Có lỗi xảy ra khi thanh toán: " + err.message);
        })
    }
}

// UI banner hủy đơn trong 60s
function showCancelBanner(pendingId) {
    // Tạo banner nếu chưa có
    let banner = document.getElementById('cancel-banner');
    if (!banner) {
        banner = document.createElement('div');
        banner.id = 'cancel-banner';
        banner.style.position = 'fixed';
        banner.style.bottom = '20px';
        banner.style.right = '20px';
        banner.style.background = '#fff';
        banner.style.border = '1px solid #ddd';
        banner.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
        banner.style.padding = '16px';
        banner.style.borderRadius = '8px';
        banner.style.zIndex = '9999';
        banner.style.maxWidth = '320px';
        banner.innerHTML = `
            <div style="margin-bottom: 8px; font-weight: 600;">Đơn hàng đang chờ tiếp nhận</div>
            <div style="margin-bottom: 8px;">Bạn có <span id="cancel-countdown">60</span>s để hủy nếu bấm nhầm.</div>
            <div style="display:flex; gap:8px;">
                <button id="keep-order-btn" class="btn btn-danger btn-sm">Giữ đơn</button>
                <button id="cancel-order-btn" class="btn btn-light btn-sm">Hủy đơn</button>
            </div>
        `;
        document.body.appendChild(banner);
    }

    // Countdown
    let seconds = 60;
    const countdownEl = document.getElementById('cancel-countdown');
    const intervalId = setInterval(() => {
        seconds -= 1;
        if (countdownEl) countdownEl.textContent = String(seconds);
        if (seconds <= 0) {
            clearInterval(intervalId);
            // Hết hạn: ẩn banner và reload để làm sạch giỏ
            banner.remove();
            alert('Đơn đã được tiếp nhận.');
            location.reload();
        }
    }, 1000);

    // Nút hủy
    const cancelBtn = document.getElementById('cancel-order-btn');
    cancelBtn.onclick = function() {
        fetch(`/api/pending/${pendingId}/cancel`, { method: 'post' })
            .then(res => res.json())
            .then(data => {
                if (data.status === 200) {
                    clearInterval(intervalId);
                    banner.remove();
                    alert('Đã hủy đơn hàng.');
                    location.reload();
                } else {
                    alert(data.message || 'Không thể hủy đơn.');
                }
            })
            .catch(err => alert('Lỗi khi hủy đơn: ' + err.message));
    };

    // Nút giữ đơn
    const keepBtn = document.getElementById('keep-order-btn');
    keepBtn.onclick = function() {
        clearInterval(intervalId);
        banner.remove();
        alert('Đơn sẽ được tiếp nhận trong giây lát.');
        location.reload();
    };
}
