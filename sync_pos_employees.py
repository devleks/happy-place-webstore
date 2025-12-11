#!/usr/bin/env python3
"""
Manual Employee Sync for POS App
Syncs employees from backend API to POS SQLite database
"""

import sqlite3
import requests
import json
import os
from datetime import datetime
from pathlib import Path

# Database path
DB_PATH = Path.home() / "Library/Application Support/happy-place-pos/pos.db"
BACKEND_URL = "http://127.0.0.1:5001/api/employees/sync"

def sync_employees():
    print("🔄 Starting employee sync...\n")

    # Connect to database
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    try:
        # Get sync token
        cursor.execute("SELECT value FROM sync_metadata WHERE key = 'sync_token'")
        token_row = cursor.fetchone()

        if not token_row:
            print("❌ No sync token found. Please configure sync token first.")
            return False

        sync_token = token_row[0]
        print(f"🔑 Sync token: {sync_token[:20]}...\n")

        # Fetch employees from backend
        print("📡 Fetching employees from backend...")
        headers = {
            'Authorization': f'Bearer {sync_token}',
            'Content-Type': 'application/json'
        }

        response = requests.get(BACKEND_URL, headers=headers)
        print(f"📊 Response status: {response.status_code}\n")

        if response.status_code != 200:
            print(f"❌ Sync failed: {response.text}")
            return False

        data = response.json()

        if data.get('success') and data.get('employees'):
            employees = data['employees']
            print(f"📦 Received {len(employees)} employees\n")

            sync_time = datetime.utcnow().isoformat()
            inserted_count = 0

            # Insert each employee
            for emp in employees:
                try:
                    print(f"👤 Syncing: {emp['email']} ({emp['role']})")

                    cursor.execute("""
                        INSERT OR REPLACE INTO employees
                        (backend_id, email, full_name, role, password_hash, permissions,
                         is_active, last_synced_at, sync_version, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        emp['id'],
                        emp['email'],
                        emp['full_name'],
                        emp['role'],
                        emp['password_hash'],
                        json.dumps(emp.get('permissions', {})),
                        1 if emp['is_active'] else 0,
                        sync_time,
                        emp.get('version', 1),
                        sync_time
                    ))

                    inserted_count += 1

                except Exception as emp_error:
                    print(f"❌ Failed to insert {emp['email']}: {emp_error}")

            # Commit changes
            conn.commit()

            print(f"\n✅ Successfully synced {inserted_count}/{len(employees)} employees")

            # Save sync version
            cursor.execute("""
                INSERT OR REPLACE INTO sync_metadata (key, value, updated_at)
                VALUES ('last_employee_sync', ?, ?)
            """, (data['sync_version'], datetime.utcnow().isoformat()))

            conn.commit()

            print(f"📌 Saved sync version: {data['sync_version']}")

            # Verify
            cursor.execute("SELECT COUNT(*) FROM employees")
            count = cursor.fetchone()[0]
            print(f"\n📊 Total employees in database: {count}")

            # Show admin account
            cursor.execute("SELECT email, role FROM employees WHERE role = 'admin' LIMIT 1")
            admin = cursor.fetchone()
            if admin:
                print(f"\n🔐 Admin account available: {admin[0]}")
                print(f"   Role: {admin[1]}")
                print(f"   Password: admin123 (from backend)")

            return True

        else:
            print("❌ No employee data received")
            return False

    except Exception as error:
        print(f"❌ Sync error: {error}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        conn.close()

if __name__ == '__main__':
    success = sync_employees()
    exit(0 if success else 1)
