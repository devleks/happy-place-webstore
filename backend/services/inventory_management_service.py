"""
Inventory Management Service
Handles product inventory, stock adjustments, and transfers
"""

from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy import and_, or_, desc
from models.database_models import (
    db, Product, Category, Inventory, ActivityLog
)
from models.extended_models import ProductVariant


class InventoryManagementService:
    """Service for managing inventory"""

    def get_inventory_list(self, filters: Dict = None, page: int = 1, per_page: int = 50) -> Dict:
        """
        Get paginated inventory list with filters

        Args:
            filters: Dict with category_id, status, stock_level, search
            page: Page number
            per_page: Items per page

        Returns:
            Paginated inventory data
        """
        filters = filters or {}

        # Base query
        query = db.session.query(
            ProductVariant.id,
            ProductVariant.sku,
            ProductVariant.size,
            ProductVariant.color,
            Inventory.quantity,
            Inventory.reserved_quantity,
            Product.price,
            Product.id.label('product_id'),
            Product.name.label('product_name'),
            Product.is_active,
            Category.name.label('category_name')
        ).join(Product, ProductVariant.product_id == Product.id)\
         .join(Inventory, ProductVariant.id == Inventory.variant_id)\
         .outerjoin(Category, Product.category_id == Category.id)

        # Apply filters
        if filters.get('category_id'):
            query = query.filter(Product.category_id == filters['category_id'])

        if filters.get('status'):
            if filters['status'] == 'active':
                query = query.filter(Product.is_active.is_(True))
            elif filters['status'] == 'inactive':
                query = query.filter(Product.is_active.is_(False))

        if filters.get('stock_level'):
            if filters['stock_level'] == 'out_of_stock':
                query = query.filter((Inventory.quantity - Inventory.reserved_quantity) <= 0)
            elif filters['stock_level'] == 'low_stock':
                query = query.filter(
                    and_(
                        (Inventory.quantity - Inventory.reserved_quantity) > 0,
                        (Inventory.quantity - Inventory.reserved_quantity) < 10
                    )
                )
            elif filters['stock_level'] == 'in_stock':
                query = query.filter((Inventory.quantity - Inventory.reserved_quantity) >= 10)

        if filters.get('search'):
            search_term = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Product.name.ilike(search_term),
                    ProductVariant.sku.ilike(search_term)
                )
            )

        # Pagination
        total_count = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()

        inventory_list = []
        for item in items:
            available = item.quantity - (item.reserved_quantity or 0)

            # Get primary product image
            from models.database_models import ProductImage
            primary_image = ProductImage.query.filter_by(
                product_id=item.product_id,
                is_primary=True
            ).first()

            image_url = primary_image.image_url if primary_image else None

            inventory_list.append({
                'variant_id': item.id,
                'product_id': item.product_id,
                'product_name': item.product_name,
                'category': item.category_name or 'Uncategorized',
                'sku': item.sku,
                'size': item.size,
                'color': item.color,
                'stock': item.quantity,
                'reserved': item.reserved_quantity or 0,
                'available': available,
                'price': float(item.price) if item.price else 0,
                'status': 'active' if item.is_active else 'inactive',
                'stock_status': self._get_stock_status(available),
                'image_url': image_url
            })

        return {
            'items': inventory_list,
            'total': total_count,
            'page': page,
            'per_page': per_page,
            'total_pages': (total_count + per_page - 1) // per_page
        }

    def get_product_details(self, product_id: int) -> Dict:
        """
        Get complete product details with all variants

        Args:
            product_id: Product ID

        Returns:
            Product details dictionary
        """
        product = Product.query.get(product_id)
        if not product:
            return {'error': 'Product not found'}

        # Get variants with their inventory
        variants = db.session.query(
            ProductVariant, Inventory
        ).join(Inventory, ProductVariant.id == Inventory.variant_id)\
         .filter(ProductVariant.product_id == product_id).all()

        variant_list = []
        total_stock = 0
        total_reserved = 0

        for variant, inventory in variants:
            available = inventory.quantity - (inventory.reserved_quantity or 0)
            total_stock += inventory.quantity or 0
            total_reserved += inventory.reserved_quantity or 0

            variant_list.append({
                'id': variant.id,
                'sku': variant.sku,
                'size': variant.size,
                'color': variant.color,
                'stock': inventory.quantity or 0,
                'reserved': inventory.reserved_quantity or 0,
                'available': available,
                'price': float(product.price) if product.price else 0,
                'stock_status': self._get_stock_status(available)
            })

        return {
            'id': product.id,
            'name': product.name,
            'description': product.description,
            'category_id': product.category_id,
            'category_name': product.category.name if product.category else None,
            'is_active': product.is_active,
            'is_clearance': product.is_clearance or False,
            'created_at': product.created_at.isoformat() if product.created_at else None,
            'variants': variant_list,
            'total_stock': total_stock,
            'total_reserved': total_reserved,
            'total_available': total_stock - total_reserved
        }

    def update_product(self, product_id: int, data: Dict) -> bool:
        """
        Update product information

        Args:
            product_id: Product ID
            data: Updated product data

        Returns:
            Success boolean
        """
        try:
            product = Product.query.get(product_id)
            if not product:
                return False

            # Update allowed fields
            if 'name' in data:
                product.name = data['name']
            if 'description' in data:
                product.description = data['description']
            if 'category_id' in data:
                product.category_id = data['category_id']
            if 'is_active' in data:
                product.is_active = data['is_active']
            if 'is_clearance' in data:
                product.is_clearance = data['is_clearance']

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error updating product: {e}")
            return False

    def bulk_update_stock(self, updates: List[Dict], employee_id: int) -> Dict:
        """
        Bulk update stock quantities

        Args:
            updates: List of {variant_id, quantity, reason}
            employee_id: Employee performing the update

        Returns:
            Result dictionary with success/failure counts
        """
        success_count = 0
        failure_count = 0
        errors = []

        for update in updates:
            try:
                variant_id = update.get('variant_id')
                quantity = update.get('quantity')
                reason = update.get('reason', 'Bulk stock update')

                # Get inventory record
                inventory = Inventory.query.filter_by(variant_id=variant_id).first()
                if not inventory:
                    failure_count += 1
                    errors.append(f"Inventory for variant {variant_id} not found")
                    continue

                old_quantity = inventory.quantity
                inventory.quantity = quantity

                # Log the change
                self._log_inventory_change(
                    variant_id=variant_id,
                    change_type='adjustment',
                    quantity_change=quantity - old_quantity,
                    reason=reason,
                    employee_id=employee_id
                )

                success_count += 1
            except Exception as e:
                failure_count += 1
                errors.append(f"Error updating variant {update.get('variant_id')}: {str(e)}")
                db.session.rollback()
                continue

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': f"Failed to commit changes: {str(e)}"
            }

        return {
            'success': True,
            'updated': success_count,
            'failed': failure_count,
            'errors': errors
        }

    def adjust_stock(self, variant_id: int, adjustment: Dict, employee_id: int) -> bool:
        """
        Adjust stock with reason tracking

        Args:
            variant_id: Variant ID
            adjustment: {type: 'add'|'remove'|'set', quantity, reason}
            employee_id: Employee performing adjustment

        Returns:
            Success boolean
        """
        try:
            inventory = Inventory.query.filter_by(variant_id=variant_id).first()
            if not inventory:
                return False

            old_quantity = inventory.quantity
            adjustment_type = adjustment.get('type', 'set')
            quantity = adjustment.get('quantity', 0)
            reason = adjustment.get('reason', 'Stock adjustment')

            if adjustment_type == 'add':
                new_quantity = old_quantity + quantity
                change_type = 'restock'
            elif adjustment_type == 'remove':
                new_quantity = old_quantity - quantity
                change_type = 'adjustment'
            else:  # set
                new_quantity = quantity
                change_type = 'adjustment'

            # Ensure stock doesn't go negative
            if new_quantity < 0:
                new_quantity = 0

            inventory.quantity = new_quantity

            # Log the change
            self._log_inventory_change(
                variant_id=variant_id,
                change_type=change_type,
                quantity_change=new_quantity - old_quantity,
                reason=reason,
                employee_id=employee_id
            )

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error adjusting stock: {e}")
            return False

    def transfer_stock(self, transfer_data: Dict, employee_id: int) -> bool:
        """
        Transfer stock between online and store (placeholder for future multi-location)

        Args:
            transfer_data: {variant_id, from_location, to_location, quantity, notes}
            employee_id: Employee performing transfer

        Returns:
            Success boolean
        """
        try:
            variant_id = transfer_data.get('variant_id')
            quantity = transfer_data.get('quantity', 0)
            notes = transfer_data.get('notes', '')

            # Verify inventory exists
            inventory = Inventory.query.filter_by(variant_id=variant_id).first()
            if not inventory:
                return False

            # For now, just log the transfer
            # In the future, this would handle multi-location inventory
            self._log_inventory_change(
                variant_id=variant_id,
                change_type='transfer',
                quantity_change=0,  # No net change for transfer
                reason=f"Transfer: {notes}",
                employee_id=employee_id
            )

            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error transferring stock: {e}")
            return False

    def get_stock_history(self, variant_id: int, days: int = 30) -> List[Dict]:
        """
        Get stock movement history for a variant

        Args:
            variant_id: Variant ID
            days: Number of days of history

        Returns:
            List of inventory changes
        """
        try:
            start_date = datetime.now() - timedelta(days=days)

            # Query ActivityLog for inventory changes related to this variant
            logs = ActivityLog.query\
                .filter(
                    and_(
                        ActivityLog.resource_type == 'inventory',
                        ActivityLog.resource_id == variant_id,
                        ActivityLog.timestamp >= start_date
                    )
                )\
                .order_by(desc(ActivityLog.timestamp))\
                .all()

            history = []
            for log in logs:
                # Parse details JSON if available
                import json
                details_dict = {}
                if log.details:
                    try:
                        details_dict = json.loads(log.details)
                    except:
                        details_dict = {'raw': log.details}

                history.append({
                    'id': log.id,
                    'date': log.timestamp.isoformat() if log.timestamp else None,
                    'type': log.action,
                    'quantity_change': details_dict.get('quantity_change', 0),
                    'reason': details_dict.get('reason', log.action),
                    'employee': log.employee.full_name if log.employee else 'System',
                    'employee_id': log.employee_id
                })

            return history
        except Exception as e:
            print(f"Error getting stock history: {e}")
            return []

    def delete_product(self, product_id: int) -> bool:
        """
        Soft delete product (mark as inactive)

        Args:
            product_id: Product ID

        Returns:
            Success boolean
        """
        try:
            product = Product.query.get(product_id)
            if not product:
                return False

            product.is_active = False
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting product: {e}")
            return False

    # ===== PRIVATE HELPER METHODS =====

    def _get_stock_status(self, quantity: int) -> str:
        """Determine stock status based on quantity"""
        if quantity <= 0:
            return 'out_of_stock'
        elif quantity < 10:
            return 'low_stock'
        else:
            return 'in_stock'

    def _log_inventory_change(self, variant_id: int, change_type: str,
                              quantity_change: int, reason: str, employee_id: int):
        """Log inventory change to ActivityLog table"""
        try:
            import json
            details = json.dumps({
                'quantity_change': quantity_change,
                'reason': reason,
                'change_type': change_type
            })

            log = ActivityLog(
                employee_id=employee_id,
                action=change_type,
                resource_type='inventory',
                resource_id=variant_id,
                details=details,
                timestamp=datetime.now()
            )
            db.session.add(log)
        except Exception as e:
            print(f"Error logging inventory change: {e}")
