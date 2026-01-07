"""
M-Pesa Daraja API Integration Service
Handles STK Push (Lipa Na M-Pesa Online) payment initiation.

Based on Safaricom Daraja API v1
Sandbox endpoint: https://sandbox.safaricom.co.ke
"""

import os
import base64
import requests
from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class MPesaService:
    """M-Pesa Daraja API integration for STK Push payments"""

    # Sandbox configuration
    SANDBOX_URL = "https://sandbox.safaricom.co.ke"
    PRODUCTION_URL = "https://api.safaricom.co.ke"

    def __init__(self):
        """Initialize M-Pesa service with credentials from environment"""
        self.consumer_key = os.getenv('MPESA_CONSUMER_KEY', '')
        self.consumer_secret = os.getenv('MPESA_CONSUMER_SECRET', '')
        self.business_shortcode = os.getenv('MPESA_SHORTCODE', '174379')  # Sandbox default
        self.passkey = os.getenv('MPESA_PASSKEY', 'bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919')  # Sandbox default
        self.callback_url = os.getenv('MPESA_CALLBACK_URL', 'https://yourdomain.com/api/payments/mpesa/callback')

        # Use sandbox by default in development
        self.is_production = os.getenv('FLASK_ENV', 'development') == 'production'
        self.base_url = self.PRODUCTION_URL if self.is_production else self.SANDBOX_URL

        # Access token cache
        self._access_token = None
        self._token_expires_at = None

    def get_access_token(self) -> str:
        """
        Generate OAuth access token for API authentication.

        Token is cached and reused until expiration.

        Returns:
            str: Access token

        Raises:
            RuntimeError: If token generation fails
        """
        # Return cached token if still valid
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token

        # Generate new token
        auth_url = f"{self.base_url}/oauth/v1/generate?grant_type=client_credentials"

        try:
            response = requests.get(
                auth_url,
                auth=(self.consumer_key, self.consumer_secret),
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            self._access_token = data.get('access_token')

            # Cache token (expires in ~1 hour typically)
            expires_in = int(data.get('expires_in', 3600))
            from datetime import timedelta
            self._token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)  # Refresh 1 min early

            logger.info("M-Pesa access token generated successfully")
            return self._access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get M-Pesa access token: {e}")
            raise RuntimeError(f"M-Pesa authentication failed: {str(e)}")

    def generate_password(self, timestamp: str) -> str:
        """
        Generate Base64 encoded password for STK Push request.

        Formula: Base64(Shortcode + Passkey + Timestamp)

        Args:
            timestamp: Timestamp in format YYYYMMDDHHmmss

        Returns:
            str: Base64 encoded password
        """
        data_to_encode = f"{self.business_shortcode}{self.passkey}{timestamp}"
        encoded_password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
        return encoded_password

    def initiate_stk_push(
        self,
        phone_number: str,
        amount: float,
        account_reference: str,
        transaction_desc: str = "Payment"
    ) -> Dict:
        """
        Initiate STK Push payment request to customer's phone.

        Args:
            phone_number: Customer phone number (format: 254XXXXXXXXX)
            amount: Amount to charge (minimum 1 KES)
            account_reference: Order ID or reference (max 12 chars)
            transaction_desc: Description shown to customer (max 13 chars)

        Returns:
            dict: {
                'success': bool,
                'CheckoutRequestID': str (if successful),
                'MerchantRequestID': str (if successful),
                'ResponseCode': str,
                'ResponseDescription': str,
                'CustomerMessage': str,
                'error': str (if failed)
            }

        Raises:
            ValueError: If input validation fails
            RuntimeError: If API request fails
        """
        # Validate inputs
        if not phone_number or not phone_number.startswith('254'):
            raise ValueError("Phone number must start with 254 (Kenyan format)")

        if len(phone_number) != 12:
            raise ValueError("Phone number must be 12 digits (254XXXXXXXXX)")

        if amount < 1:
            raise ValueError("Amount must be at least 1 KES")

        if len(account_reference) > 12:
            account_reference = account_reference[:12]

        if len(transaction_desc) > 13:
            transaction_desc = transaction_desc[:13]

        # Generate timestamp
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)

        # Get access token
        try:
            access_token = self.get_access_token()
        except RuntimeError as e:
            return {
                'success': False,
                'error': f"Authentication failed: {str(e)}"
            }

        # Prepare STK Push request
        stk_push_url = f"{self.base_url}/mpesa/stkpush/v1/processrequest"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'BusinessShortCode': self.business_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),  # Must be integer
            'PartyA': phone_number,  # Customer phone number
            'PartyB': self.business_shortcode,  # Business shortcode
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference,
            'TransactionDesc': transaction_desc
        }

        try:
            logger.info(f"Initiating STK Push for {phone_number}, amount: {amount}")

            response = requests.post(
                stk_push_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            data = response.json()

            # Check response
            if response.status_code == 200 and data.get('ResponseCode') == '0':
                logger.info(f"STK Push successful: {data.get('CheckoutRequestID')}")
                return {
                    'success': True,
                    'CheckoutRequestID': data.get('CheckoutRequestID'),
                    'MerchantRequestID': data.get('MerchantRequestID'),
                    'ResponseCode': data.get('ResponseCode'),
                    'ResponseDescription': data.get('ResponseDescription'),
                    'CustomerMessage': data.get('CustomerMessage', 'Payment request sent')
                }
            else:
                error_msg = data.get('errorMessage') or data.get('ResponseDescription') or 'Unknown error'
                logger.error(f"STK Push failed: {error_msg}")
                return {
                    'success': False,
                    'ResponseCode': data.get('ResponseCode'),
                    'ResponseDescription': data.get('ResponseDescription'),
                    'error': error_msg
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"STK Push request failed: {e}")
            return {
                'success': False,
                'error': f"Request failed: {str(e)}"
            }

    def query_stk_status(self, checkout_request_id: str) -> Dict:
        """
        Query the status of an STK Push transaction.

        Args:
            checkout_request_id: CheckoutRequestID from initiate_stk_push

        Returns:
            dict: Transaction status information
        """
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = self.generate_password(timestamp)

        try:
            access_token = self.get_access_token()
        except RuntimeError as e:
            return {
                'success': False,
                'error': f"Authentication failed: {str(e)}"
            }

        query_url = f"{self.base_url}/mpesa/stkpushquery/v1/query"

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'BusinessShortCode': self.business_shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }

        try:
            response = requests.post(
                query_url,
                json=payload,
                headers=headers,
                timeout=30
            )

            data = response.json()

            if response.status_code == 200:
                return {
                    'success': True,
                    'ResultCode': data.get('ResultCode'),
                    'ResultDesc': data.get('ResultDesc'),
                    'data': data
                }
            else:
                return {
                    'success': False,
                    'error': data.get('errorMessage', 'Query failed')
                }

        except requests.exceptions.RequestException as e:
            logger.error(f"STK status query failed: {e}")
            return {
                'success': False,
                'error': f"Query failed: {str(e)}"
            }
