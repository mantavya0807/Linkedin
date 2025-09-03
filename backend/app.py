from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time
import os
from dotenv import load_dotenv

# Import our services
from ai_service import AIService
from email_service import EmailService
from linkedin_service import LinkedInService
from email_scraper import EmailScraper

load_dotenv()

app = Flask(__name__)
CORS(app)

# Global services
ai_service = AIService()
email_service = EmailService()
linkedin_service = LinkedInService()
email_scraper = EmailScraper()

# Simple in-memory storage for results
campaign_results = []
campaign_counter = 1

def run_campaign_async(campaign_data):
    """Run the outreach campaign in background"""
    global campaign_counter, campaign_results
    
    campaign_id = campaign_counter
    campaign_counter += 1
    
    # Initialize result
    result = {
        'id': campaign_id,
        'domain': campaign_data['domain'],
        'status': 'running',
        'emails_found': 0,
        'emails_sent': 0,
        'linkedin_sent': 0,
        'errors': []
    }
    
    campaign_results.append(result)
    
    try:
        domain = campaign_data['domain']
        target_email_count = campaign_data.get('target_email_count', 5)  # Add default
        job_description = campaign_data.get('job_description', '')
        email_enabled = campaign_data.get('email_enabled', True)
        linkedin_enabled = campaign_data.get('linkedin_enabled', True)
        
        print(f"\n🚀 Starting campaign {campaign_id} for {domain}")
        
        # Get company name for messaging
        clean_domain = email_scraper.clean_domain(domain)
        if not clean_domain:
            result['status'] = 'failed'
            result['errors'].append('Invalid domain')
            return
        
        company_name = clean_domain.split('.')[0].title()
        
        # Load resume and generate personalized content
        resume_content = ai_service.load_resume()
        personalized_email = ai_service.generate_personalized_paragraph(
            resume_content, job_description
        )
        
        # EMAIL OUTREACH
        if email_enabled:
            try:
                print(f"📧 Starting email outreach for {company_name}...")
                
                # Find emails using our enhanced scraper with AI filtering
                emails = email_scraper.find_emails(clean_domain)
                result['emails_found'] = len(emails)
                
                if emails:
                    print(f"✅ Found {len(emails)} real people emails")
                    
                    # Send emails to found contacts
                    emails_sent = 0
                    for email in emails[:target_email_count]:
                        try:
                            # Generate personalized email using AI
                            personalized_content = ai_service.generate_personalized_email(
                                resume_content, job_description, company_name, email
                            )
                            
                            subject = f"Software Engineer Opportunity - {personalized_content.get('subject', 'Partnership Inquiry')}"
                            body = personalized_content.get('body', personalized_email)
                            
                            # Send email
                            if email_service.send_email(email, subject, body):
                                emails_sent += 1
                                print(f"   ✅ Email sent to {email}")
                                time.sleep(2)  # Rate limiting
                            else:
                                print(f"   ❌ Failed to send email to {email}")
                                
                        except Exception as e:
                            print(f"   ❌ Error sending to {email}: {e}")
                            continue
                    
                    result['emails_sent'] = emails_sent
                    print(f"📧 Email campaign complete: {emails_sent}/{len(emails)} sent")
                else:
                    print("❌ No emails found for outreach")
                    
            except Exception as e:
                print(f"❌ Email outreach failed: {e}")
                result['errors'].append(f'Email error: {str(e)}')
        
        # LINKEDIN OUTREACH
        if linkedin_enabled:
            try:
                print(f"\n🔗 Starting LinkedIn outreach for {company_name}...")
                
                # Use the emails we found to search for people on LinkedIn
                target_emails = emails[:10] if emails else []  # Use first 10 emails
                
                if target_emails:
                    linkedin_results = linkedin_service.search_people_by_emails(
                        target_emails, company_name, max_connections=5
                    )
                    
                    result['linkedin_people_found'] = len(linkedin_results)
                    result['linkedin_connections_sent'] = sum(1 for r in linkedin_results if r.get('connected'))
                    
                    print(f"🔗 LinkedIn campaign complete: {result['linkedin_connections_sent']} connections sent")
                else:
                    print("❌ No email data available for LinkedIn search")
                    
            except Exception as e:
                print(f"❌ LinkedIn outreach failed: {e}")
                result['errors'].append(f'LinkedIn error: {str(e)}')
        
        # Update final status
        if result['emails_sent'] > 0 or result.get('linkedin_connections_sent', 0) > 0:
            result['status'] = 'completed'
        else:
            result['status'] = 'failed'
            
        result['completed_at'] = time.time()
        print(f"\n✅ Campaign {campaign_id} completed!")
        print(f"   📧 Emails: {result['emails_sent']}/{result['emails_found']}")
        print(f"   🔗 LinkedIn: {result.get('linkedin_connections_sent', 0)}/{result.get('linkedin_people_found', 0)}")
        
    except Exception as e:
        print(f"❌ Campaign {campaign_id} failed: {e}")
        result['status'] = 'failed'
        result['errors'].append(str(e))

# API Routes
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "message": "Cold Outreach API is running",
        "services": {
            "ai": len(ai_service.models) > 0,
            "email": len(email_service.email_providers) > 0,
            "linkedin": bool(linkedin_service.linkedin_email)
        }
    })

@app.route('/api/launch', methods=['POST'])
def launch_campaign():
    """Launch a new outreach campaign"""
    try:
        data = request.json
        
        # Validation
        if not data or not data.get('domain'):
            return jsonify({"error": "Domain is required"}), 400
        
        if not data.get('email_enabled') and not data.get('linkedin_enabled'):
            return jsonify({"error": "At least one outreach method must be enabled"}), 400
        
        # Start campaign in background
        campaign_thread = threading.Thread(target=run_campaign_async, args=(data,))
        campaign_thread.daemon = True
        campaign_thread.start()
        
        return jsonify({
            "success": True,
            "message": "Campaign launched successfully",
            "campaign_id": campaign_counter - 1
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/campaigns', methods=['GET'])
def get_campaigns():
    """Get all campaign results"""
    return jsonify({
        "success": True,
        "campaigns": campaign_results
    })

@app.route('/api/campaigns/<int:campaign_id>', methods=['GET'])
def get_campaign(campaign_id):
    """Get specific campaign result"""
    campaign = next((c for c in campaign_results if c['id'] == campaign_id), None)
    
    if not campaign:
        return jsonify({"error": "Campaign not found"}), 404
    
    return jsonify({
        "success": True,
        "campaign": campaign
    })

@app.route('/api/test-email-connection', methods=['POST'])
def test_email_connection():
    """Test email provider connections"""
    try:
        results = []
        
        for provider in email_service.email_providers:
            test_result = email_service.test_connection(provider)
            results.append({
                'provider': provider['name'],
                'email': provider['email'],
                'success': test_result
            })
        
        return jsonify({
            "success": True,
            "connection_tests": results
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-email', methods=['POST'])
def test_email():
    """Test email sending"""
    try:
        data = request.json
        test_email = data.get('email')
        
        if not test_email:
            return jsonify({"error": "Email address required"}), 400
        
        # Send test email
        success = email_service.send_email(
            test_email,
            "Test Email from Cold Outreach System",
            "This is a test email to verify email configuration is working."
        )
        
        return jsonify({
            "success": success,
            "message": "Test email sent" if success else "Test email failed"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-scraper', methods=['POST'])
def test_scraper():
    """Test email scraping"""
    try:
        data = request.json
        domain = data.get('domain')
        
        if not domain:
            return jsonify({"error": "Domain required"}), 400
        
        # Test scraping
        emails = email_scraper.find_emails(domain)
        
        return jsonify({
            "success": True,
            "domain": domain,
            "emails_found": len(emails),
            "emails": emails[:5]  # Return first 5 for testing
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/test-email-template', methods=['POST'])
def test_email_template():
    """Test the new email template generation"""
    try:
        data = request.json
        company_name = data.get('company_name', 'Example Company')
        job_description = data.get('job_description', 'We are looking for talented software engineers to join our team.')
        
        # Generate personalized email
        resume_content = ai_service.load_resume()
        personalized_email = ai_service.generate_personalized_paragraph(
            resume_content, job_description
        )
        
        # Create subject
        subject = f"Quick question about opportunities at {company_name}"
        
        return jsonify({
            "success": True,
            "subject": subject,
            "body": personalized_email,
            "template_info": {
                "structure": "6-8 sentences with hook, intro, knowledge, value, portfolio, ask",
                "tone": "casual, confident, not salesy"
            }
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Starting Cold Outreach API Server...")
    print("📍 Server: http://localhost:5000")
    print("🔧 Available endpoints:")
    print("   - GET  /api/health - Health check")
    print("   - POST /api/launch - Launch campaign")
    print("   - GET  /api/campaigns - Get all campaigns")
    print("   - POST /api/test-email-connection - Test email connections")
    print("   - POST /api/test-email - Test email sending")
    print("   - POST /api/test-scraper - Test email scraping")
    print("   - POST /api/test-email-template - Test new email template")
    
    # Check service health on startup
    print("\n🔍 Checking services...")
    print(f"   AI Service: {'✅' if len(ai_service.models) > 0 else '❌'} ({len(ai_service.models)} keys)")
    print(f"   Email Service: {'✅' if len(email_service.email_providers) > 0 else '❌'} ({len(email_service.email_providers)} providers)")
    print(f"   LinkedIn Service: {'✅' if linkedin_service.linkedin_email else '❌'}")
    
    print("\n🌟 Server starting...")
    app.run(debug=True, host='0.0.0.0', port=5000)