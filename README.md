Stockroom API


A RESTful inventory and order management API built with Python, FastAPI, SQLAlchemy, and SQLite.


Stockroom API provides endpoints for managing products, tracking inventory, and processing customer orders. It includes input validation, transactional database operations, and automated tests. 


Features:

- Product Management: Create, retrieve, update, and delete products.
- Order Management: Create orders containing one or more products, and retrieve existing orders. 
- Inventory Tracking: Automatically deduct available stock when an order is placed.
- Order Status Management: Complete or cancel pending orders.
- Inventory Restoration: Restore product quantities when an order is cancelled.
- Deletion Protection: Prevent deletion of products associated with existing orders.
- Input Validation: Validate product prices, quantities and order data.
- Error Handling: Return appropriate HTTP status codes for invalid requests and unavailable resources.
- Automated Testing: Test API functionality using pytest.


Tech Stack:

- Python
- FastAPI
- SQLAlchemy
- SQLite
- Pydantic
- Pytest
- HTTPX
 

Getting Started

Prerequisites:
- Python 3.10 or later
- Git

 
Installation

1. Clone the repository:
git clone https://github.com/Mallika02/stockroom-api.git
cd stockroom-api

2. Create and activate a virtual environment:
python3 -m venv venv
source venv/bin/activate

3. Install dependencies:
pip install fastapi uvicorn sqlalchemy pytest httpx


Running the API 

Start the development server:
uvicorn main:app --reload

The API will be available at:
http://127.0.0.1:8000

Interactive API documentation (Swagger UI):
http://127.0.0.1:8000/docs


API Endpoints

Method          Endpoint                  Description

GET               /                     API welcome message
POST              /products             Create a product
GET               /products             Retrieve all products
GET        /products/{product_id}       Retrieve a product
PUT        /products/{product_id}       Update a product
DELETE     /products/{product_id}       Delete a product
POST              /orders               Create an order    
GET               /orders               Retrieve all orders
GET          /orders/{order_id}         Retrieve an order 
PATCH      /orders/{order_id}/status    Update order status


Running Tests

Run the automated test suite:
pytest -q

The test suite covers product operations, order processing, inventory updates, input validation, and error handling.


Database:

Stockroom API uses SQLite with SQLAlchemy ORM for database operations.
The SQLite database is created automatically when the application starts.


Future Improvements

- Automated CI/CD workflows using GitHub Actions.
- Deployment to a cloud hosting platform.
- Additional API features and test coverage.

  
(Developed as a backend engineering portfolio project)
