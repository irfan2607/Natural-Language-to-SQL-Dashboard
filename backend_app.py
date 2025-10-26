from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_redis import FlaskRedis
import sqlite3
import google.generativeai as genai
import pandas as pd
import os
from datetime import datetime, timedelta
import json
import logging
from prometheus_client import Counter, Histogram, generate_latest
import time

app = Flask(__name__)
CORS(app)
app.config['REDIS_URL'] = 'redis://localhost:6379/0'
redis_client = FlaskRedis(app)

# GCP Configuration
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Prometheus metrics
SQL_QUERIES_COUNT = Counter('sql_queries_total', 'Total SQL queries executed')
QUERY_DURATION = Histogram('query_duration_seconds', 'Query execution time')

class DatabaseManager:
    def __init__(self, db_path='database/business.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT,
                email TEXT,
                city TEXT,
                signup_date DATE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT,
                category TEXT,
                price DECIMAL(10,2),
                stock INTEGER
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER,
                product_id INTEGER,
                quantity INTEGER,
                order_date DATE,
                total DECIMAL(10,2),
                FOREIGN KEY (customer_id) REFERENCES customers (id),
                FOREIGN KEY (product_id) REFERENCES products (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY,
                order_id INTEGER,
                revenue DECIMAL(10,2),
                profit_margin DECIMAL(5,2),
                sales_date DATE,
                FOREIGN KEY (order_id) REFERENCES orders (id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    @QUERY_DURATION.time()
    def execute_query(self, query):
        SQL_QUERIES_COUNT.inc()
        conn = sqlite3.connect(self.db_path)
        try:
            df = pd.read_sql_query(query, conn)
            return df.to_dict('records')
        except Exception as e:
            raise Exception(f"SQL Error: {str(e)}")
        finally:
            conn.close()

class LLMQueryGenerator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro')
        self.system_prompt = """
        You are a SQL expert. Convert natural language questions to SQL queries for the following schema:

        customers: id, name, email, city, signup_date
        products: id, name, category, price, stock  
        orders: id, customer_id, product_id, quantity, order_date, total
        sales: id, order_id, revenue, profit_margin, sales_date

        Rules:
        - Use only SELECT queries
        - Always include LIMIT for large results
        - Use proper JOINs when needed
        - Return only SQL, no explanations
        - Use SQLite syntax
        """
    
    def generate_sql(self, natural_language_query):
        cache_key = f"sql_cache:{natural_language_query}"
        cached = redis_client.get(cache_key)
        if cached:
            return cached.decode()
        
        prompt = f"{self.system_prompt}\n\nQuestion: {natural_language_query}\nSQL:"
        
        try:
            response = self.model.generate_content(prompt)
            sql_query = response.text.strip().replace('```sql', '').replace('```', '').strip()
            
            # Cache for 1 hour
            redis_client.setex(cache_key, 3600, sql_query)
            return sql_query
        except Exception as e:
            raise Exception(f"LLM Error: {str(e)}")

class AnalyticsEngine:
    def __init__(self, db_manager):
        self.db = db_manager
    
    def get_kpis(self):
        """Calculate real-time business KPIs"""
        kpis = {}
        
        # Total Revenue
        revenue_query = "SELECT SUM(revenue) as total_revenue FROM sales"
        kpis['total_revenue'] = self.db.execute_query(revenue_query)[0]['total_revenue'] or 0
        
        # Total Orders
        orders_query = "SELECT COUNT(*) as total_orders FROM orders"
        kpis['total_orders'] = self.db.execute_query(orders_query)[0]['total_orders']
        
        # Total Customers
        customers_query = "SELECT COUNT(*) as total_customers FROM customers"
        kpis['total_customers'] = self.db.execute_query(customers_query)[0]['total_customers']
        
        # Monthly Growth
        monthly_query = """
        SELECT strftime('%Y-%m', sales_date) as month, SUM(revenue) as monthly_revenue
        FROM sales 
        GROUP BY month 
        ORDER BY month DESC 
        LIMIT 2
        """
        monthly_data = self.db.execute_query(monthly_query)
        if len(monthly_data) >= 2:
            current = monthly_data[0]['monthly_revenue']
            previous = monthly_data[1]['monthly_revenue']
            kpis['revenue_growth'] = ((current - previous) / previous * 100) if previous else 0
        else:
            kpis['revenue_growth'] = 0
            
        return kpis

# Initialize services
db_manager = DatabaseManager()
llm_generator = LLMQueryGenerator()
analytics_engine = AnalyticsEngine(db_manager)

@app.route('/api/query', methods=['POST'])
def handle_nl_query():
    try:
        data = request.get_json()
        natural_query = data.get('query')
        
        if not natural_query:
            return jsonify({'error': 'No query provided'}), 400
        
        # Generate SQL from natural language
        sql_query = llm_generator.generate_sql(natural_query)
        
        # Execute query
        results = db_manager.execute_query(sql_query)
        
        return jsonify({
            'sql_query': sql_query,
            'results': results,
            'count': len(results)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    try:
        kpis = analytics_engine.get_kpis()
        return jsonify(kpis)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chart/<chart_type>', methods=['GET'])
def get_chart_data(chart_type):
    try:
        chart_queries = {
            'sales_trend': """
                SELECT strftime('%Y-%m', sales_date) as month, 
                       SUM(revenue) as revenue
                FROM sales 
                GROUP BY month 
                ORDER BY month
            """,
            'product_performance': """
                SELECT p.category, SUM(s.revenue) as revenue
                FROM sales s
                JOIN orders o ON s.order_id = o.id
                JOIN products p ON o.product_id = p.id
                GROUP BY p.category
                ORDER BY revenue DESC
            """,
            'customer_analytics': """
                SELECT c.city, COUNT(o.id) as order_count, 
                       SUM(s.revenue) as total_revenue
                FROM customers c
                JOIN orders o ON c.id = o.customer_id
                JOIN sales s ON o.id = s.order_id
                GROUP BY c.city
                ORDER BY total_revenue DESC
                LIMIT 10
            """
        }
        
        if chart_type not in chart_queries:
            return jsonify({'error': 'Invalid chart type'}), 400
            
        data = db_manager.execute_query(chart_queries[chart_type])
        return jsonify(data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/metrics')
def metrics():
    return generate_latest()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)