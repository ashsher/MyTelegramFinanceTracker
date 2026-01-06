"""
Database initialization and management script
Run this to reset or inspect your database
"""

import sqlite3
from datetime import datetime

DATABASE = 'finance.db'

def create_tables():
    """Create all database tables"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("Creating tables...")
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Users table created")
    
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
    print("✓ Money sources table created")
    
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
    print("✓ Expenses table created")
    
    conn.commit()
    conn.close()
    print("\nDatabase setup complete!")

def add_sample_data():
    """Add sample data for testing"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("\nAdding sample data...")
    
    # Add test user
    cursor.execute('''
        INSERT OR IGNORE INTO users (telegram_id, username)
        VALUES (123456789, 'testuser')
    ''')
    user_id = cursor.lastrowid or 1
    print(f"✓ Test user created (ID: {user_id})")
    
    # Add sample money sources
    sources = [
        ('Credit Card 1', 1000.00, 'card'),
        ('Cash', 500.00, 'cash'),
        ('PayPal', 750.00, 'paypal')
    ]
    
    for name, balance, source_type in sources:
        cursor.execute('''
            INSERT INTO money_sources (user_id, name, balance, type)
            VALUES (?, ?, ?, ?)
        ''', (user_id, name, balance, source_type))
    print(f"✓ Added {len(sources)} money sources")
    
    # Add sample expenses
    expenses = [
        (1, 45.50, 'Food', 'Grocery shopping'),
        (1, 120.00, 'Shopping', 'New shoes'),
        (2, 15.00, 'Transport', 'Taxi ride'),
        (3, 30.00, 'Entertainment', 'Movie tickets')
    ]
    
    for source_id, amount, category, note in expenses:
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
    
    print(f"✓ Added {len(expenses)} sample expenses")
    
    conn.commit()
    conn.close()
    print("\nSample data added successfully!")

def view_database():
    """View current database contents"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("\n" + "="*50)
    print("DATABASE CONTENTS")
    print("="*50)
    
    # Users
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    print(f"\n📊 USERS ({len(users)} total):")
    print("-" * 50)
    for user in users:
        print(f"ID: {user['id']}, Telegram ID: {user['telegram_id']}, Username: {user['username']}")
    
    # Money Sources
    cursor.execute('SELECT * FROM money_sources')
    sources = cursor.fetchall()
    print(f"\n💰 MONEY SOURCES ({len(sources)} total):")
    print("-" * 50)
    for source in sources:
        print(f"ID: {source['id']}, Name: {source['name']}, Balance: ${source['balance']:.2f}, Type: {source['type']}")
    
    # Expenses
    cursor.execute('''
        SELECT e.*, ms.name as source_name 
        FROM expenses e
        JOIN money_sources ms ON e.source_id = ms.id
        ORDER BY e.created_at DESC
    ''')
    expenses = cursor.fetchall()
    print(f"\n💳 EXPENSES ({len(expenses)} total):")
    print("-" * 50)
    for expense in expenses:
        print(f"ID: {expense['id']}, Amount: ${expense['amount']:.2f}, Category: {expense['category']}")
        print(f"   Source: {expense['source_name']}, Note: {expense['note']}")
        print(f"   Date: {expense['created_at']}")
        print()
    
    conn.close()

def reset_database():
    """Delete all data and recreate tables"""
    response = input("\n⚠️  WARNING: This will delete ALL data. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Reset cancelled.")
        return
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    print("\nResetting database...")
    cursor.execute('DROP TABLE IF EXISTS expenses')
    cursor.execute('DROP TABLE IF EXISTS money_sources')
    cursor.execute('DROP TABLE IF EXISTS users')
    print("✓ Old tables dropped")
    
    conn.commit()
    conn.close()
    
    create_tables()
    print("\n✓ Database reset complete!")

def main():
    """Main menu"""
    while True:
        print("\n" + "="*50)
        print("FINANCE TRACKER - Database Management")
        print("="*50)
        print("1. Create/Initialize Database")
        print("2. Add Sample Data (for testing)")
        print("3. View Database Contents")
        print("4. Reset Database (delete all data)")
        print("5. Exit")
        print("="*50)
        
        choice = input("\nEnter your choice (1-5): ").strip()
        
        if choice == '1':
            create_tables()
        elif choice == '2':
            add_sample_data()
        elif choice == '3':
            view_database()
        elif choice == '4':
            reset_database()
        elif choice == '5':
            print("\nGoodbye!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()