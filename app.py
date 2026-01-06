from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
from datetime import datetime, timedelta
import os

app = Flask(__name__, static_folder='static')
CORS(app)

DATABASE = 'finance.db'

# Initialize database
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Money sources table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS money_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            balance REAL DEFAULT 0,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Expenses table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            source_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (source_id) REFERENCES money_sources (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Get database connection
def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Create or get user
def get_or_create_user(telegram_id, username=None):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('INSERT INTO users (telegram_id, username) VALUES (?, ?)',
                      (telegram_id, username))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['id']
    
    conn.close()
    return user_id

# Routes
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/init', methods=['POST'])
def init_user():
    data = request.json
    telegram_id = data.get('telegram_id')
    username = data.get('username')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    user_id = get_or_create_user(telegram_id, username)
    return jsonify({'user_id': user_id, 'message': 'User initialized'})

# Money Sources endpoints
@app.route('/api/sources', methods=['GET'])
def get_sources():
    telegram_id = request.args.get('telegram_id')
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    cursor.execute('''
        SELECT * FROM money_sources 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    
    sources = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(sources)

@app.route('/api/sources', methods=['POST'])
def add_source():
    data = request.json
    telegram_id = data.get('telegram_id')
    name = data.get('name')
    balance = data.get('balance', 0)
    source_type = data.get('type', 'other')
    
    if not telegram_id or not name:
        return jsonify({'error': 'telegram_id and name are required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    cursor.execute('''
        INSERT INTO money_sources (user_id, name, balance, type)
        VALUES (?, ?, ?, ?)
    ''', (user_id, name, balance, source_type))
    
    conn.commit()
    source_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'id': source_id,
        'message': 'Source added successfully'
    }), 201

@app.route('/api/sources/<int:source_id>', methods=['PUT'])
def update_source(source_id):
    data = request.json
    telegram_id = data.get('telegram_id')
    balance = data.get('balance')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    cursor.execute('''
        UPDATE money_sources 
        SET balance = ? 
        WHERE id = ? AND user_id = ?
    ''', (balance, source_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Source updated successfully'})

@app.route('/api/sources/<int:source_id>', methods=['DELETE'])
def delete_source(source_id):
    telegram_id = request.args.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    cursor.execute('''
        DELETE FROM money_sources 
        WHERE id = ? AND user_id = ?
    ''', (source_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Source deleted successfully'})

# Expenses endpoints
@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    telegram_id = request.args.get('telegram_id')
    limit = request.args.get('limit', 50)
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    cursor.execute('''
        SELECT e.*, ms.name as source_name, ms.type as source_type
        FROM expenses e
        JOIN money_sources ms ON e.source_id = ms.id
        WHERE e.user_id = ?
        ORDER BY e.created_at DESC
        LIMIT ?
    ''', (user_id, limit))
    
    expenses = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify(expenses)

@app.route('/api/expenses', methods=['POST'])
def add_expense():
    data = request.json
    telegram_id = data.get('telegram_id')
    source_id = data.get('source_id')
    amount = data.get('amount')
    category = data.get('category')
    note = data.get('note', '')
    
    if not all([telegram_id, source_id, amount, category]):
        return jsonify({'error': 'Missing required fields'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    # Check if source exists and has enough balance
    cursor.execute('SELECT balance FROM money_sources WHERE id = ? AND user_id = ?',
                  (source_id, user_id))
    source = cursor.fetchone()
    
    if not source:
        conn.close()
        return jsonify({'error': 'Source not found'}), 404
    
    if source['balance'] < amount:
        conn.close()
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # Add expense
    cursor.execute('''
        INSERT INTO expenses (user_id, source_id, amount, category, note)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, source_id, amount, category, note))
    
    # Update source balance
    cursor.execute('''
        UPDATE money_sources 
        SET balance = balance - ? 
        WHERE id = ?
    ''', (amount, source_id))
    
    conn.commit()
    expense_id = cursor.lastrowid
    conn.close()
    
    return jsonify({
        'id': expense_id,
        'message': 'Expense added successfully'
    }), 201

@app.route('/api/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    telegram_id = request.args.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    # Get expense details before deleting
    cursor.execute('''
        SELECT amount, source_id FROM expenses 
        WHERE id = ? AND user_id = ?
    ''', (expense_id, user_id))
    
    expense = cursor.fetchone()
    
    if not expense:
        conn.close()
        return jsonify({'error': 'Expense not found'}), 404
    
    # Restore balance to source
    cursor.execute('''
        UPDATE money_sources 
        SET balance = balance + ? 
        WHERE id = ?
    ''', (expense['amount'], expense['source_id']))
    
    # Delete expense
    cursor.execute('DELETE FROM expenses WHERE id = ? AND user_id = ?',
                  (expense_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Expense deleted and balance restored'})

# Statistics endpoints
@app.route('/api/statistics/monthly', methods=['GET'])
def get_monthly_statistics():
    telegram_id = request.args.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    # Get current month's expenses by category
    cursor.execute('''
        SELECT category, SUM(amount) as total
        FROM expenses
        WHERE user_id = ? 
        AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        GROUP BY category
        ORDER BY total DESC
    ''', (user_id,))
    
    categories = [dict(row) for row in cursor.fetchall()]
    
    # Get total for current month
    cursor.execute('''
        SELECT SUM(amount) as total
        FROM expenses
        WHERE user_id = ? 
        AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
    ''', (user_id,))
    
    total = cursor.fetchone()['total'] or 0
    
    conn.close()
    
    return jsonify({
        'categories': categories,
        'total': total
    })

@app.route('/api/statistics/weekly', methods=['GET'])
def get_weekly_statistics():
    telegram_id = request.args.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    # Get last 7 days expenses
    cursor.execute('''
        SELECT DATE(created_at) as date, SUM(amount) as total
        FROM expenses
        WHERE user_id = ? 
        AND created_at >= date('now', '-7 days')
        GROUP BY DATE(created_at)
        ORDER BY date ASC
    ''', (user_id,))
    
    daily = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'daily': daily})

@app.route('/api/statistics/sources', methods=['GET'])
def get_source_statistics():
    telegram_id = request.args.get('telegram_id')
    
    if not telegram_id:
        return jsonify({'error': 'telegram_id is required'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    user_id = get_or_create_user(telegram_id)
    
    # Get spending by source
    cursor.execute('''
        SELECT ms.name, ms.balance, SUM(e.amount) as spent
        FROM money_sources ms
        LEFT JOIN expenses e ON ms.id = e.source_id
        WHERE ms.user_id = ?
        GROUP BY ms.id
        ORDER BY spent DESC
    ''', (user_id,))
    
    sources = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'sources': sources})

# Initialize database on startup
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)