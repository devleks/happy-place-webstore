"""
Email Service - SMTP-based email sending
Supports custom SMTP servers and email templates
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import List, Optional, Dict
from datetime import datetime
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """
    SMTP-based email service for transactional emails

    Supports:
    - Order confirmations
    - Shipping notifications
    - Delivery updates
    - Password resets
    - Account notifications
    """

    def __init__(self):
        """Initialize email service with SMTP configuration"""
        self.smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.smtp_use_tls = os.getenv('SMTP_USE_TLS', 'true').lower() == 'true'
        self.smtp_use_ssl = os.getenv('SMTP_USE_SSL', 'false').lower() == 'true'

        # Email settings
        self.from_email = os.getenv('EMAIL_FROM', 'noreply@happyplace.com')
        self.from_name = os.getenv('EMAIL_FROM_NAME', 'Happy Place Boutique')
        self.reply_to = os.getenv('EMAIL_REPLY_TO', 'support@happyplace.com')

        # Feature flags
        self.email_enabled = os.getenv('EMAIL_ENABLED', 'true').lower() == 'true'

        # Store info
        self.store_name = "Happy Place Boutique"
        self.store_address = "Nairobi, Kenya"
        self.store_phone = "+254 700 000 000"
        self.store_email = "info@happyplace.com"
        self.store_website = os.getenv('WEBSITE_URL', 'https://happyplace.com')

    def _create_smtp_connection(self):
        """Create and return authenticated SMTP connection"""
        try:
            if self.smtp_use_ssl:
                # Use SSL (port 465)
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port, timeout=60)
            else:
                # Use regular SMTP with longer timeout
                server = smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=60)

                # Set debug level for troubleshooting
                # server.set_debuglevel(1)  # Uncomment to see SMTP conversation

                if self.smtp_use_tls:
                    # Start TLS (port 587)
                    server.starttls()

            # Login if credentials provided
            if self.smtp_username and self.smtp_password:
                server.login(self.smtp_username, self.smtp_password)

            return server
        except Exception as e:
            logger.error(f"SMTP connection failed: {str(e)}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Dict]] = None
    ) -> Dict:
        """
        Send email via SMTP

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_body: HTML email body
            text_body: Plain text fallback (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)
            attachments: List of attachment dicts (optional)

        Returns:
            Dict with success status and message
        """
        if not self.email_enabled:
            logger.info(f"Email disabled - Would send to {to_email}: {subject}")
            return {'success': True, 'message': 'Email disabled (test mode)'}

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Reply-To'] = self.reply_to

            if cc:
                msg['Cc'] = ', '.join(cc)

            # Add text and HTML parts
            if text_body:
                part1 = MIMEText(text_body, 'plain')
                msg.attach(part1)

            part2 = MIMEText(html_body, 'html')
            msg.attach(part2)

            # Add attachments if any
            if attachments:
                for attachment in attachments:
                    # Handle different attachment types
                    pass  # TODO: Implement attachment handling

            # Send email
            server = self._create_smtp_connection()

            recipients = [to_email]
            if cc:
                recipients.extend(cc)
            if bcc:
                recipients.extend(bcc)

            server.sendmail(self.from_email, recipients, msg.as_string())
            server.quit()

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return {'success': True, 'message': 'Email sent successfully'}

        except Exception as e:
            error_msg = f"Failed to send email to {to_email}: {str(e)}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}

    def send_order_confirmation(self, order_data: Dict) -> Dict:
        """
        Send order confirmation email

        Args:
            order_data: Dict containing order details
                - order_id, order_number, customer_name, customer_email
                - order_total, items, payment_method, shipping_address

        Returns:
            Dict with success status
        """
        try:
            # Load template
            template_html = self._get_order_confirmation_template()

            # Render template with order data
            template = Template(template_html)
            html_body = template.render(
                customer_name=order_data.get('customer_name', 'Valued Customer'),
                order_number=order_data.get('order_number', ''),
                order_id=order_data.get('order_id', ''),
                order_date=order_data.get('order_date', datetime.now().strftime('%B %d, %Y')),
                order_total=order_data.get('order_total', '0.00'),
                items=order_data.get('items', []),
                payment_method=order_data.get('payment_method', 'N/A'),
                shipping_address=order_data.get('shipping_address', {}),
                store_name=self.store_name,
                store_website=self.store_website,
                store_email=self.store_email,
                store_phone=self.store_phone
            )

            # Send email
            result = self.send_email(
                to_email=order_data.get('customer_email'),
                subject=f"Order Confirmation #{order_data.get('order_number')} - {self.store_name}",
                html_body=html_body
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send order confirmation: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_shipping_notification(self, order_data: Dict) -> Dict:
        """
        Send shipping notification email

        Args:
            order_data: Dict containing order and shipping details
                - tracking_number, carrier, estimated_delivery

        Returns:
            Dict with success status
        """
        try:
            template_html = self._get_shipping_notification_template()

            template = Template(template_html)
            html_body = template.render(
                customer_name=order_data.get('customer_name', 'Valued Customer'),
                order_number=order_data.get('order_number', ''),
                tracking_number=order_data.get('tracking_number', 'N/A'),
                carrier=order_data.get('carrier', 'Standard Delivery'),
                estimated_delivery=order_data.get('estimated_delivery', 'N/A'),
                tracking_url=order_data.get('tracking_url', '#'),
                store_name=self.store_name,
                store_website=self.store_website
            )

            result = self.send_email(
                to_email=order_data.get('customer_email'),
                subject=f"Your Order #{order_data.get('order_number')} Has Shipped! 📦",
                html_body=html_body
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send shipping notification: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_delivery_confirmation(self, order_data: Dict) -> Dict:
        """
        Send delivery confirmation email

        Args:
            order_data: Dict containing delivery details

        Returns:
            Dict with success status
        """
        try:
            template_html = self._get_delivery_confirmation_template()

            template = Template(template_html)
            html_body = template.render(
                customer_name=order_data.get('customer_name', 'Valued Customer'),
                order_number=order_data.get('order_number', ''),
                delivery_date=order_data.get('delivery_date', datetime.now().strftime('%B %d, %Y')),
                review_url=f"{self.store_website}/orders/{order_data.get('order_id')}/review",
                store_name=self.store_name,
                store_website=self.store_website
            )

            result = self.send_email(
                to_email=order_data.get('customer_email'),
                subject=f"Your Order #{order_data.get('order_number')} Has Been Delivered! 🎉",
                html_body=html_body
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send delivery confirmation: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_password_reset(self, email: str, reset_token: str) -> Dict:
        """
        Send password reset email

        Args:
            email: User email address
            reset_token: Password reset token

        Returns:
            Dict with success status
        """
        try:
            reset_url = f"{self.store_website}/reset-password?token={reset_token}"

            template_html = self._get_password_reset_template()

            template = Template(template_html)
            html_body = template.render(
                reset_url=reset_url,
                store_name=self.store_name,
                store_website=self.store_website
            )

            result = self.send_email(
                to_email=email,
                subject=f"Password Reset Request - {self.store_name}",
                html_body=html_body
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send password reset: {str(e)}")
            return {'success': False, 'error': str(e)}

    def send_verification_email(self, email: str, customer_name: str, verification_token: str) -> Dict:
        """
        Send account verification email

        Args:
            email: User email address
            customer_name: Customer's name
            verification_token: Email verification token

        Returns:
            Dict with success status
        """
        try:
            verification_url = f"{self.store_website}/verify-email?token={verification_token}"

            template_html = self._get_verification_email_template()

            template = Template(template_html)
            html_body = template.render(
                customer_name=customer_name,
                verification_url=verification_url,
                store_name=self.store_name,
                store_website=self.store_website
            )

            result = self.send_email(
                to_email=email,
                subject=f"Verify Your Email - {self.store_name}",
                html_body=html_body
            )

            return result

        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return {'success': False, 'error': str(e)}

    # ============================================
    # Email Templates
    # ============================================

    def _get_order_confirmation_template(self) -> str:
        """Get order confirmation email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Confirmation</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .order-details { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; }
        .item { border-bottom: 1px solid #eee; padding: 15px 0; }
        .item:last-child { border-bottom: none; }
        .total { font-size: 1.2em; font-weight: bold; color: #8e44ad; margin-top: 20px; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
        .button { display: inline-block; background: #8e44ad; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Order Confirmed! 🎉</h1>
            <p>Thank you for your purchase</p>
        </div>

        <div class="content">
            <p>Hi {{ customer_name }},</p>

            <p>We've received your order and are getting it ready. You'll receive a shipping confirmation email with tracking information once your order ships.</p>

            <div class="order-details">
                <h2>Order #{{ order_number }}</h2>
                <p><strong>Order Date:</strong> {{ order_date }}</p>
                <p><strong>Payment Method:</strong> {{ payment_method }}</p>

                <h3>Order Items:</h3>
                {% for item in items %}
                <div class="item">
                    <strong>{{ item.product_name }}</strong>
                    {% if item.variant_name %}<br><small>{{ item.variant_name }}</small>{% endif %}
                    <br>Quantity: {{ item.quantity }} × KES {{ item.price }}
                    <br><strong>KES {{ item.subtotal }}</strong>
                </div>
                {% endfor %}

                <div class="total">
                    Total: KES {{ order_total }}
                </div>
            </div>

            {% if shipping_address %}
            <div class="order-details">
                <h3>Shipping Address:</h3>
                <p>
                    {{ shipping_address.street }}<br>
                    {{ shipping_address.city }}, {{ shipping_address.postal_code }}<br>
                    {{ shipping_address.country }}
                </p>
            </div>
            {% endif %}

            <center>
                <a href="{{ store_website }}/orders/{{ order_id }}" class="button">View Order Details</a>
            </center>

            <p>If you have any questions, please contact us at {{ store_email }} or {{ store_phone }}.</p>

            <p>Thank you for shopping with us!</p>
        </div>

        <div class="footer">
            <p>{{ store_name }}<br>{{ store_website }}</p>
            <p><small>This is an automated email. Please do not reply to this message.</small></p>
        </div>
    </div>
</body>
</html>
        """

    def _get_shipping_notification_template(self) -> str:
        """Get shipping notification email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Shipped</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .tracking-box { background: white; padding: 20px; margin: 20px 0; border-radius: 5px; border-left: 4px solid #3498db; }
        .button { display: inline-block; background: #3498db; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Your Order Has Shipped! 📦</h1>
        </div>

        <div class="content">
            <p>Hi {{ customer_name }},</p>

            <p>Great news! Your order #{{ order_number }} is on its way!</p>

            <div class="tracking-box">
                <h3>Tracking Information</h3>
                <p><strong>Carrier:</strong> {{ carrier }}</p>
                <p><strong>Tracking Number:</strong> {{ tracking_number }}</p>
                <p><strong>Estimated Delivery:</strong> {{ estimated_delivery }}</p>
            </div>

            <center>
                <a href="{{ tracking_url }}" class="button">Track Your Package</a>
            </center>

            <p>You can track your shipment using the tracking number above. We'll notify you once your order is delivered.</p>

            <p>Thank you for shopping with {{ store_name }}!</p>
        </div>

        <div class="footer">
            <p>{{ store_name }}<br>{{ store_website }}</p>
        </div>
    </div>
</body>
</html>
        """

    def _get_delivery_confirmation_template(self) -> str:
        """Get delivery confirmation email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Order Delivered</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #27ae60 0%, #229954 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #27ae60; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Order Delivered! 🎉</h1>
        </div>

        <div class="content">
            <p>Hi {{ customer_name }},</p>

            <p>Your order #{{ order_number }} has been delivered on {{ delivery_date }}.</p>

            <p>We hope you love your purchase! If you have a moment, we'd appreciate it if you could share your feedback.</p>

            <center>
                <a href="{{ review_url }}" class="button">Write a Review</a>
            </center>

            <p>If you have any issues with your order, please don't hesitate to contact us.</p>

            <p>Thank you for choosing {{ store_name }}!</p>
        </div>

        <div class="footer">
            <p>{{ store_name }}<br>{{ store_website }}</p>
        </div>
    </div>
</body>
</html>
        """

    def _get_password_reset_template(self) -> str:
        """Get password reset email template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Password Reset</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #e74c3c; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .warning { background: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>

        <div class="content">
            <p>We received a request to reset your password for your {{ store_name }} account.</p>

            <center>
                <a href="{{ reset_url }}" class="button">Reset Password</a>
            </center>

            <div class="warning">
                <strong>⚠️ Security Notice:</strong><br>
                This link will expire in 1 hour. If you didn't request this password reset, please ignore this email.
            </div>

            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{{ reset_url }}</p>
        </div>

        <div class="footer">
            <p>{{ store_name }}<br>{{ store_website }}</p>
        </div>
    </div>
</body>
</html>
        """

    def _get_verification_email_template(self) -> str:
        """Get email verification template"""
        return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Verify Your Email</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #00b894 0%, #00a383 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #00b894; color: white; padding: 15px 40px; text-decoration: none; border-radius: 5px; margin: 20px 0; font-size: 1.1em; font-weight: bold; }
        .info-box { background: #e8f5f1; border-left: 4px solid #00b894; padding: 15px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 0.9em; }
        .icon { font-size: 3em; margin-bottom: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon">✉️</div>
            <h1>Welcome to {{ store_name }}!</h1>
            <p>Please verify your email address</p>
        </div>

        <div class="content">
            <p>Hi {{ customer_name }},</p>

            <p>Thank you for creating an account with {{ store_name }}! We're excited to have you join our community.</p>

            <p>To complete your registration and start shopping, please verify your email address by clicking the button below:</p>

            <center>
                <a href="{{ verification_url }}" class="button">Verify My Email</a>
            </center>

            <div class="info-box">
                <strong>📌 Why verify?</strong><br>
                Email verification helps us:
                <ul>
                    <li>Keep your account secure</li>
                    <li>Send you order confirmations and updates</li>
                    <li>Notify you about exclusive offers</li>
                </ul>
            </div>

            <p>If the button doesn't work, copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{{ verification_url }}</p>

            <p><strong>Note:</strong> This verification link will expire in 24 hours.</p>

            <p>If you didn't create an account with us, please ignore this email.</p>

            <p>Happy shopping!</p>
        </div>

        <div class="footer">
            <p>{{ store_name }}<br>{{ store_website }}</p>
            <p><small>This is an automated email. Please do not reply to this message.</small></p>
        </div>
    </div>
</body>
</html>
        """


# Singleton instance
email_service = EmailService()
