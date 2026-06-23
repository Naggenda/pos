import requests
import json
import hmac
import hashlib
from datetime import datetime
from config import EFRIS_CONFIG
from models import db, EfrisLog

class EfrisClient:
    """Client for EFRIS API integration"""
    
    def __init__(self):
        self.base_url = EFRIS_CONFIG['base_url']
        self.username = EFRIS_CONFIG['username']
        self.password = EFRIS_CONFIG['password']
        self.tin = EFRIS_CONFIG['tin']
        self.device_serial = EFRIS_CONFIG['device_serial']
        self.token = None
        
    def authenticate(self):
        """Authenticate with EFRIS API"""
        try:
            auth_data = {
                'username': self.username,
                'password': self.password,
            }
            
            response = requests.post(
                f'{self.base_url}/auth/token',
                json=auth_data,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                self.token = result.get('token')
                return True, 'Authentication successful'
            else:
                error_msg = response.json().get('message', 'Authentication failed')
                return False, error_msg
                
        except requests.exceptions.RequestException as e:
            return False, f'Connection error: {str(e)}'
        except Exception as e:
            return False, f'Error: {str(e)}'
    
    def get_headers(self):
        """Get request headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
            
        return headers
    
    def submit_sales_invoice(self, sale_data):
        """Submit a sales invoice to EFRIS"""
        try:
            if not self.token:
                success, msg = self.authenticate()
                if not success:
                    return False, msg, None
            
            # Format invoice data for EFRIS
            invoice_payload = self._format_invoice(sale_data)
            
            # Submit to EFRIS
            response = requests.post(
                f'{self.base_url}/invoices/submit',
                json=invoice_payload,
                headers=self.get_headers(),
                timeout=15
            )
            
            # Log the interaction
            self._log_interaction(
                sale_id=sale_data.get('sale_id'),
                endpoint='/invoices/submit',
                method='POST',
                request_data=invoice_payload,
                response_status=response.status_code,
                response_data=response.json() if response.text else None
            )
            
            if response.status_code in [200, 201]:
                result = response.json()
                receipt_code = result.get('receiptCode') or result.get('receipt_code')
                return True, 'Invoice submitted successfully', receipt_code
            else:
                error_msg = response.json().get('message', 'Failed to submit invoice')
                return False, error_msg, None
                
        except requests.exceptions.RequestException as e:
            error_msg = f'Connection error: {str(e)}'
            self._log_interaction(
                sale_id=sale_data.get('sale_id'),
                endpoint='/invoices/submit',
                method='POST',
                request_data=sale_data,
                response_status=500,
                error_message=error_msg
            )
            return False, error_msg, None
        except Exception as e:
            error_msg = f'Error: {str(e)}'
            return False, error_msg, None
    
    def _format_invoice(self, sale_data):
        """Format sale data into EFRIS invoice format"""
        items = []
        
        for item in sale_data.get('items', []):
            items.append({
                'itemCode': item.get('product_id'),
                'description': item.get('product_name'),
                'quantity': item['quantity'],
                'unitPrice': item['unit_price'],
                'taxRate': item.get('tax_rate', 0.18),
                'taxAmount': item.get('tax_amount', 0),
                'grossAmount': item['subtotal'],
            })
        
        invoice = {
            'invoiceNumber': sale_data.get('receipt_number'),
            'invoiceDate': datetime.now().isoformat(),
            'tin': self.tin,
            'deviceSerialNumber': self.device_serial,
            'currency': 'UGX',
            'lines': items,
            'totals': {
                'grossAmount': sale_data.get('total_amount', 0),
                'taxAmount': sale_data.get('tax_amount', 0),
                'netAmount': sale_data.get('net_amount', 0),
                'discountAmount': sale_data.get('discount_amount', 0),
            },
            'paymentMethod': sale_data.get('payment_method', 'CASH'),
            'remarks': 'POS Sale',
        }
        
        return invoice
    
    def get_invoice_status(self, receipt_code):
        """Get the status of a submitted invoice"""
        try:
            if not self.token:
                success, msg = self.authenticate()
                if not success:
                    return False, msg, None
            
            response = requests.get(
                f'{self.base_url}/invoices/{receipt_code}/status',
                headers=self.get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                status = result.get('status', 'UNKNOWN')
                return True, 'Status retrieved successfully', status
            else:
                error_msg = response.json().get('message', 'Failed to get invoice status')
                return False, error_msg, None
                
        except requests.exceptions.RequestException as e:
            return False, f'Connection error: {str(e)}', None
        except Exception as e:
            return False, f'Error: {str(e)}', None
    
    def _log_interaction(self, sale_id=None, endpoint='', method='', 
                        request_data=None, response_status=None, 
                        response_data=None, error_message=None):
        """Log EFRIS API interaction"""
        try:
            log = EfrisLog(
                sale_id=sale_id,
                endpoint=endpoint,
                method=method,
                request_data=request_data,
                response_status=response_status,
                response_data=response_data,
                error_message=error_message
            )
            db.session.add(log)
            db.session.commit()
        except Exception as e:
            print(f'Error logging EFRIS interaction: {str(e)}')


def submit_to_efris(sale):
    """Helper function to submit a sale to EFRIS"""
    client = EfrisClient()
    
    sale_data = {
        'sale_id': sale.id,
        'receipt_number': sale.receipt_number,
        'total_amount': sale.total_amount,
        'tax_amount': sale.tax_amount,
        'net_amount': sale.net_amount,
        'discount_amount': sale.discount_amount,
        'payment_method': sale.payment_method,
        'items': [item.to_dict() for item in sale.items],
    }
    
    success, message, receipt_code = client.submit_sales_invoice(sale_data)
    
    if success:
        sale.efris_status = 'SUBMITTED'
        sale.efris_receipt_code = receipt_code
    else:
        sale.efris_status = 'FAILED'
    
    db.session.commit()
    
    return success, message, receipt_code
