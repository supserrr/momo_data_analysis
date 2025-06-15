import re
from datetime import datetime
from lxml import etree
import os

class SMSParser:
    def __init__(self):
        self.categories = {
            'incoming_money': [
                r'You have received.*RWF from',
                r'received.*RWF.*from',
                r'incoming.*payment.*from'
            ],
            'payment_to_code': [
                r'Your payment of.*RWF to.*\d{5} has been completed',
                r'payment.*completed.*code.*\d{5}',
                r'sent.*RWF.*to.*\d{5}'
            ],
            'transfer_to_number': [
                r'transferred to.*\(250\d+\)',
                r'sent.*RWF.*to.*\(\d+\)',
                r'transfer.*completed.*to.*\d+'
            ],
            'bank_deposit': [
                r'bank deposit of.*RWF has been added',
                r'deposit.*bank.*RWF',
                r'bank.*transaction.*deposit'
            ],
            'airtime_payment': [
                r'Your payment of.*RWF to Airtime',
                r'airtime.*purchase.*RWF',
                r'payment.*airtime.*completed'
            ],
            'cash_power': [
                r'Your payment of.*RWF to.*Cash Power',
                r'cash power.*purchase.*RWF',
                r'electricity.*payment.*RWF'
            ],
            'third_party_initiated': [
                r'initiated by third party',
                r'third party.*transaction',
                r'external.*initiated'
            ],
            'withdrawal_from_agent': [
                r'withdrawn.*RWF.*via agent',
                r'cash.*withdrawal.*agent',
                r'agent.*withdrawal.*RWF'
            ],
            'bank_transfer': [
                r'Bank Transfer.*completed',
                r'transfer.*bank.*completed',
                r'bank.*transaction.*transfer'
            ],
            'internet_voice_bundle': [
                r'Internet.*Voice Bundle.*purchased',
                r'bundle.*internet.*voice',
                r'data.*bundle.*purchased'
            ],
            'fees_and_charges': [
                r'fee.*charged',
                r'service.*charge',
                r'transaction.*fee'
            ],
            'balance_inquiry': [
                r'balance.*inquiry',
                r'check.*balance',
                r'account.*balance'
            ]
        }
    
    def categorize_transaction(self, body):
        """Categorize transaction based on message content"""
        body_lower = body.lower()
        
        for category, patterns in self.categories.items():
            for pattern in patterns:
                if re.search(pattern, body, re.IGNORECASE):
                    return category
        return 'other'
    
    def extract_amount(self, body):
        """Extract transaction amount from message"""
        patterns = [
            r'(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',  # Standard format
            r'of\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',  # "of X RWF"
            r'received\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',  # "received X RWF"
            r'sent\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',  # "sent X RWF"
            r'withdrawn\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',  # "withdrawn X RWF"
            r'deposited\s+(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF'  # "deposited X RWF"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return 0.0
    
    def extract_fee(self, body):
        """Extract transaction fee from message"""
        fee_patterns = [
            r'Fee\s*(?:was|:)?\s*(\d+(?:\.\d+)?)\s*RWF',
            r'fee\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*RWF',
            r'charge\s*(?:of)?\s*(\d+(?:\.\d+)?)\s*RWF'
        ]
        
        for pattern in fee_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue
        return 0.0
    
    def extract_balance(self, body):
        """Extract balance from message"""
        patterns = [
            r'balance[:\s]+(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',
            r'NEW BALANCE\s*:?\s*(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',
            r'current.*balance.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF',
            r'remaining.*balance.*?(\d+(?:,\d+)*(?:\.\d+)?)\s*RWF'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                balance_str = match.group(1).replace(',', '')
                try:
                    return float(balance_str)
                except ValueError:
                    continue
        return None
    
    def extract_transaction_id(self, body):
        """Extract transaction ID from message"""
        patterns = [
            r'TxId:\s*(\w+)',
            r'Transaction Id:\s*(\w+)',
            r'Financial Transaction Id:\s*(\w+)',
            r'Ref:\s*(\w+)',
            r'Reference:\s*(\w+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def extract_recipient_info(self, body):
        """Extract recipient name and number"""
        recipient_patterns = [
            # For payments to code holders
            (r'to\s+([A-Za-z\s]+)\s+(\d{5})', 'code'),
            # For transfers to phone numbers
            (r'to\s+([A-Za-z\s]+)\s*\((\d+)\)', 'phone'),
            # For incoming money
            (r'from\s+([A-Za-z\s]+)\s*\(\*+(\d+)\)', 'from'),
            # For agent transactions
            (r'agent\s+([A-Za-z\s]+)\s*\((\d+)\)', 'agent'),
            # Generic recipient patterns
            (r'recipient\s+([A-Za-z\s]+)\s*\((\d+)\)', 'recipient')
        ]
        
        for pattern, transaction_type in recipient_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                number = match.group(2)
                return name, number
        
        return None, None
    
    def extract_sender_info(self, body):
        """Extract sender information for incoming transactions"""
        sender_patterns = [
            r'from\s+([A-Za-z\s]+)\s*\(\*+(\d+)\)',
            r'sender\s+([A-Za-z\s]+)\s*\((\d+)\)',
            r'initiated by\s+([A-Za-z\s]+)\s*\((\d+)\)'
        ]
        
        for pattern in sender_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                number = match.group(2)
                return name, number
        
        return None, None
    
    def extract_message_content(self, body):
        """Extract message/memo content if present"""
        message_patterns = [
            r'message[:\s]+"([^"]+)"',
            r'memo[:\s]+"([^"]+)"',
            r'note[:\s]+"([^"]+)"'
        ]
        
        for pattern in message_patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def parse_xml_file(self, file_path):
        """Parse the XML file and extract SMS data"""
        transactions = []
        
        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"XML file not found: {file_path}")
            
            # Parse XML
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            # Get total SMS count
            sms_count = int(root.get('count', 0))
            print(f"Processing {sms_count} SMS messages...")
            
            # Find all SMS elements
            sms_elements = root.xpath('//sms')
            
            processed_count = 0
            momo_count = 0
            
            for sms in sms_elements:
                processed_count += 1
                
                # Only process M-Money messages
                address = sms.get('address', '')
                if address.lower() not in ['m-money', 'mtn mobile money', 'momo']:
                    continue
                
                momo_count += 1
                body = sms.get('body', '')
                date_ms = int(sms.get('date', 0))
                
                # Convert timestamp (milliseconds) to datetime
                try:
                    date = datetime.fromtimestamp(date_ms / 1000)
                except (ValueError, OSError):
                    # Handle invalid timestamps
                    date = datetime.now()
                
                # Extract transaction data
                transaction = {
                    'body': body,
                    'date': date,
                    'category': self.categorize_transaction(body),
                    'amount': self.extract_amount(body),
                    'fee': self.extract_fee(body),
                    'balance': self.extract_balance(body),
                    'transaction_id': self.extract_transaction_id(body)
                }
                
                # Extract recipient/sender information
                recipient_name, recipient_number = self.extract_recipient_info(body)
                sender_name, sender_number = self.extract_sender_info(body)
                
                transaction['recipient_name'] = recipient_name
                transaction['recipient_number'] = recipient_number
                transaction['sender_name'] = sender_name
                transaction['sender_number'] = sender_number
                
                # Extract message content
                transaction['message'] = self.extract_message_content(body)
                
                # Store raw body for debugging
                transaction['raw_body'] = body
                
                transactions.append(transaction)
                
                # Progress update for large files
                if processed_count % 100 == 0:
                    print(f"Processed {processed_count}/{sms_count} messages, found {momo_count} MoMo transactions...")
            
            print(f"Parsing complete! Found {momo_count} MoMo transactions out of {processed_count} total SMS messages.")
            
            return transactions, sms_count
            
        except etree.XMLSyntaxError as e:
            print(f"XML parsing error: {e}")
            raise ValueError(f"Invalid XML file format: {e}")
        except Exception as e:
            print(f"Error parsing XML: {e}")
            raise
    
    def validate_xml_structure(self, file_path):
        """Validate XML file structure before processing"""
        try:
            tree = etree.parse(file_path)
            root = tree.getroot()
            
            # Check if it's an SMS backup format
            if root.tag != 'smses':
                return False, "Not a valid SMS backup XML file"
            
            # Check for required attributes
            if 'count' not in root.attrib:
                return False, "Missing count attribute in root element"
            
            # Check for SMS elements
            sms_elements = root.xpath('//sms')
            if not sms_elements:
                return False, "No SMS messages found in file"
            
            # Check SMS element structure
            sample_sms = sms_elements[0]
            required_attrs = ['address', 'date', 'body']
            missing_attrs = [attr for attr in required_attrs if attr not in sample_sms.attrib]
            
            if missing_attrs:
                return False, f"SMS elements missing required attributes: {missing_attrs}"
            
            return True, "Valid SMS backup XML file"
            
        except Exception as e:
            return False, f"XML validation error: {e}"