"""
Create test employees directly in PostgreSQL database
"""
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.database_models import Employee
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check existing employees
    existing = Employee.query.all()
    print(f"\n📋 Current employees: {len(existing)}")
    
    if len(existing) > 0:
        print("\n✅ Employees already exist:")
        for emp in existing:
            print(f"  • {emp.email} - {emp.full_name} ({emp.role})")
        print("\nNo action needed.")
    else:
        print("\n🌱 Creating test employees...")
        
        # Admin
        admin = Employee(
            email='admin@happyplace.com',
            password_hash=generate_password_hash('admin123'),
            full_name='Administrator',
            role='admin',
            active=True
        )
        db.session.add(admin)
        
        # Manager
        manager = Employee(
            email='manager1@happyplace.co.ke',
            password_hash=generate_password_hash('manager123'),
            full_name='Jane Manager',
            role='manager',
            active=True
        )
        db.session.add(manager)
        
        # Cashier
        cashier = Employee(
            email='cashier1@happyplace.co.ke',
            password_hash=generate_password_hash('cashier123'),
            full_name='John Cashier',
            role='cashier',
            active=True
        )
        db.session.add(cashier)
        
        db.session.commit()
        
        print("✅ Created 3 test employees:")
        print("  • admin@happyplace.com / admin123 (admin)")
        print("  • manager1@happyplace.co.ke / manager123 (manager)")
        print("  • cashier1@happyplace.co.ke / cashier123 (cashier)")
    
    print()
