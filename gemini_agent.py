import os
from google import genai

def analyze_crowd_data(gate_data):
    """
    Analyzes live venue gate load data and returns a strategic recommendation.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI Insight Disabled: No GEMINI_API_KEY set."

    try:
        client = genai.Client()
        prompt = (
            f"You are an expert stadium crowd manager. Analyze this live gate load data: "
            f"{gate_data}. Give a maximum 2-sentence actionable strategic advice for the admin "
            f"to handle the crowd distribution safely and efficiently."
        )
        response = client.models.generate_content(
            model='gemini-2.0-flash', # Use flash for speed
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"AI Insight Unavailable: {str(e)}"

def get_chat_response(message, role, context_data):
    """
    Dynamic chatbot handler.
    Strictly forbidden from discussing passwords/hashes.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Bot System Offline (Missing API Key)."

    try:
        client = genai.Client()
        
        system_instruction = (
            "You are 'VenueFlow AI', a helpful and professional stadium assistant for IPL 2026. "
            f"The user you are talking to has the role of: {role}. "
            "Your goals are: 1. Assist with logistics, gate status, and match info. "
            "2. Provide operational tips if they are Staff or Admin. "
            "3. Help with registration if they are a Guest/Login user. "
            "CRITICAL SECURITY RULE: NEVER provide passwords, pbkdf2 hashes, or any credential data. "
            "If asked for a password, state that for security reasons, you do not have access to passwords."
        )

        full_prompt = (
            f"Context Information: {context_data}\n\n"
            f"User Question: {message}\n\n"
            "Response (concise, professional, and emoji-friendly):"
        )

        response = client.models.generate_content(
            model='gemini-2.0-flash',
            config={'system_instruction': system_instruction},
            contents=full_prompt,
        )
        return response.text
    except Exception as e:
        return f"Bot Error: {str(e)}"
