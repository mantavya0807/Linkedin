import google.generativeai as genai
import os
import time
import random
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.api_keys = [
            os.getenv('GEMINI_API_KEY_1'),
            os.getenv('GEMINI_API_KEY_2')
        ]
        self.current_key_index = 0
        self.models = []
        
        # Initialize models for both keys
        for key in self.api_keys:
            if key:
                try:
                    genai.configure(api_key=key)
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    self.models.append(model)
                    print(f"✅ Gemini API key initialized: {key[:10]}...")
                except Exception as e:
                    print(f"❌ Failed to initialize Gemini key {key[:10]}...: {e}")
        
        if not self.models:
            print("❌ No Gemini API keys working!")
    
    def get_predefined_templates(self):
        """Fallback templates when AI fails"""
        templates = [
            "Most scaling challenges feel like you're constantly putting out fires — but that's where the interesting engineering problems live. I'm Mantavya Mahajan, a Computer Science and Mathematics student at Penn State, currently working as a GenAI intern at Scale AI. I've been following your company's work in building robust infrastructure, and your approach to handling high-throughput systems really stands out. My experience with optimizing API performance (boosted throughput by 15% to 1,440 req/sec at M8) and building ML pipelines could be valuable as you scale. Here's some of my work: https://mantavya-mahajan-portfolio.vercel.app/. Would you be open to a quick chat about internship opportunities this summer, or even fall and full-time roles starting December 2025?",
            
            "Building products that actually solve real problems is harder than it looks — most tools end up being clunky workarounds. I'm Mantavya Mahajan, a Computer Science and Mathematics student at Penn State, currently working as a GenAI intern at Scale AI. Your product's focus on user experience and technical elegance really caught my attention. With my background in full-stack development and AI systems (built multi-agent workflows reducing content creation time by 60%), I'd love to contribute to what you're building. Check out my work: https://mantavya-mahajan-portfolio.vercel.app/. Would you be open to a quick chat about summer internships or full-time opportunities starting December 2025?",
            
            "Data pipelines that actually work reliably are surprisingly rare — yours seem to be the exception. I'm Mantavya Mahajan, a CS and Math student at Penn State, currently interning at Scale AI on GenAI systems. I've been impressed by your approach to handling large-scale data processing and your focus on reliability. My experience with building RAG systems, optimizing database performance, and working with real-time data processing could add value to your team. Here's my portfolio: https://mantavya-mahajan-portfolio.vercel.app/. Would you be interested in a quick chat about internship opportunities or full-time roles starting December 2025?",
            
            "Most AI tools feel like black boxes wrapped in hype — but your approach to transparency and practical implementation is refreshing. I'm Mantavya Mahajan, a Computer Science and Mathematics student at Penn State, currently working as a GenAI intern at Scale AI. Your work on making AI actually useful for real business problems really resonates with me. With my experience in LLM optimization, building evaluation frameworks, and full-stack AI applications, I think I could contribute meaningfully to your mission. Check out my work: https://mantavya-mahajan-portfolio.vercel.app/. Would you be open to discussing summer internship or full-time opportunities starting December 2025?"
        ]
        return random.choice(templates)
    
    def generate_personalized_paragraph(self, resume_content="", job_description=""):
        """Generate personalized paragraph with AI fallbacks"""
        
        if not self.models:
            return self.get_predefined_templates()
        
        if not resume_content or not job_description:
            return self.get_predefined_templates()
        
        prompt = f"""You are writing a cold outreach email for Mantavya Mahajan to a tech company. Follow this EXACT structure and tone:

STRUCTURE (6-8 sentences total):
1. **Hook**: One short, witty sentence about their product/industry pain point
2. **Intro**: "I'm Mantavya Mahajan, a Computer Science and Mathematics student at Penn State, currently working as a GenAI intern at Scale AI."
3. **Knowledge**: 1-2 sentences showing you know what they do (be specific)
4. **Value**: 1-2 sentences on relevant skills/experience that could help them
5. **Portfolio**: Natural mention: "Here's some of my work: https://mantavya-mahajan-portfolio.vercel.app/"
6. **Ask**: "Would you be open to a quick chat about internship opportunities this summer, or even fall and full-time roles starting December 2025?"

TONE: Casual, confident, not salesy. No buzzwords or jargon.

RESUME HIGHLIGHTS TO USE:
- Scale AI: GenAI intern improving LLM accuracy, building evaluation systems
- M8: Lead Backend Developer, optimized APIs to 1,440 req/sec
- Voodies: Full-stack AI engineer, built multi-agent workflows
- Projects: Meal Plan Optimizer (5,000+ transactions), EPU Index (50,000+ headlines)
- Skills: Python, AI/ML, full-stack development, system optimization

COMPANY INFO:
{job_description}

Generate the complete email following this structure. Keep it conversational and specific to their company/role:"""

        # Try each model/key
        for attempt in range(len(self.models)):
            try:
                model = self.models[self.current_key_index]
                print(f"🧠 Trying Gemini API key {self.current_key_index + 1}...")
                
                response = model.generate_content(prompt)
                if response and response.text:
                    generated_email = response.text.strip()
                    if len(generated_email) > 200 and "Mantavya Mahajan" in generated_email:  # Quality check
                        print("✅ AI email generated successfully")
                        return generated_email
                
            except Exception as e:
                print(f"⚠️ Gemini key {self.current_key_index + 1} failed: {e}")
                
            # Switch to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.models)
            time.sleep(1)  # Brief delay before retry
        
        print("⚠️ All AI services failed, using predefined template")
        return self.get_predefined_templates()
    
    def load_resume(self, resume_path="resume.txt"):
        """Load resume content from file"""
        try:
            with open(resume_path, "r", encoding="utf-8") as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"❌ Resume file not found: {resume_path}")
            return ""
        except Exception as e:
            print(f"❌ Error loading resume: {e}")
            return ""