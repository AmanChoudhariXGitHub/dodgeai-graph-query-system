"""
Data ingestion script - Loads sample dataset into PostgreSQL
Run this after database is initialized to populate with sample data
"""
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from db import SessionLocal, init_db
from models import Customer, Product, Order, OrderItem, Delivery, Invoice, Payment
import random

def ingest_sample_data():
    """Load sample ERP data into the database"""
    db = SessionLocal()
    
    try:
        # Clear existing data (optional, for dev)
        # for model in [Payment, Invoice, Delivery, OrderItem, Order, Product, Customer]:
        #     db.query(model).delete()
        # db.commit()
        
        # Create sample customers
        customers = []
        customer_names = [
            "Acme Corp", "TechFlow Inc", "Global Logistics",
            "Innovation Labs", "Digital Solutions", "Enterprise Systems"
        ]
        for name in customer_names:
            customer = Customer(
                name=name,
                email=f"{name.lower().replace(' ', '_')}@example.com"
            )
            db.add(customer)
            customers.append(customer)
        
        db.commit()
        
        # Create sample products
        products = []
        product_data = [
            ("Laptop", 1299.99),
            ("Monitor", 399.99),
            ("Keyboard", 89.99),
            ("Mouse", 29.99),
            ("USB-C Cable", 19.99),
            ("Wireless Headphones", 149.99),
        ]
        for name, price in product_data:
            product = Product(name=name, price=price)
            db.add(product)
            products.append(product)
        
        db.commit()
        
        # Create sample orders with full flow
        base_date = datetime.utcnow() - timedelta(days=30)
        
        for i in range(10):
            customer = random.choice(customers)
            order_date = base_date + timedelta(days=i*3)
            
            # Create order
            order = Order(
                customer_id=customer.id,
                order_date=order_date,
                total=random.uniform(500, 5000),
                status="completed"
            )
            db.add(order)
            db.flush()
            
            # Add order items
            num_items = random.randint(1, 3)
            for _ in range(num_items):
                product = random.choice(products)
                quantity = random.randint(1, 5)
                order_item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantity=quantity
                )
                db.add(order_item)
            
            # Create delivery
            delivery = Delivery(
                order_id=order.id,
                delivery_date=order_date + timedelta(days=random.randint(2, 7)),
                status="delivered"
            )
            db.add(delivery)
            db.flush()
            
            # Create invoice
            invoice = Invoice(
                delivery_id=delivery.id,
                amount=order.total,
                issue_date=delivery.delivery_date + timedelta(days=1)
            )
            db.add(invoice)
            db.flush()
            
            # Create payment
            payment = Payment(
                invoice_id=invoice.id,
                amount=order.total,
                payment_date=invoice.issue_date + timedelta(days=random.randint(1, 10)),
                status="completed"
            )
            db.add(payment)
        
        db.commit()
        print("✅ Sample data ingested successfully!")
        print(f"   - {len(customers)} customers")
        print(f"   - {len(products)} products")
        print(f"   - {len(db.query(Order).all())} orders with full flow (delivery → invoice → payment)")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error ingesting data: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Initializing database...")
    init_db()
    print("Loading sample data...")
    ingest_sample_data()
