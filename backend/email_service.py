import smtplib
import os
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self):
        self.email_providers = [
            {
                'name': 'Gmail',
                'smtp_server': 'smtp.gmail.com',
                'port': 465,  # SSL port for Gmail
                'email': os.getenv('GMAIL_EMAIL'),
                'password': os.getenv('GMAIL_APP_PASSWORD'),
                'use_ssl': True
            },
            {
                'name': 'Gmail_TLS',
                'smtp_server': 'smtp.gmail.com', 
                'port': 587,  # TLS port for Gmail
                'email': os.getenv('GMAIL_EMAIL'),
                'password': os.getenv('GMAIL_APP_PASSWORD'),
                'use_ssl': False
            },
            {
                'name': 'Outlook',
                'smtp_server': 'smtp-mail.outlook.com',
                'port': 587,
                'email': os.getenv('OUTLOOK_EMAIL'),
                'password': os.getenv('OUTLOOK_PASSWORD'),
                'use_ssl': False
            }
        ]
        
        # Filter out providers with missing credentials
        self.email_providers = [
            provider for provider in self.email_providers 
            if provider['email'] and provider['password']
        ]
        
        if not self.email_providers:
            print("❌ No email providers configured!")
        else:
            for provider in self.email_providers:
                print(f"✅ Email provider ready: {provider['name']}")
    
    def get_name_from_email(self, email):
        """Extract name from email address"""
        local = email.split('@')[0]
        if '.' in local:
            parts = local.split('.')
            first = parts[0].replace('-', ' ').replace('_', ' ').title()
            last = parts[1].replace('-', ' ').replace('_', ' ').title() if len(parts) > 1 else ""
            return f"{first} {last}".strip()
        else:
            return local.replace('-', ' ').replace('_', ' ').title()
    
    def create_email_content(self, recipient_email, company_name, personalized_email_content):
        """Create email subject and use AI-generated body"""
        # Simple subject line
        subject = f"Quick question about opportunities at {company_name}"
        
        # Use the AI-generated content as the body
        body = personalized_email_content
        
        return subject, body
    
    def test_connection(self, provider):
        """Test SMTP connection for a provider"""
        try:
            print(f"🔧 Testing connection to {provider['name']}...")
            
            if provider.get('use_ssl', False):
                # Use SSL connection (port 465)
                server = smtplib.SMTP_SSL(provider['smtp_server'], provider['port'], timeout=10)
            else:
                # Use TLS connection (port 587)
                server = smtplib.SMTP(provider['smtp_server'], provider['port'], timeout=10)
                server.starttls()
            
            server.login(provider['email'], provider['password'])
            server.quit()
            print(f"✅ {provider['name']} connection successful")
            return True
        except Exception as e:
            print(f"❌ {provider['name']} connection failed: {str(e)}")
            return False
    
    def send_email(self, to_email, subject, body):
        """Send email with fallback providers"""
        if not self.email_providers:
            print("❌ No email providers available")
            return False
        
        # Try each provider
        for provider in self.email_providers:
            try:
                print(f"📧 Trying to send email via {provider['name']}...")
                print(f"   From: {provider['email']}")
                print(f"   To: {to_email}")
                print(f"   Subject: {subject}")
                
                # Create message
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = provider['email']
                msg['To'] = to_email
                
                # Create both plain text and HTML versions
                text_part = MIMEText(body, 'plain')
                html_body = body.replace('\n', '<br>')
                html_part = MIMEText(html_body, 'html')
                
                msg.attach(text_part)
                msg.attach(html_part)
                
                # Send email with detailed error logging and timeout
                print(f"   Connecting to {provider['smtp_server']}:{provider['port']}...")
                
                if provider.get('use_ssl', False):
                    # Use SSL connection (port 465)
                    server = smtplib.SMTP_SSL(provider['smtp_server'], provider['port'], timeout=10)
                else:
                    # Use TLS connection (port 587)
                    server = smtplib.SMTP(provider['smtp_server'], provider['port'], timeout=10)
                    print(f"   Starting TLS...")
                    server.starttls()
                
                print(f"   Logging in...")
                server.login(provider['email'], provider['password'])
                
                print(f"   Sending message...")
                server.send_message(msg)
                server.quit()
                
                print(f"✅ Email sent to {to_email} via {provider['name']}")
                return True
                
            except smtplib.SMTPAuthenticationError as e:
                print(f"❌ {provider['name']} authentication failed: {str(e)}")
                print(f"   Check if app password is correct for {provider['email']}")
            except smtplib.SMTPRecipientsRefused as e:
                print(f"❌ {provider['name']} recipient refused: {str(e)}")
            except smtplib.SMTPServerDisconnected as e:
                print(f"❌ {provider['name']} server disconnected: {str(e)}")
            except Exception as e:
                print(f"❌ {provider['name']} failed: {str(e)}")
            
            time.sleep(2)  # Brief delay before trying next provider
        
        print(f"❌ All email providers failed for {to_email}")
        return False
    
    def send_bulk_emails(self, email_list, company_name, personalized_email_content):
        """Send emails to multiple recipients"""
        results = {
            'sent': 0,
            'failed': 0,
            'total': len(email_list)
        }
        
        for email in email_list:
            try:
                subject, body = self.create_email_content(email, company_name, personalized_email_content)
                
                if self.send_email(email, subject, body):
                    results['sent'] += 1
                else:
                    results['failed'] += 1
                
                # Delay between emails to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error sending to {email}: {e}")
                results['failed'] += 1
        
        return results
