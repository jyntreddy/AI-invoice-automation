import os
import base64
from typing import List, Dict, Any, Optional
from datetime import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger()


class GmailService:
    """Service for interacting with Gmail API."""
    
    def __init__(self):
        self.creds = None
        self.service = None
        
    def authenticate(self, token_file: Optional[str] = None) -> bool:
        """Authenticate with Gmail API using OAuth2."""
        token_path = token_file or settings.GMAIL_TOKEN_FILE
        
        try:
            # Load credentials from token file if exists
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If no valid credentials, let user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        settings.GMAIL_CREDENTIALS_FILE,
                        settings.GMAIL_SCOPES
                    )
                    self.creds = flow.run_local_server(port=0)
                
                # Save credentials for future use
                with open(token_path, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=self.creds)
            logger.info("Gmail authentication successful")
            return True
            
        except Exception as e:
            logger.error(f"Gmail authentication failed: {str(e)}")
            return False
    
    def get_messages(
        self,
        query: str = "",
        max_results: int = 100,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get messages from Gmail."""
        if not self.service:
            raise Exception("Gmail service not authenticated")
        
        try:
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results,
                labelIds=label_ids or []
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Retrieved {len(messages)} messages from Gmail")
            return messages
            
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {str(e)}")
            return []
    
    def get_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a message."""
        if not self.service:
            raise Exception("Gmail service not authenticated")
        
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            return self._parse_message(message)
            
        except Exception as e:
            logger.error(f"Failed to get message details: {str(e)}")
            return None
    
    def _parse_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Gmail message to extract useful information."""
        headers = message['payload'].get('headers', [])
        
        parsed = {
            'id': message['id'],
            'thread_id': message.get('threadId'),
            'label_ids': message.get('labelIds', []),
            'snippet': message.get('snippet', ''),
            'internal_date': message.get('internalDate'),
            'from': self._get_header(headers, 'From'),
            'to': self._get_header(headers, 'To'),
            'subject': self._get_header(headers, 'Subject'),
            'date': self._get_header(headers, 'Date'),
            'attachments': []
        }
        
        # Extract attachments
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part.get('filename') and part['body'].get('attachmentId'):
                    parsed['attachments'].append({
                        'filename': part['filename'],
                        'mime_type': part.get('mimeType'),
                        'attachment_id': part['body']['attachmentId'],
                        'size': part['body'].get('size', 0)
                    })
        
        return parsed
    
    def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
        filename: str,
        output_dir: str
    ) -> Optional[str]:
        """Download attachment from Gmail message."""
        if not self.service:
            raise Exception("Gmail service not authenticated")
        
        try:
            attachment = self.service.users().messages().attachments().get(
                userId='me',
                messageId=message_id,
                id=attachment_id
            ).execute()
            
            file_data = base64.urlsafe_b64decode(attachment['data'])
            
            # Save to file
            os.makedirs(output_dir, exist_ok=True)
            file_path = os.path.join(output_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Downloaded attachment: {filename}")
            return file_path
            
        except Exception as e:
            logger.error(f"Failed to download attachment: {str(e)}")
            return None
    
    def get_messages_with_attachments(
        self,
        query: str = "has:attachment",
        after_date: Optional[datetime] = None,
        file_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get messages with specific attachment types."""
        # Build query
        if after_date:
            date_str = after_date.strftime("%Y/%m/%d")
            query += f" after:{date_str}"
        
        if file_types:
            file_query = " OR ".join([f"filename:{ext}" for ext in file_types])
            query += f" ({file_query})"
        
        messages = self.get_messages(query=query)
        detailed_messages = []
        
        for msg in messages:
            details = self.get_message_details(msg['id'])
            if details and details['attachments']:
                detailed_messages.append(details)
        
        return detailed_messages
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark a message as read."""
        if not self.service:
            raise Exception("Gmail service not authenticated")
        
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to mark message as read: {str(e)}")
            return False
    
    @staticmethod
    def _get_header(headers: List[Dict[str, str]], name: str) -> Optional[str]:
        """Get header value by name."""
        for header in headers:
            if header['name'].lower() == name.lower():
                return header['value']
        return None


# Singleton instance
gmail_service = GmailService()
