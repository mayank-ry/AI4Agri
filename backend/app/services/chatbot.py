import google.generativeai as genai
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)

class KisanMitraBot:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key and "PASTE" not in self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            logger.warning("Gemini API key not configured properly.")
        
        self.system_prompt = """
        You are 'Kisan Mitra' (Farmer's Friend), an AI agricultural assistant for Indian farmers.
        You help farmers with crop diseases, irrigation, weather, and yield predictions.
        Keep answers short, highly practical, and actionable.
        Always respond in the language the user speaks (English or Hindi).
        Use technical farming terms but explain them simply.
        """

    async def get_response(self, user_message: str, context: str = "") -> str:
        if not self.model:
            return "Kisan Mitra system is currently offline due to missing API keys. Please try again later."
            
        prompt = f"System: {self.system_prompt}\n\nContext: {context}\n\nUser: {user_message}"
        
        try:
            # Gemini SDK is synchronous by default, wrapping in a try-except
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error("gemini_api_error", error=str(e))
            return "Maaf karein, server error ki wajah se main abhi jawab nahi de paa raha. Thodi der baad koshish karein."

chatbot = KisanMitraBot()
