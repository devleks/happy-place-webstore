"""
Employee Management Service
Handles employee accounts, roles, permissions, and performance tracking
"""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import and_, desc, func
from models.database_models import db, Employee, POSTransaction
from services.auth_service import AuthService
import secrets


class EmployeeManagementService:
    """Service for managing employees"""

    def __init__(self):
        self.auth_service = AuthService()

    def get_employee_list(self, filters: Dict = None) -> List[Dict]:
        """Get employee list with filters"""
        filters = filters or {}
        query = Employee.query

        if filters.get('role'):
            query = query.filter(Employee.role == filters['role'])

        if filters.get('status') == 'active':
            query = query.filter(Employee.is_active.is_(True))
        elif filters.get('status') == 'inactive':
            query = query.filter(Employee.is_active.is_(False))

        query = query.order_by(Employee.full_name)
        employees = query.all()

        employee_list = []
        for emp in employees:
            employee_list.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'email': emp.email,
                'role': emp.role,
                'is_active': emp.is_active,
                'created_at': emp.created_at.isoformat() if emp.created_at else None,
                'last_login': emp.last_login.isoformat() if hasattr(emp, 'last_login') and emp.last_login else None
            })

        return employee_list

    def get_employee_details(self, employee_id: int) -> Dict:
        """Get employee profile and permissions"""
        employee = Employee.query.get(employee_id)
        if not employee:
            return {'error': 'Employee not found'}

        # Get permissions for role
        permissions = self.auth_service.get_employee_permissions(employee_id)

        # Get performance metrics
        performance = self.get_employee_performance(employee_id, 'month')

        return {
            'id': employee.id,
            'full_name': employee.full_name,
            'email': employee.email,
            'role': employee.role,
            'is_active': employee.is_active,
            'created_at': employee.created_at.isoformat() if employee.created_at else None,
            'totp_enabled': employee.totp_enabled if hasattr(employee, 'totp_enabled') else False,
            'pin_set': employee.pin is not None if hasattr(employee, 'pin') else False,
            'permissions': permissions,
            'performance': performance
        }

    def create_employee(self, data: Dict) -> Dict:
        """Create new employee account"""
        try:
            # Generate temporary password
            temp_password = secrets.token_urlsafe(12)
            
            # Check if employee already exists
            from models.database_models import Employee
            existing_employee = Employee.query.filter_by(email=data['email']).first()
            if existing_employee:
                return {'success': False, 'error': 'Employee with this email already exists'}

            # Create employee directly in database
            from werkzeug.security import generate_password_hash
            employee = Employee(
                email=data['email'],
                password_hash=generate_password_hash(temp_password, method='scrypt'),
                full_name=data['full_name'],
                role=data.get('role', 'staff'),
                is_active=True,
                created_at=datetime.utcnow()
            )

            db.session.add(employee)
            db.session.commit()

            return {
                'success': True,
                'employee_id': employee.id,
                'email': employee.email,
                'full_name': employee.full_name,
                'role': employee.role,
                'temp_password': temp_password
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def update_employee(self, employee_id: int, data: Dict) -> bool:
        """Update employee information"""
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return False

            if 'full_name' in data:
                employee.full_name = data['full_name']
            if 'email' in data:
                employee.email = data['email']
            if 'role' in data:
                employee.role = data['role']
            if 'is_active' in data:
                employee.is_active = data['is_active']

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating employee: {e}")
            return False

    def deactivate_employee(self, employee_id: int) -> bool:
        """Deactivate employee account"""
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return False

            employee.is_active = False
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def reset_employee_password(self, employee_id: int) -> str:
        """Reset password and return temp password"""
        try:
            employee = Employee.query.get(employee_id)
            if not employee:
                return None

            temp_password = secrets.token_urlsafe(12)
            employee.password_hash = self.auth_service._hash_password(temp_password)

            db.session.commit()
            return temp_password
        except Exception:
            db.session.rollback()
            return None

    def disable_employee_2fa(self, employee_id: int) -> bool:
        """Disable 2FA for employee"""
        try:
            result = self.auth_service.disable_2fa(employee_id)
            return result.get('success', False)
        except Exception:
            return False

    def get_employee_activity(self, employee_id: int, days: int = 7) -> List[Dict]:
        """Get employee activity log"""
        start_date = datetime.now() - timedelta(days=days)
        activities = []

        # Get POS transactions
        transactions = POSTransaction.query.filter(
            and_(
                POSTransaction.employee_id == employee_id,
                POSTransaction.created_at >= start_date
            )
        ).order_by(desc(POSTransaction.created_at)).limit(50).all()

        for trans in transactions:
            activities.append({
                'type': 'pos_transaction',
                'timestamp': trans.created_at.isoformat() if trans.created_at else None,
                'description': f'Processed sale KSh {trans.total_amount}',
                'amount': float(trans.total_amount or 0)
            })

        activities.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return activities[:50]

    def get_employee_performance(self, employee_id: int, period: str = 'month') -> Dict:
        """Get employee performance metrics"""
        if period == 'week':
            days = 7
        elif period == 'month':
            days = 30
        else:
            days = 90

        start_date = datetime.now() - timedelta(days=days)

        # POS sales
        pos_stats = db.session.query(
            func.count(POSTransaction.id).label('transaction_count'),
            func.coalesce(func.sum(POSTransaction.total), 0).label('total_sales')
        ).filter(
            and_(
                POSTransaction.employee_id == employee_id,
                POSTransaction.created_at >= start_date,
                POSTransaction.status == 'completed'
            )
        ).first()

        # Calculate average transaction value
        avg_transaction_value = float(pos_stats.total_sales) / pos_stats.transaction_count if pos_stats.transaction_count > 0 else 0

        return {
            'total_sales': float(pos_stats.total_sales or 0),
            'transaction_count': pos_stats.transaction_count or 0,
            'avg_transaction_value': avg_transaction_value,
            'period': period
        }
