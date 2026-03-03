"""Gmail IMAP Service for fetching emails directly."""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Any, Optional
from datetime import datetime
import os
import hashlib

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()


class GmailIMAPService:
    """Service for fetching emails via IMAP."""
    
    def __init__(self):
        self.imap = None
        self.email_address = None
        self.is_connected = False
    
    def connect(self, email_address: str, password: str) -> Dict[str, Any]:
        """Connect to Gmail via IMAP."""
        try:
            # Connect to Gmail IMAP server
            self.imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
            
            # Login
            self.imap.login(email_address, password)
            
            self.email_address = email_address
            self.is_connected = True
            
            logger.info(f"Successfully connected to Gmail IMAP for {email_address}")
            
            return {
                "success": True,
                "message": f"Connected to {email_address}",
                "email": email_address
            }
            
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP authentication failed: {str(e)}")
            return {
                "success": False,
                "message": "Authentication failed. Please check your email and password. For Gmail, you need to use an App Password.",
                "error": str(e)
            }
        except Exception as e:
            logger.error(f"IMAP connection failed: {str(e)}")
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
                "error": str(e)
            }
    
    def disconnect(self):
        """Disconnect from IMAP server."""
        try:
            if self.imap:
                self.imap.logout()
            self.is_connected = False
            self.email_address = None
            logger.info("Disconnected from Gmail IMAP")
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
    
    def get_messages(self, folder: str = "INBOX", limit: int = 50, 
                     has_attachments: bool = True) -> List[Dict[str, Any]]:
        """Fetch messages from Gmail."""
        if not self.is_connected:
            raise Exception("Not connected to IMAP server")
        
        try:
            # Select mailbox
            self.imap.select(folder)
            
            # Search for emails
            if has_attachments:
                # Search for emails with attachments
                status, messages = self.imap.search(None, '(OR HEADER Content-Type "application/" HEADER Content-Type "image/")')
            else:
                status, messages = self.imap.search(None, 'ALL')
            
            if status != 'OK':
                return []
            
            # Get message IDs
            message_ids = messages[0].split()
            
            # Get latest messages up to limit
            message_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
            message_ids.reverse()  # Most recent first
            
            email_list = []
            
            for msg_id in message_ids:
                try:
                    # Fetch email data
                    status, msg_data = self.imap.fetch(msg_id, '(RFC822)')
                    
                    if status != 'OK':
                        continue
                    
                    # Parse email
                    raw_email = msg_data[0][1]
                    email_message = email.message_from_bytes(raw_email)
                    
                    # Extract basic info
                    subject = self._decode_header(email_message.get('Subject', ''))
                    from_email = email_message.get('From', '')
                    date_str = email_message.get('Date', '')
                    
                    # Parse date
                    try:
                        email_date = email.utils.parsedate_to_datetime(date_str)
                    except:
                        email_date = datetime.now()
                    
                    # Check for attachments
                    attachments = []
                    for part in email_message.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            if filename:
                                attachments.append({
                                    'filename': self._decode_header(filename),
                                    'content_type': part.get_content_type(),
                                    'size': len(part.get_payload(decode=True) or b'')
                                })
                    
                    # Only include if we're looking for attachments and it has them, or not filtering
                    if not has_attachments or attachments:
                        email_list.append({
                            'id': msg_id.decode(),
                            'subject': subject,
                            'from': from_email,
                            'date': email_date.isoformat(),
                            'attachments': attachments,
                            'has_attachments': len(attachments) > 0
                        })
                
                except Exception as e:
                    logger.error(f"Error parsing email {msg_id}: {str(e)}")
                    continue
            
            return email_list
            
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            raise
    
    def download_attachment(self, message_id: str, attachment_filename: str, 
                           save_dir: str) -> Optional[str]:
        """Download a specific attachment from an email."""
        if not self.is_connected:
            raise Exception("Not connected to IMAP server")
        
        try:
            # Fetch email
            status, msg_data = self.imap.fetch(message_id.encode(), '(RFC822)')
            
            if status != 'OK':
                return None
            
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Find and save attachment
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = self._decode_header(part.get_filename())
                    
                    if filename == attachment_filename:
                        # Create directory if not exists
                        os.makedirs(save_dir, exist_ok=True)
                        
                        # Generate unique filename
                        file_hash = hashlib.md5(message_id.encode()).hexdigest()[:8]
                        save_filename = f"{file_hash}_{filename}"
                        save_path = os.path.join(save_dir, save_filename)
                        
                        # Save attachment
                        with open(save_path, 'wb') as f:
                            f.write(part.get_payload(decode=True))
                        
                        logger.info(f"Downloaded attachment: {save_path}")
                        return save_path
            
            return None
            
        except Exception as e:
            logger.error(f"Error downloading attachment: {str(e)}")
            return None
    
    def _decode_header(self, header: str) -> str:
        """Decode email header."""
        if not header:
            return ""
        
        decoded_parts = decode_header(header)
        decoded_string = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                try:
                    decoded_string += part.decode(encoding or 'utf-8', errors='ignore')
                except:
                    decoded_string += part.decode('utf-8', errors='ignore')
            else:
                decoded_string += part
        
        return decoded_string


# Global instance
gmail_imap_service = GmailIMAPService()
