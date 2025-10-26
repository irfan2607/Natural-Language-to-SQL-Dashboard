import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta
import random

class DataLoader:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
    
    def load_sample_data(self):
        """Load sample business data for demonstration"""
        self._load_customers()
        self._load_products()
        self._load_orders()
        self._load_sales()
    
    def _load_customers(self):
        customers = [
            (1, 'John Smith', 'john@email.com', 'New York', '2023-01-15'),
            (2, 'Jane Doe', 'jane@email.com', 'Los Angeles', '2023-02-20'),
            (3, 'Mike Johnson', 'mike@email.com', 'Chicago', '2023-03-10'),
            (4, 'Sarah Wilson', 'sarah@email.com', 'Miami', '2023-01-25'),
            (5, 'David Brown', 'david@email.com', 'Seattle', '2023-04-05'),
            (6, 'Emily Davis', 'emily@email.com', 'Boston', '2023-02-28'),
            (7, 'Chris Lee', 'chris@email.com', 'Austin', '2023-03-15'),
            (8, 'Amanda Garcia', 'amanda@email.com', 'Denver', '2023-01-10'),
            (9, 'Kevin Miller', 'kevin@email.com', 'Atlanta', '2023-04-20'),
            (10, 'Lisa Martinez', 'lisa@email.com', 'Phoenix', '2023-03-05')
        ]
        
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT OR REPLACE INTO customers (id, name, email, city, signup_date)
            VALUES (?, ?, ?, ?, ?)
        ''', customers)
        self.conn.commit()
    
    def _load_products(self):
        products = [
            (1, 'Laptop', 'Electronics', 999.99, 50),
            (2, 'Smartphone', 'Electronics', 699.99, 100),
            (3, 'Desk Chair', 'Furniture', 199.99, 30),
            (4, 'Coffee Maker', 'Home Appliances', 89.99, 75),
            (5, 'Running Shoes', 'Sports', 129.99, 60),
            (6, 'Backpack', 'Accessories', 59.99, 80),
            (7, 'Headphones', 'Electronics', 149.99, 45),
            (8, 'Water Bottle', 'Accessories', 24.99, 120),
            (9, 'Fitness Tracker', 'Electronics', 79.99, 90),
            (10, 'Office Desk', 'Furniture', 299.99, 20)
        ]
        
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT OR REPLACE INTO products (id, name, category, price, stock)
            VALUES (?, ?, ?, ?, ?)
        ''', products)
        self.conn.commit()
    
    def _load_orders(self):
        orders = []
        order_id = 1
        for customer_id in range(1, 11):
            for _ in range(random.randint(3, 8)):
                product_id = random.randint(1, 10)
                quantity = random.randint(1, 3)
                order_date = f"2023-{random.randint(1, 6):02d}-{random.randint(1, 28):02d}"
                total = quantity * [999.99, 699.99, 199.99, 89.99, 129.99, 59.99, 149.99, 24.99, 79.99, 299.99][product_id-1]
                
                orders.append((
                    order_id, customer_id, product_id, quantity, order_date, total
                ))
                order_id += 1
        
        cursor = self.conn.cursor()
        cursor.executemany('''
            INSERT OR REPLACE INTO orders (id, customer_id, product_id, quantity, order_date, total)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', orders)
        self.conn.commit()
    
    def _load_sales(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id, total, order_date FROM orders')
        orders = cursor.fetchall()
        
        sales = []
        for order_id, total, order_date in orders:
            profit_margin = random.uniform(0.15, 0.35)
            sales.append((
                order_id, order_id, total, profit_margin, order_date
            ))
        
        cursor.executemany('''
            INSERT OR REPLACE INTO sales (id, order_id, revenue, profit_margin, sales_date)
            VALUES (?, ?, ?, ?, ?)
        ''', sales)
        self.conn.commit()
    
    def close(self):
        self.conn.close()

if __name__ == '__main__':
    loader = DataLoader('database/business.db')
    loader.load_sample_data()
    loader.close()
    print("Sample data loaded successfully!")