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
    if (confirm("Bạn chắc chắn thanh toán không?") == true) {
        fetch("/api/pay").then(res => res.json()).then(data => {
            if (data.status === 200)
                location.reload()
            else
                alert("Hệ thống đang bị lỗi!")
        })
    }
}