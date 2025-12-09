"""
Middleware package for Happy Place Boutique API.
Contains authentication and authorization decorators.
"""

from .auth import (
    customer_required,
    employee_required,
    admin_required,
    manager_required,
    packer_required,
    shipper_required,
    get_current_customer,
    get_current_employee
)

__all__ = [
    'customer_required',
    'employee_required',
    'admin_required',
    'manager_required',
    'packer_required',
    'shipper_required',
    'get_current_customer',
    'get_current_employee'
]
