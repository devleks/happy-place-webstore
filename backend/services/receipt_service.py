"""
Receipt Generation Service
Handles thermal receipt and PDF receipt generation for POS transactions.
"""

from typing import Dict, Optional
from datetime import datetime
from io import BytesIO
import base64


class ReceiptService:
    """Service for generating receipts in various formats"""

    # Store information
    STORE_INFO = {
        'name': 'Happy Place Boutique',
        'address': 'Kimathi Street, City Centre',
        'city': 'Nairobi, Kenya',
        'phone': '+254 700 123456',
        'email': 'store@happyplace.co.ke',
        'tax_id': 'P051234567X',
        'website': 'www.happyplace.co.ke'
    }

    @staticmethod
    def format_currency(amount: float) -> str:
        """Format amount as Kenyan Shillings"""
        return f"KSh {amount:,.2f}"

    @staticmethod
    def format_datetime(dt: datetime) -> str:
        """Format datetime for receipt"""
        return dt.strftime("%d/%m/%Y %H:%M:%S")

    @staticmethod
    def generate_thermal_receipt(transaction: Dict, width: int = 32) -> str:
        """
        Generate thermal receipt text (58mm or 80mm paper).

        Args:
            transaction: Transaction data from POSService.get_transaction()
            width: Character width (32 for 58mm, 48 for 80mm)

        Returns:
            str: Formatted receipt text ready for thermal printer
        """
        lines = []

        # Helper functions for formatting
        def center(text: str) -> str:
            return text.center(width)

        def left_right(left: str, right: str) -> str:
            space = width - len(left) - len(right)
            return left + (' ' * space) + right

        def separator(char: str = '-') -> str:
            return char * width

        # Header
        lines.append(center('=' * width))
        lines.append(center(ReceiptService.STORE_INFO['name'].upper()))
        lines.append(center(ReceiptService.STORE_INFO['address']))
        lines.append(center(ReceiptService.STORE_INFO['city']))
        lines.append(center(f"Tel: {ReceiptService.STORE_INFO['phone']}"))
        lines.append(center(f"PIN: {ReceiptService.STORE_INFO['tax_id']}"))
        lines.append(center('=' * width))
        lines.append('')

        # Transaction details
        lines.append(center('SALES RECEIPT'))
        lines.append('')
        lines.append(left_right('Receipt No:', transaction['transaction_number']))
        lines.append(left_right('Date:', ReceiptService.format_datetime(transaction['created_at'])))
        lines.append(left_right('Cashier:', transaction['employee_name']))
        if transaction.get('shift_number'):
            lines.append(left_right('Shift:', transaction['shift_number']))
        lines.append(separator())
        lines.append('')

        # Items header
        lines.append('ITEMS')
        lines.append(separator())

        # Items
        for item in transaction['items']:
            # Product name (may wrap)
            product_line = f"{item['product_name']}"
            if len(product_line) > width:
                lines.append(product_line[:width])
                lines.append(product_line[width:width*2])
            else:
                lines.append(product_line)

            # Size and color
            variant_info = f"  {item['size']}, {item['color']}"
            lines.append(variant_info)

            # Quantity, price, total
            qty_price = f"  {item['quantity']} x {ReceiptService.format_currency(item['unit_price'])}"
            total = ReceiptService.format_currency(item['total_price'])
            lines.append(left_right(qty_price, total))
            lines.append('')

        lines.append(separator())

        # Totals
        lines.append(left_right('Subtotal:', ReceiptService.format_currency(transaction['subtotal'])))
        lines.append(left_right('VAT (16%):', ReceiptService.format_currency(transaction['tax'])))
        lines.append(separator('='))
        lines.append(left_right('TOTAL:', ReceiptService.format_currency(transaction['total'])))
        lines.append(separator('='))
        lines.append('')

        # Payment details
        payment_method = transaction['payment_method'].upper()
        if payment_method == 'CASH':
            lines.append(left_right('Payment Method:', 'CASH'))
            if transaction.get('cash_tendered'):
                lines.append(left_right('Cash Tendered:', ReceiptService.format_currency(transaction['cash_tendered'])))
                lines.append(left_right('Change:', ReceiptService.format_currency(transaction['change_given'])))
        elif payment_method == 'MPESA':
            lines.append(left_right('Payment Method:', 'M-PESA'))
        elif payment_method == 'CARD':
            lines.append(left_right('Payment Method:', 'CARD'))

        lines.append('')
        lines.append(separator())

        # Footer
        lines.append('')
        lines.append(center('Thank you for shopping with us!'))
        lines.append(center('Visit us again soon'))
        lines.append('')
        lines.append(center(ReceiptService.STORE_INFO['website']))
        lines.append(center('For inquiries: ' + ReceiptService.STORE_INFO['email']))
        lines.append('')

        # Void status
        if transaction.get('voided_at'):
            lines.append('')
            lines.append(center('*** VOIDED ***'))
            lines.append(center(f"Voided: {ReceiptService.format_datetime(transaction['voided_at'])}"))
            if transaction.get('void_reason'):
                lines.append(center(f"Reason: {transaction['void_reason']}"))
            lines.append('')

        # Tax compliance
        lines.append(center('VAT INCLUSIVE'))
        lines.append(center('Goods sold are not returnable'))
        lines.append('')
        lines.append(center('=' * width))
        lines.append('')

        return '\n'.join(lines)

    @staticmethod
    def generate_html_receipt(transaction: Dict) -> str:
        """
        Generate HTML receipt for display or PDF conversion.

        Args:
            transaction: Transaction data from POSService.get_transaction()

        Returns:
            str: HTML receipt content
        """
        items_html = ''
        for item in transaction['items']:
            items_html += f"""
            <tr>
                <td>
                    <strong>{item['product_name']}</strong><br>
                    <small>{item['size']}, {item['color']}</small>
                </td>
                <td style="text-align: center;">{item['quantity']}</td>
                <td style="text-align: right;">{ReceiptService.format_currency(item['unit_price'])}</td>
                <td style="text-align: right;">{ReceiptService.format_currency(item['total_price'])}</td>
            </tr>
            """

        # Payment details
        payment_details = ''
        payment_method = transaction['payment_method'].upper()
        if payment_method == 'CASH' and transaction.get('cash_tendered'):
            payment_details = f"""
            <tr>
                <td colspan="3" style="text-align: right;"><strong>Cash Tendered:</strong></td>
                <td style="text-align: right;">{ReceiptService.format_currency(transaction['cash_tendered'])}</td>
            </tr>
            <tr>
                <td colspan="3" style="text-align: right;"><strong>Change:</strong></td>
                <td style="text-align: right;">{ReceiptService.format_currency(transaction['change_given'])}</td>
            </tr>
            """

        # Void status
        void_banner = ''
        if transaction.get('voided_at'):
            void_banner = f"""
            <div style="background: #dc3545; color: white; padding: 15px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <h2 style="margin: 0;">*** VOIDED ***</h2>
                <p style="margin: 5px 0;">Voided: {ReceiptService.format_datetime(transaction['voided_at'])}</p>
                {f'<p style="margin: 5px 0;">Reason: {transaction["void_reason"]}</p>' if transaction.get('void_reason') else ''}
            </div>
            """

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Receipt - {transaction['transaction_number']}</title>
            <style>
                body {{
                    font-family: 'Courier New', monospace;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background: #f5f5f5;
                }}
                .receipt {{
                    background: white;
                    padding: 40px;
                    border: 1px solid #ddd;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header {{
                    text-align: center;
                    border-bottom: 2px solid #333;
                    padding-bottom: 20px;
                    margin-bottom: 20px;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    text-transform: uppercase;
                }}
                .header p {{
                    margin: 5px 0;
                    font-size: 12px;
                }}
                .transaction-info {{
                    margin-bottom: 20px;
                    font-size: 12px;
                }}
                .transaction-info table {{
                    width: 100%;
                }}
                .items {{
                    margin: 20px 0;
                }}
                .items table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .items th {{
                    background: #f8f9fa;
                    padding: 10px;
                    text-align: left;
                    border-bottom: 2px solid #333;
                    font-size: 12px;
                }}
                .items td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                    font-size: 12px;
                }}
                .totals {{
                    margin-top: 20px;
                    font-size: 12px;
                }}
                .totals table {{
                    width: 100%;
                    margin-left: auto;
                }}
                .totals .total-row {{
                    border-top: 2px solid #333;
                    font-weight: bold;
                    font-size: 14px;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #333;
                    font-size: 11px;
                }}
                @media print {{
                    body {{
                        background: white;
                        padding: 0;
                    }}
                    .receipt {{
                        box-shadow: none;
                        border: none;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="receipt">
                <div class="header">
                    <h1>{ReceiptService.STORE_INFO['name']}</h1>
                    <p>{ReceiptService.STORE_INFO['address']}</p>
                    <p>{ReceiptService.STORE_INFO['city']}</p>
                    <p>Tel: {ReceiptService.STORE_INFO['phone']} | Email: {ReceiptService.STORE_INFO['email']}</p>
                    <p>PIN: {ReceiptService.STORE_INFO['tax_id']}</p>
                </div>

                {void_banner}

                <div class="transaction-info">
                    <table>
                        <tr>
                            <td><strong>Receipt No:</strong></td>
                            <td>{transaction['transaction_number']}</td>
                            <td><strong>Date:</strong></td>
                            <td>{ReceiptService.format_datetime(transaction['created_at'])}</td>
                        </tr>
                        <tr>
                            <td><strong>Cashier:</strong></td>
                            <td>{transaction['employee_name']}</td>
                            <td><strong>Payment:</strong></td>
                            <td>{payment_method}</td>
                        </tr>
                    </table>
                </div>

                <div class="items">
                    <table>
                        <thead>
                            <tr>
                                <th>Item</th>
                                <th style="text-align: center;">Qty</th>
                                <th style="text-align: right;">Price</th>
                                <th style="text-align: right;">Total</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                </div>

                <div class="totals">
                    <table>
                        <tr>
                            <td colspan="3" style="text-align: right;"><strong>Subtotal:</strong></td>
                            <td style="text-align: right;">{ReceiptService.format_currency(transaction['subtotal'])}</td>
                        </tr>
                        <tr>
                            <td colspan="3" style="text-align: right;"><strong>VAT (16%):</strong></td>
                            <td style="text-align: right;">{ReceiptService.format_currency(transaction['tax'])}</td>
                        </tr>
                        <tr class="total-row">
                            <td colspan="3" style="text-align: right; padding-top: 10px;"><strong>TOTAL:</strong></td>
                            <td style="text-align: right; padding-top: 10px;">{ReceiptService.format_currency(transaction['total'])}</td>
                        </tr>
                        {payment_details}
                    </table>
                </div>

                <div class="footer">
                    <p><strong>Thank you for shopping with us!</strong></p>
                    <p>Visit us again soon</p>
                    <p>{ReceiptService.STORE_INFO['website']}</p>
                    <p style="margin-top: 15px;">VAT INCLUSIVE | Goods sold are not returnable</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    @staticmethod
    def generate_email_receipt_html(transaction: Dict, customer_email: str) -> str:
        """
        Generate email-friendly HTML receipt.

        Args:
            transaction: Transaction data
            customer_email: Customer email address

        Returns:
            str: Email HTML content
        """
        # Use the same HTML receipt but with email-specific wrapper
        receipt_html = ReceiptService.generate_html_receipt(transaction)

        # Wrap in email template
        email_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body style="margin: 0; padding: 20px; font-family: Arial, sans-serif; background: #f5f5f5;">
            <div style="max-width: 600px; margin: 0 auto; background: white; padding: 20px;">
                <p>Dear Valued Customer,</p>
                <p>Thank you for your purchase at {ReceiptService.STORE_INFO['name']}. Please find your receipt below:</p>

                {receipt_html}

                <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 5px;">
                    <p style="margin: 0; font-size: 12px;">
                        <strong>Need help?</strong> Contact us at {ReceiptService.STORE_INFO['email']}
                        or call {ReceiptService.STORE_INFO['phone']}
                    </p>
                </div>

                <p style="font-size: 11px; color: #666; margin-top: 20px;">
                    This is an automated email. Please do not reply to this message.
                </p>
            </div>
        </body>
        </html>
        """

        return email_html

    @staticmethod
    def get_receipt_formats(transaction: Dict) -> Dict[str, str]:
        """
        Get all receipt formats at once.

        Args:
            transaction: Transaction data from POSService.get_transaction()

        Returns:
            dict: {
                'thermal_58mm': str,
                'thermal_80mm': str,
                'html': str
            }
        """
        return {
            'thermal_58mm': ReceiptService.generate_thermal_receipt(transaction, width=32),
            'thermal_80mm': ReceiptService.generate_thermal_receipt(transaction, width=48),
            'html': ReceiptService.generate_html_receipt(transaction)
        }
