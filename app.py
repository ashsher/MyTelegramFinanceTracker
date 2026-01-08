from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='static')
CORS(app)

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL')

# Use PostgreSQL (Supabase) or SQLite for local development
if DATABASE_URL and DATABASE_URL.startswith('postgres'):
    # PostgreSQL connection (Supabase)
    import psycopg2
    from psycopg2.extras import RealDictCursor
    
    def get_db():
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = RealDictCursor
        return conn
    
    def init_db():
        """Initialize PostgreSQL tables"""
        conn = get_db()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id BIGSERIAL PRIMARY KEY,
                telegram_id BIGINT UNIQUE NOT NULL,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Money sources table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS money_sources (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                name TEXT NOT NULL,
                balance NUMERIC(12,2) DEFAULT 0,
                type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Expenses table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id BIGSERIAL PRIMARY KEY,
                user_id BIGINT NOT NULL,
                source_id BIGINT NOT NULL,
                amount NUMERIC(12,2) NOT NULL,
                category TEXT NOT NULL,
                note TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (source_id) REFERENCES money_sources (id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_user_id ON expenses(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_created_at ON expenses(created_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sources_user_id ON money_sources(user_id)')
        
        conn.commit()
        conn.close()
else:
    # SQLite for local development
    import sqlite3
    
    DATABASE = 'finance.db'
    
    def get_db():
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db():
        """Initialize SQLite tables"""
        conn = get_db()
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

# Helper function to convert Row/RealDictRow to dict
def row_to_dict(row):
    """Convert database row to dictionary"""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)

# Create or get user
def get_or_create_user(telegram_id, username=None):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE telegram_id = %s' if DATABASE_URL else 'SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
    user = cursor.fetchone()
    
    if not user:
        cursor.execute('INSERT INTO users (telegram_id, username) VALUES (%s, %s) RETURNING id' if DATABASE_URL else 'INSERT INTO users (telegram_id, username) VALUES (?, ?)',
                      (telegram_id, username))
        conn.commit()
        if DATABASE_URL:
            user_id = cursor.fetchone()['id']
        else:
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
    
    query = 'SELECT * FROM money_sources WHERE user_id = %s ORDER BY created_at DESC' if DATABASE_URL else 'SELECT * FROM money_sources WHERE user_id = ? ORDER BY created_at DESC'
    cursor.execute(query, (user_id,))
    
    sources = [row_to_dict(row) for row in cursor.fetchall()]
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
    
    query = 'INSERT INTO money_sources (user_id, name, balance, type) VALUES (%s, %s, %s, %s) RETURNING id' if DATABASE_URL else 'INSERT INTO money_sources (user_id, name, balance, type) VALUES (?, ?, ?, ?)'
    cursor.execute(query, (user_id, name, balance, source_type))
    
    conn.commit()
    
    if DATABASE_URL:
        source_id = cursor.fetchone()['id']
    else:
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
    
    query = 'UPDATE money_sources SET balance = %s WHERE id = %s AND user_id = %s' if DATABASE_URL else 'UPDATE money_sources SET balance = ? WHERE id = ? AND user_id = ?'
    cursor.execute(query, (balance, source_id, user_id))
    
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
    
    # Check if source has any expenses
    query = 'SELECT COUNT(*) as count FROM expenses WHERE source_id = %s AND user_id = %s' if DATABASE_URL else 'SELECT COUNT(*) as count FROM expenses WHERE source_id = ? AND user_id = ?'
    cursor.execute(query, (source_id, user_id))
    
    expense_count = cursor.fetchone()['count']
    
    if expense_count > 0:
        conn.close()
        return jsonify({'error': f'Cannot delete source with {expense_count} expenses. Delete expenses first.'}), 400
    
    query = 'DELETE FROM money_sources WHERE id = %s AND user_id = %s' if DATABASE_URL else 'DELETE FROM money_sources WHERE id = ? AND user_id = ?'
    cursor.execute(query, (source_id, user_id))
    
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
    
    query = '''
        SELECT e.*, ms.name as source_name, ms.type as source_type
        FROM expenses e
        JOIN money_sources ms ON e.source_id = ms.id
        WHERE e.user_id = %s
        ORDER BY e.created_at DESC
        LIMIT %s
    ''' if DATABASE_URL else '''
        SELECT e.*, ms.name as source_name, ms.type as source_type
        FROM expenses e
        JOIN money_sources ms ON e.source_id = ms.id
        WHERE e.user_id = ?
        ORDER BY e.created_at DESC
        LIMIT ?
    '''
    
    cursor.execute(query, (user_id, limit))
    
    expenses = [row_to_dict(row) for row in cursor.fetchall()]
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
    query = 'SELECT balance FROM money_sources WHERE id = %s AND user_id = %s' if DATABASE_URL else 'SELECT balance FROM money_sources WHERE id = ? AND user_id = ?'
    cursor.execute(query, (source_id, user_id))
    source = cursor.fetchone()
    
    if not source:
        conn.close()
        return jsonify({'error': 'Source not found'}), 404
    
    if float(source['balance']) < float(amount):
        conn.close()
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # Add expense
    query = 'INSERT INTO expenses (user_id, source_id, amount, category, note) VALUES (%s, %s, %s, %s, %s) RETURNING id' if DATABASE_URL else 'INSERT INTO expenses (user_id, source_id, amount, category, note) VALUES (?, ?, ?, ?, ?)'
    cursor.execute(query, (user_id, source_id, amount, category, note))
    
    # Update source balance
    query = 'UPDATE money_sources SET balance = balance - %s WHERE id = %s' if DATABASE_URL else 'UPDATE money_sources SET balance = balance - ? WHERE id = ?'
    cursor.execute(query, (amount, source_id))
    
    conn.commit()
    
    if DATABASE_URL:
        expense_id = cursor.fetchone()['id']
    else:
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
    query = 'SELECT amount, source_id FROM expenses WHERE id = %s AND user_id = %s' if DATABASE_URL else 'SELECT amount, source_id FROM expenses WHERE id = ? AND user_id = ?'
    cursor.execute(query, (expense_id, user_id))
    
    expense = cursor.fetchone()
    
    if not expense:
        conn.close()
        return jsonify({'error': 'Expense not found'}), 404
    
    # Restore balance to source
    query = 'UPDATE money_sources SET balance = balance + %s WHERE id = %s' if DATABASE_URL else 'UPDATE money_sources SET balance = balance + ? WHERE id = ?'
    cursor.execute(query, (expense['amount'], expense['source_id']))
    
    # Delete expense
    query = 'DELETE FROM expenses WHERE id = %s AND user_id = %s' if DATABASE_URL else 'DELETE FROM expenses WHERE id = ? AND user_id = ?'
    cursor.execute(query, (expense_id, user_id))
    
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
    if DATABASE_URL:
        query = '''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = %s 
            AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
            GROUP BY category
            ORDER BY total DESC
        '''
    else:
        query = '''
            SELECT category, SUM(amount) as total
            FROM expenses
            WHERE user_id = ? 
            AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
            GROUP BY category
            ORDER BY total DESC
        '''
    
    cursor.execute(query, (user_id,))
    categories = [row_to_dict(row) for row in cursor.fetchall()]
    
    # Get total for current month
    if DATABASE_URL:
        query = '''
            SELECT SUM(amount) as total
            FROM expenses
            WHERE user_id = %s 
            AND DATE_TRUNC('month', created_at) = DATE_TRUNC('month', CURRENT_DATE)
        '''
    else:
        query = '''
            SELECT SUM(amount) as total
            FROM expenses
            WHERE user_id = ? 
            AND strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')
        '''
    
    cursor.execute(query, (user_id,))
    total = cursor.fetchone()['total'] or 0
    
    conn.close()
    
    return jsonify({
        'categories': categories,
        'total': float(total)
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
    if DATABASE_URL:
        query = '''
            SELECT DATE(created_at) as date, SUM(amount) as total
            FROM expenses
            WHERE user_id = %s 
            AND created_at >= CURRENT_DATE - INTERVAL '7 days'
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        '''
    else:
        query = '''
            SELECT DATE(created_at) as date, SUM(amount) as total
            FROM expenses
            WHERE user_id = ? 
            AND created_at >= date('now', '-7 days')
            GROUP BY DATE(created_at)
            ORDER BY date ASC
        '''
    
    cursor.execute(query, (user_id,))
    daily = [row_to_dict(row) for row in cursor.fetchall()]
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
    query = '''
        SELECT ms.name, ms.balance, SUM(e.amount) as spent
        FROM money_sources ms
        LEFT JOIN expenses e ON ms.id = e.source_id
        WHERE ms.user_id = %s
        GROUP BY ms.id, ms.name, ms.balance
        ORDER BY spent DESC
    ''' if DATABASE_URL else '''
        SELECT ms.name, ms.balance, SUM(e.amount) as spent
        FROM money_sources ms
        LEFT JOIN expenses e ON ms.id = e.source_id
        WHERE ms.user_id = ?
        GROUP BY ms.id
        ORDER BY spent DESC
    '''
    
    cursor.execute(query, (user_id,))
    sources = [row_to_dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return jsonify({'sources': sources})

# Initialize database on startup
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)