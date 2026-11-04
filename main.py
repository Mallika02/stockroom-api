from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import SessionLocal, Product, Order, OrderItem


def get_db():  # Helper function, creates a database session for the request
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()    # request gets closed afterwards


class ProductCreate(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    quantity: int = Field(ge=0)


app = FastAPI(title="Stockroom API")


@app.get("/")
def home():
    return {"message": "Stockroom API is running!"}

# 4 core product operations: create, read, update, delete


@app.post("/products", status_code=201)
def create_product(     # to create a product, the new product gets saved to the database
        product: ProductCreate,
        db: Session = Depends(get_db)  # FastAPI provides a database session for this request
):
    db_product = Product(
        name=product.name,
        price=product.price,
        quantity=product.quantity
    )

    db.add(db_product)
    db.commit()  # commits the database transaction, saving the changes
    db.refresh(db_product)  # refreshes the object with the latest values from the database

    return {
        "id": db_product.id,
        "name": db_product.name,
        "price": db_product.price,
        "quantity": db_product.quantity
    }


@app.get("/products")  # retrieves all products from the database, and returns them as SQLAlchemy model objects,
def list_products(db: Session = Depends(get_db)):  # after which FastAPI serializes the results as JSON
    return db.query(Product).all()


@app.get("/products/{product_id}")  # searches the database for the requested ID
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    '''
    The above line, product = db.query....first() finds the first product whose
    ID matches the requested ID, if not applicable it returns None.
    Thus, the product's database ID gets compared with the requested ID, 
    via Product.id == product_id
    '''

    if product is None:   # if the product doesn't exist returns HTTP 404
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@app.put("/products/{product_id}")
def update_product(     # to update an existing product, without creating duplicates
   product_id: int,
   updated_product: ProductCreate,
   db: Session = Depends(get_db)
):
    product = db.query(Product).filter(Product.id == product_id).first()

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    # the above line stops normal processing and returns an HTTP 404 error

    product.name = updated_product.name
    product.price = updated_product.price
    product.quantity = updated_product.quantity

    db.commit()
    db.refresh(product)

    return product


@app.delete("/products/{product_id}")   # to permanently delete a product (that specific database row)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    try:
        product = db.query(Product).filter(
            Product.id == product_id
        ).first()

        if product is None:
            raise HTTPException(
                status_code=404,
                detail="Product not found"
            )

        # Prevent deletion if the product appears in an order.
        existing_order_item = db.query(OrderItem).filter(
            OrderItem.product_id == product_id
        ).first()

        if existing_order_item is not None:
            raise HTTPException(
                status_code=409,
                detail="Cannot delete a product associated with an order"
            )

        db.delete(product)
        db.commit()

        return {"message": "Product deleted successfully"}

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: str = Field(pattern="^(completed|cancelled)$")


class OrderItemResponse(BaseModel):
    product_id: int
    quantity: int

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    id: int
    status: str
    items: list[OrderItemResponse]

    model_config = ConfigDict(from_attributes=True)


@app.post("/orders", status_code=201)
def create_order(
    order: OrderCreate,
    db: Session = Depends(get_db)
):
    try:
        products = {}
        requested_quantities = {}

        # Check that every product exists.
        for item in order.items:
            product = db.query(Product).filter(
                Product.id == item.product_id
            ).first()

            if product is None:
                raise HTTPException(
                    status_code=404,
                    detail=f"Product {item.product_id} not found"
                )

            products[item.product_id] = product

            # Add quantities if the same product appears more than once.
            requested_quantities[item.product_id] = (
                requested_quantities.get(item.product_id, 0)
                + item.quantity
            )

        # Check total requested quantities against available stock.
        for product_id, requested in requested_quantities.items():
            if products[product_id].quantity < requested:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for product {product_id}"
                )

        # Create the order and obtain its ID.
        new_order = Order(status="pending")
        db.add(new_order)
        db.flush()

        # Reduce inventory and record each order item.
        for product_id, requested in requested_quantities.items():
            products[product_id].quantity -= requested

        for item in order.items:
            db.add(
                OrderItem(
                    order_id=new_order.id,
                    product_id=item.product_id,
                    quantity=item.quantity
                )
            )

        # Save the order, its items, and stock changes together.
        db.commit()
        db.refresh(new_order)

        return {
            "id": new_order.id,
            "status": new_order.status,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity
                }
                for item in order.items
            ]
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise


@app.get("/orders", response_model=list[OrderResponse])
def list_orders(db: Session = Depends(get_db)):
    return db.query(Order).all()


@app.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@app.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    updated_status: OrderStatusUpdate,
    db: Session = Depends(get_db)
):
    try:
        order = db.scalars(
            select(Order).where(Order.id == order_id)
        ).first()

        if order is None:
            raise HTTPException(
                status_code=404,
                detail="Order not found"
            )

        if order.status != "pending":
            raise HTTPException(
                status_code=400,
                detail="Only pending orders can be updated"
            )

        if updated_status.status == "cancelled":
            for item in order.items:
                product = db.scalars(
                    select(Product).where(Product.id == item.product_id)
                ).first()

                if product is None:
                    raise HTTPException(
                        status_code=409,
                        detail=f"Product {item.product_id} no longer exists"
                    )

                product.quantity += item.quantity

        order.status = updated_status.status

        db.commit()
        db.refresh(order)

        return {
            "id": order.id,
            "status": order.status
        }

    except HTTPException:
        db.rollback()
        raise

    except Exception:
        db.rollback()
        raise
