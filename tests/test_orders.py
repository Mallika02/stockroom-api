def test_create_order_deducts_inventory(client):
    create_response = client.post(
        "/products",
        json={
            "name": "Office Laptop",
            "price": 1200,
            "quantity": 10
        }
    )

    product_id = create_response.json()["id"]

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 3
                }
            ]
        }
    )

    assert response.status_code == 201
    assert response.json()["status"] == "pending"

    product_response = client.get(f"/products/{product_id}")

    assert product_response.status_code == 200
    assert product_response.json()["quantity"] == 7


def test_create_order_with_insufficient_stock(client):
    create_response = client.post(
        "/products",
        json={
            "name": "Office Laptop",
            "price": 1200,
            "quantity": 5
        }
    )

    product_id = create_response.json()["id"]

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 8
                }
            ]
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        f"Insufficient stock for product {product_id}"
    )

    product_response = client.get(f"/products/{product_id}")

    assert product_response.json()["quantity"] == 5


def test_create_order_with_nonexistent_product(client):
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": 9999,
                    "quantity": 1
                }
            ]
        }
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product 9999 not found"


def test_create_order_with_zero_quantity(client):
    product_response = client.post(
        "/products",
        json={
            "name": "Test Laptop",
            "price": 1000,
            "quantity": 10
        }
    )

    product_id = product_response.json()["id"]

    product_before = client.get(f"/products/{product_id}").json()
#   print("BEFORE:", product_before)
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 0
                }
            ]
        }
    )

    assert response.status_code == 422

    product_after = client.get(f"/products/{product_id}").json()
#   print("AFTER:", product_after)
    assert product_after["quantity"] == product_before["quantity"]


def test_create_order_with_negative_quantity(client):
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": 2,
                    "quantity": -3
                }
            ]
        }
    )

    assert response.status_code == 422


def test_create_order_with_empty_items(client):
    response = client.post(
        "/orders",
        json={
            "items": []
        }
    )

    assert response.status_code == 422


def test_create_order_with_multiple_items_insufficient_stock(client):
    laptop_response = client.post(
        "/products",
        json={
            "name": "Test Laptop",
            "price": 1000,
            "quantity": 10
        }
    )

    laptop_id = laptop_response.json()["id"]

    mouse_response = client.post(
        "/products",
        json={
            "name": "Test Mouse",
            "price": 20,
            "quantity": 1
        }
    )

    mouse_id = mouse_response.json()["id"]

    # Submit an order requesting more mice than available
    response = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": laptop_id, "quantity": 2},
                {"product_id": mouse_id, "quantity": 2}
            ]
        }
    )

    assert response.status_code == 400

    laptop_after = client.get(f"/products/{laptop_id}").json()
    mouse_after = client.get(f"/products/{mouse_id}").json()

    assert laptop_after["quantity"] == 10
    assert mouse_after["quantity"] == 1


def test_create_order_with_duplicate_products(client):
    product_response = client.post(
        "/products",
        json={
            "name": "Test Keyboard",
            "price": 50,
            "quantity": 10
        }
    )

    product_id = product_response.json()["id"]

    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                },
                {
                    "product_id": product_id,
                    "quantity": 3
                }
            ]
        }
    )

    assert response.status_code == 201

    product_after = client.get(f"/products/{product_id}").json()

    assert product_after["quantity"] == 5


def test_create_order_with_multiple_different_products(client):
    # Create Laptop
    laptop_response = client.post(
        "/products",
        json={"name": "Laptop", "price": 1000, "quantity": 10}
    )
    laptop_id = laptop_response.json()["id"]

    # Create Mouse
    mouse_response = client.post(
        "/products",
        json={"name": "Mouse", "price": 25, "quantity": 5}
    )
    mouse_id = mouse_response.json()["id"]

    # Submit an order containing both products
    response = client.post(
        "/orders",
        json={
            "items": [
                {"product_id": laptop_id, "quantity": 2},
                {"product_id": mouse_id, "quantity": 3}
            ]
        }
    )

    assert response.status_code == 201

    laptop_after = client.get(f"/products/{laptop_id}").json()
    mouse_after = client.get(f"/products/{mouse_id}").json()

    assert laptop_after["quantity"] == 8
    assert mouse_after["quantity"] == 2


def _create_test_product(client, quantity=10):
    response = client.post(
        "/products",
        json={
            "name": "Test Product",
            "price": 100,
            "quantity": quantity
        }
    )
    return response.json()["id"]


def _create_test_order(client, product_id, quantity=3):
    response = client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": quantity
                }
            ]
        }
    )
    return response.json()["id"]


def test_cancel_order_restores_inventory(client):
    product_id = _create_test_product(client)
    order_id = _create_test_order(client, product_id)

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "cancelled"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    product = client.get(f"/products/{product_id}")

    assert product.json()["quantity"] == 10


def test_complete_order_does_not_restore_inventory(client):
    product_id = _create_test_product(client)
    order_id = _create_test_order(client, product_id)

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "completed"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"

    product = client.get(f"/products/{product_id}")

    assert product.json()["quantity"] == 7


def test_non_pending_order_cannot_be_updated(client):
    product_id = _create_test_product(client)
    cancelled_order_id = _create_test_order(client, product_id)
    completed_order_id = _create_test_order(client, product_id)

    client.patch(
        f"/orders/{cancelled_order_id}/status",
        json={"status": "cancelled"}
    )

    client.patch(
        f"/orders/{completed_order_id}/status",
        json={"status": "completed"}
    )

    # Neither an already-cancelled nor completed order can be updated.
    cancelled_response = client.patch(
        f"/orders/{cancelled_order_id}/status",
        json={"status": "completed"}
    )

    completed_response = client.patch(
        f"/orders/{completed_order_id}/status",
        json={"status": "cancelled"}
    )

    assert cancelled_response.status_code == 400
    assert completed_response.status_code == 400


def test_invalid_order_status(client):
    product_id = _create_test_product(client)
    order_id = _create_test_order(client, product_id)

    response = client.patch(
        f"/orders/{order_id}/status",
        json={"status": "shipped"}
    )

    assert response.status_code == 422


def test_update_nonexistent_order(client):
    response = client.patch(
        "/orders/99999/status",
        json={"status": "cancelled"}
    )

    assert response.status_code == 404
