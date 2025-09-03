"""
AI-powered email filtering service to identify real people vs customer support/HR emails
"""
import os
import re
from typing import List, Dict
import google.generativeai as genai

class EmailFilter:
    def __init__(self):
        """Initialize AI email filter with Gemini API"""
        try:
            # Get API keys from environment
            api_key1 = os.getenv('GEMINI_API_KEY')
            api_key2 = os.getenv('GEMINI_API_KEY_2')
            
            if not api_key1 and not api_key2:
                raise Exception("No Gemini API keys found in environment")
            
            # Use first available key
            api_key = api_key1 if api_key1 else api_key2
            genai.configure(api_key=api_key)
            
            # Initialize model
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            print("✅ Email filter AI initialized")
            
        except Exception as e:
            print(f"❌ Email filter initialization failed: {e}")
            self.model = None
    
    def filter_emails(self, emails: List[str], company_domain: str) -> Dict:
        """
        Filter emails to identify real people vs support/HR/generic emails
        
        Args:
            emails: List of email addresses
            company_domain: The company domain being searched
            
        Returns:
            Dict with 'real_people', 'support_emails', and 'analysis'
        """
        if not self.model:
            print("❌ AI model not available, returning all emails")
            return {
                'real_people': emails,
                'support_emails': [],
                'analysis': 'AI filtering not available'
            }
        
        if not emails:
            return {
                'real_people': [],
                'support_emails': [],
                'analysis': 'No emails to filter'
            }
        
        print(f"🤖 AI filtering {len(emails)} emails for {company_domain}...")
        
        try:
            # Create prompt for AI analysis
            email_list = "\n".join([f"- {email}" for email in emails])
            
            prompt = f"""
Analyze these email addresses from {company_domain} and:
1. Categorize them into REAL PEOPLE vs SUPPORT/GENERIC emails
2. Extract the actual NAMES from the real people emails

REAL PEOPLE emails are:
- Personal names (john.smith@, sarah.johnson@, m.chen@)
- Individual employees who could be decision makers or potential leads
- People who might respond to business outreach

SUPPORT/GENERIC emails are:
- Customer service (support@, help@, info@, contact@)
- HR/recruiting (hr@, careers@, jobs@, recruiting@)
- General departments (sales@, marketing@, admin@)
- System/automated emails (noreply@, donotreply@, automated@)
- Generic roles (webmaster@, postmaster@, admin@)

For REAL PEOPLE emails, extract the likely full name from the email address:
- john.smith@company.com → "John Smith"  
- sarah.j@company.com → "Sarah J"
- m.chen@company.com → "M Chen"
- robert.johnson123@company.com → "Robert Johnson"
- daveburnisonms@company.com → "Dave Burnison"
- kunfei@company.com → "Kun Fei"
- abdullahyildiz@company.com → "Abdullah Yildiz"
- vanessaperson@company.com → "Vanessa Person"

IMPORTANT: Break concatenated names appropriately and capitalize properly.

Email addresses to analyze:
{email_list}

Respond in this exact JSON format:
{{
    "real_people": [
        {{"email": "john.smith@company.com", "name": "John Smith"}},
        {{"email": "sarah.j@company.com", "name": "Sarah J"}}
    ],
    "support_emails": ["support@company.com", "hr@company.com"],
    "analysis": "Brief explanation of filtering decisions"
}}
"""
            
            # Get AI response
            response = self.model.generate_content(prompt)
            response_text = response.text.strip()
            
            # Try to parse JSON from response
            try:
                import json
                # Extract JSON from response (in case there's extra text)
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    json_text = response_text[json_start:json_end]
                    result = json.loads(json_text)
                    
                    # Extract emails and names from the new format
                    real_people_data = result.get('real_people', [])
                    if real_people_data and isinstance(real_people_data[0], dict):
                        # New format with names
                        emails_list = [person['email'] for person in real_people_data]
                        names_list = [person['name'] for person in real_people_data]
                        
                        print(f"✅ AI identified {len(emails_list)} real people with names")
                        print(f"   👤 People: {', '.join(names_list[:3])}{'...' if len(names_list) > 3 else ''}")
                        print(f"   📧 Emails: {emails_list[:3]}{'...' if len(emails_list) > 3 else ''}")
                        print(f"   🤖 Support emails: {len(result.get('support_emails', []))}")
                        
                        # Return in new format with names
                        return {
                            'real_people': real_people_data,  # List of {email, name} dicts
                            'support_emails': result.get('support_emails', []),
                            'analysis': result.get('analysis', ''),
                            'emails_only': emails_list,  # For backward compatibility
                            'names_only': names_list      # Easy access to names
                        }
                    else:
                        # Old format fallback
                        print(f"✅ AI identified {len(real_people_data)} real people")
                        print(f"   📧 Real people: {real_people_data[:3]}{'...' if len(real_people_data) > 3 else ''}")
                        print(f"   🤖 Support emails: {len(result.get('support_emails', []))}")
                        
                        return result
                else:
                    raise Exception("No JSON found in response")
                    
            except Exception as parse_error:
                print(f"⚠️ Could not parse AI response: {parse_error}")
                print(f"Raw response: {response_text[:200]}...")
                
                # Fallback: simple rule-based filtering
                return self._fallback_filter(emails, company_domain)
                
        except Exception as e:
            print(f"❌ AI filtering failed: {e}")
            # Fallback to rule-based filtering
            return self._fallback_filter(emails, company_domain)
    
    def _fallback_filter(self, emails: List[str], company_domain: str) -> Dict:
        """Fallback rule-based filtering if AI fails"""
        print("🔧 Using fallback rule-based filtering...")
        
        # Common support/generic patterns
        support_patterns = [
            r'^(support|help|info|contact|customer|service)@',
            r'^(hr|careers|jobs|recruiting|talent)@',
            r'^(sales|marketing|admin|office)@',
            r'^(noreply|donotreply|no-reply|automated)@',
            r'^(webmaster|postmaster|mail|email)@',
            r'^(billing|accounting|finance)@',
            r'^(legal|compliance|security)@',
            r'^(it|tech|system|server)@'
        ]
        
        real_people = []
        support_emails = []
        
        for email in emails:
            email_lower = email.lower()
            
            # Check if it matches support patterns
            is_support = any(re.match(pattern, email_lower) for pattern in support_patterns)
            
            if is_support:
                support_emails.append(email)
            else:
                # Additional checks for real people
                local_part = email_lower.split('@')[0]
                
                # Look for name-like patterns
                has_name_pattern = (
                    '.' in local_part or  # john.smith
                    '_' in local_part or  # john_smith
                    len(local_part) > 3   # longer names more likely to be real
                )
                
                if has_name_pattern:
                    # Extract name from email for fallback
                    name = self._extract_name_from_email(email)
                    real_people.append({"email": email, "name": name})
                else:
                    support_emails.append(email)
        
        # Prepare return data
        emails_list = [person["email"] for person in real_people]
        names_list = [person["name"] for person in real_people]
        
        return {
            'real_people': real_people,
            'support_emails': support_emails,
            'analysis': f'Rule-based filtering: {len(real_people)} potential people, {len(support_emails)} support emails',
            'emails_only': emails_list,
            'names_only': names_list
        }
    
    def _extract_name_from_email(self, email: str) -> str:
        """Extract a likely name from an email address using simple rules"""
        try:
            local_part = email.split('@')[0]
            
            # Remove numbers and common suffixes
            local_part = re.sub(r'\d+$', '', local_part)  # Remove trailing numbers
            
            # Handle different separators
            if '.' in local_part:
                # john.smith → John Smith
                name_parts = local_part.split('.')
            elif '_' in local_part:
                # john_smith → John Smith  
                name_parts = local_part.split('_')
            else:
                # Try to split concatenated names intelligently
                # Look for common patterns like camelCase or known name endings
                name_parts = self._split_concatenated_name(local_part)
            
            # Capitalize each word
            name = ' '.join(word.capitalize() for word in name_parts if word and len(word) > 1)
            
            return name if name else local_part.capitalize()
            
        except:
            return email.split('@')[0].capitalize()
    
    def _split_concatenated_name(self, name: str) -> list:
        """Split concatenated names like 'daveburnisonms' into ['dave', 'burnison', 'ms']"""
        # Simple heuristic: split on common name patterns
        # This is basic - the AI should do better
        
        # Look for obvious patterns
        name = name.lower()
        
        # Common name endings
        if name.endswith('ms'):
            return [name[:-2], 'ms']
        elif name.endswith('jr'):
            return [name[:-2], 'jr']
        
        # Try to find word boundaries (very basic)
        # Split on vowel-consonant or consonant-vowel boundaries
        import re
        
        # Simple approach: assume max 2 parts for safety
        if len(name) > 6:
            mid = len(name) // 2
            return [name[:mid], name[mid:]]
        
        return [name]
