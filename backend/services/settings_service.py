"""
Settings Service
Manages system-wide settings and configuration
"""

from datetime import datetime
from typing import Dict, List, Optional
from sqlalchemy import and_, or_
from models.database_models import db
from decimal import Decimal
import json


# Since SystemSettings model doesn't exist yet, we'll create a simple implementation
# that stores settings as JSON in the database or uses a simple key-value table
# For now, we'll use in-memory settings with database persistence planned for future


class SystemSettings(db.Model):
    """
    System settings key-value store
    Stores application configuration and business rules
    """
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    setting_key = db.Column('setting_key', db.String(100), unique=True, nullable=False, index=True)
    setting_value = db.Column('setting_value', db.Text)
    setting_type = db.Column('setting_type', db.String(20), nullable=False, default='string')
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = db.Column(db.Integer, db.ForeignKey('employees.id'))

    def to_dict(self):
        """Convert setting to dictionary"""
        # Parse value based on type
        parsed_value = self._parse_value()

        return {
            'id': self.id,
            'key': self.setting_key,
            'value': parsed_value,
            'value_type': self.setting_type,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def _parse_value(self):
        """Parse value based on type"""
        try:
            if self.setting_type == 'integer':
                return int(self.setting_value)
            elif self.setting_type == 'float':
                return float(self.setting_value)
            elif self.setting_type == 'boolean':
                return self.setting_value.lower() in ('true', '1', 'yes')
            elif self.setting_type == 'json':
                return json.loads(self.setting_value)
            else:  # string
                return self.setting_value
        except (ValueError, json.JSONDecodeError):
            return self.setting_value


class SettingsService:
    """Service for managing system settings"""

    # Default settings
    DEFAULT_SETTINGS = {
        # Business Rules
        'return_window_days': {
            'value': '2',
            'value_type': 'integer',
            'category': 'business',
            'description': 'Number of days customers can return items',
            'is_public': True
        },
        'restocking_fee_percentage': {
            'value': '10',
            'value_type': 'float',
            'category': 'business',
            'description': 'Restocking fee percentage for returns',
            'is_public': True
        },
        'low_stock_threshold': {
            'value': '10',
            'value_type': 'integer',
            'category': 'inventory',
            'description': 'Stock quantity threshold for low stock alerts',
            'is_public': False
        },
        'referral_discount_percentage': {
            'value': '5',
            'value_type': 'float',
            'category': 'business',
            'description': 'Referral code discount percentage',
            'is_public': True
        },

        # Shipping
        'nairobi_shipping_cost': {
            'value': '0',
            'value_type': 'float',
            'category': 'shipping',
            'description': 'Shipping cost for Nairobi (free)',
            'is_public': True
        },
        'outside_nairobi_base_cost': {
            'value': '300',
            'value_type': 'float',
            'category': 'shipping',
            'description': 'Base shipping cost outside Nairobi',
            'is_public': True
        },
        'shipping_cost_per_kg': {
            'value': '50',
            'value_type': 'float',
            'category': 'shipping',
            'description': 'Additional cost per kg for shipping',
            'is_public': True
        },

        # Store Info
        'store_name': {
            'value': 'Happy Place Boutique',
            'value_type': 'string',
            'category': 'general',
            'description': 'Store name',
            'is_public': True
        },
        'store_email': {
            'value': 'info@happyplaceboutique.com',
            'value_type': 'string',
            'category': 'general',
            'description': 'Store contact email',
            'is_public': True
        },
        'store_phone': {
            'value': '+254-XXX-XXXXXX',
            'value_type': 'string',
            'category': 'general',
            'description': 'Store contact phone',
            'is_public': True
        },

        # Tax
        'tax_rate': {
            'value': '0',
            'value_type': 'float',
            'category': 'business',
            'description': 'Tax rate percentage (0 for Kenya)',
            'is_public': True
        },

        # Currency
        'currency': {
            'value': 'KSh',
            'value_type': 'string',
            'category': 'general',
            'description': 'Currency symbol',
            'is_public': True
        },
        'currency_code': {
            'value': 'KES',
            'value_type': 'string',
            'category': 'general',
            'description': 'Currency ISO code',
            'is_public': True
        },

        # Payment
        'mpesa_enabled': {
            'value': 'true',
            'value_type': 'boolean',
            'category': 'payment',
            'description': 'Enable M-Pesa payments',
            'is_public': True
        },
        'cash_on_delivery_enabled': {
            'value': 'false',
            'value_type': 'boolean',
            'category': 'payment',
            'description': 'Enable cash on delivery',
            'is_public': True
        },

        # Notifications
        'order_confirmation_email': {
            'value': 'true',
            'value_type': 'boolean',
            'category': 'notifications',
            'description': 'Send order confirmation emails',
            'is_public': False
        },
        'low_stock_notifications': {
            'value': 'true',
            'value_type': 'boolean',
            'category': 'notifications',
            'description': 'Send low stock notifications to admin',
            'is_public': False
        }
    }

    def __init__(self):
        """Initialize settings service and ensure defaults exist"""
        self._ensure_defaults()

    def _ensure_defaults(self):
        """Ensure default settings exist in database"""
        # Skip this for now as the settings already exist in the database
        pass

    def get_all_settings(self) -> Dict:
        """
        Get all system settings

        Returns:
            Dictionary of all settings grouped by category
        """
        try:
            settings = SystemSettings.query.all()

            # Group by category
            grouped = {}
            for setting in settings:
                category = setting.category
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(setting.to_dict())

            return {
                'success': True,
                'settings': grouped,
                'flat': {s.key: s._parse_value() for s in settings}
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_setting(self, key: str) -> Optional[any]:
        """
        Get a specific setting value

        Args:
            key: Setting key

        Returns:
            Setting value or None if not found
        """
        try:
            setting = SystemSettings.query.filter_by(setting_key=key).first()
            if setting:
                return setting._parse_value()
            return None

        except Exception as e:
            print(f"Error getting setting {key}: {e}")
            return None

    def update_setting(self, key: str, value: any, updated_by: int = None) -> Dict:
        """
        Update a single setting

        Args:
            key: Setting key
            value: New value
            updated_by: Employee ID making the update

        Returns:
            Result dictionary
        """
        try:
            setting = SystemSettings.query.filter_by(setting_key=key).first()

            if not setting:
                return {'success': False, 'error': f'Setting {key} not found'}

            # Convert value to string based on type
            if setting.setting_type == 'boolean':
                setting.setting_value = 'true' if value else 'false'
            elif setting.setting_type == 'json':
                setting.setting_value = json.dumps(value)
            else:
                setting.setting_value = str(value)

            setting.updated_by = updated_by
            setting.updated_at = datetime.utcnow()

            db.session.commit()

            return {
                'success': True,
                'setting': setting.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def update_settings_bulk(self, settings: Dict, updated_by: int = None) -> Dict:
        """
        Update multiple settings at once

        Args:
            settings: Dictionary of key-value pairs
            updated_by: Employee ID making the update

        Returns:
            Result dictionary with success/failure counts
        """
        success_count = 0
        failure_count = 0
        errors = []

        try:
            for key, value in settings.items():
                setting = SystemSettings.query.filter_by(key=key).first()

                if not setting:
                    failure_count += 1
                    errors.append(f"Setting {key} not found")
                    continue

                try:
                    # Convert value to string based on type
                    if setting.value_type == 'boolean':
                        setting.value = 'true' if value else 'false'
                    elif setting.value_type == 'json':
                        setting.value = json.dumps(value)
                    else:
                        setting.value = str(value)

                    setting.updated_by = updated_by
                    setting.updated_at = datetime.utcnow()
                    success_count += 1

                except Exception as e:
                    failure_count += 1
                    errors.append(f"Error updating {key}: {str(e)}")

            db.session.commit()

            return {
                'success': True,
                'updated': success_count,
                'failed': failure_count,
                'errors': errors
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

    def get_public_settings(self) -> Dict:
        """
        Get settings that are public (can be accessed by frontend)

        Returns:
            Dictionary of public settings
        """
        try:
            # For now, just return currency settings
            currency = self.get_setting('currency_symbol')
            currency_code = self.get_setting('currency_code')

            return {
                'success': True,
                'settings': {
                    'currency': currency or 'KSh',
                    'currency_code': currency_code or 'KES'
                }
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_settings_by_category(self, category: str) -> Dict:
        """
        Get all settings in a specific category

        Args:
            category: Category name (general, business, payment, etc.)

        Returns:
            Dictionary of settings in category
        """
        try:
            settings = SystemSettings.query.filter_by(category=category).all()

            return {
                'success': True,
                'category': category,
                'settings': [s.to_dict() for s in settings]
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def create_setting(self, key: str, value: any, value_type: str = 'string',
                      category: str = 'general', description: str = None,
                      is_public: bool = False, created_by: int = None) -> Dict:
        """
        Create a new setting

        Args:
            key: Setting key (unique)
            value: Setting value
            value_type: Type of value (string, integer, float, boolean, json)
            category: Setting category
            description: Setting description
            is_public: Whether setting is public
            created_by: Employee ID creating the setting

        Returns:
            Result dictionary
        """
        try:
            # Check if key already exists
            existing = SystemSettings.query.filter_by(key=key).first()
            if existing:
                return {'success': False, 'error': 'Setting key already exists'}

            # Convert value to string based on type
            if value_type == 'boolean':
                str_value = 'true' if value else 'false'
            elif value_type == 'json':
                str_value = json.dumps(value)
            else:
                str_value = str(value)

            # Create setting
            setting = SystemSettings(
                key=key,
                value=str_value,
                value_type=value_type,
                category=category,
                description=description,
                is_public=is_public,
                updated_by=created_by
            )

            db.session.add(setting)
            db.session.commit()

            return {
                'success': True,
                'setting': setting.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def delete_setting(self, key: str) -> bool:
        """
        Delete a setting

        Args:
            key: Setting key

        Returns:
            Success boolean
        """
        try:
            setting = SystemSettings.query.filter_by(key=key).first()
            if not setting:
                return False

            # Don't allow deletion of default settings
            if key in self.DEFAULT_SETTINGS:
                return False

            db.session.delete(setting)
            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"Error deleting setting: {e}")
            return False

    def reset_to_defaults(self, category: str = None) -> Dict:
        """
        Reset settings to default values

        Args:
            category: Optional category to reset (None for all)

        Returns:
            Result dictionary
        """
        try:
            reset_count = 0

            for key, config in self.DEFAULT_SETTINGS.items():
                # Skip if category specified and doesn't match
                if category and config['category'] != category:
                    continue

                setting = SystemSettings.query.filter_by(key=key).first()
                if setting:
                    setting.value = config['value']
                    setting.updated_at = datetime.utcnow()
                    reset_count += 1

            db.session.commit()

            return {
                'success': True,
                'reset_count': reset_count,
                'category': category or 'all'
            }

        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
