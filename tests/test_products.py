def test_get_products_returns_empty_list(client):
    response = client.get("/products")

    assert response.status_code == 200
    assert response.json() == []


def test_create_product(client):
    response = client.post(
        "/products",
        json={
            "name": "Test Laptop",
            "price": 1200,
            "quantity": 5
        }
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Test Laptop"
    assert response.json()["price"] == 1200
    assert response.json()["quantity"] == 5


def test_create_product_with_negative_price(client):
    response = client.post(
        "/products",
        json={
            "name": "Invalid Laptop",
            "price": -100,
            "quantity": 5
        }
    )

    assert response.status_code == 422


def test_get_products_returns_created_products(client):
    client.post(
        "/products",
        json={
            "name": "Gaming Mouse",
            "price": 75,
            "quantity": 10
        }
    )

    response = client.get("/products")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Gaming Mouse"


def test_get_single_product(client):
    create_response = client.post(
        "/products",
        json={
            "name": "Mechanical Keyboard",
            "price": 100,
            "quantity": 8
        }
    )

    product_id = create_response.json()["id"]

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Mechanical Keyboard"
    assert response.json()["price"] == 100
    assert response.json()["quantity"] == 8


def test_get_nonexistent_product(client):
    response = client.get("/products/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product(client):
    create_response = client.post(
        "/products",
        json={
            "name": "Old Laptop",
            "price": 1000,
            "quantity": 5
        }
    )

    product_id = create_response.json()["id"]

    response = client.put(
        f"/products/{product_id}",
        json={
            "name": "Updated Laptop",
            "price": 1500,
            "quantity": 10
        }
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Laptop"
    assert response.json()["price"] == 1500
    assert response.json()["quantity"] == 10


def test_delete_product(client):
    create_response = client.post(
        "/products",
        json={
            "name": "Temporary Laptop",
            "price": 800,
            "quantity": 4
        }
    )

    product_id = create_response.json()["id"]

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Product deleted successfully"

    get_response = client.get(f"/products/{product_id}")

    assert get_response.status_code == 404


def test_delete_nonexistent_product(client):
    response = client.delete("/products/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_product_with_negative_quantity(client):
    response = client.post(
        "/products",
        json={
            "name": "Keyboard",
            "price": 50,
            "quantity": -5
        }
    )

    assert response.status_code == 422


def test_create_product_with_empty_name(client):
    response = client.post(
        "/products",
        json={
            "name": "",
            "price": 50,
            "quantity": 10
        }
    )

    assert response.status_code == 422


def test_cannot_delete_product_associated_with_order(client):
    # Create a product.
    product_response = client.post(
        "/products",
        json={
            "name": "Test Product",
            "price": 100,
            "quantity": 10
        }
    )

    product_id = product_response.json()["id"]

    # Create an order containing that product.
    client.post(
        "/orders",
        json={
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2
                }
            ]
        }
    )

    # Attempt to delete the product.
    delete_response = client.delete(
        f"/products/{product_id}"
    )

    assert delete_response.status_code == 409

    # Confirm the product still exists.
    get_response = client.get(
        f"/products/{product_id}"
    )

    assert get_response.status_code == 200
