import os
from google import genai

def analyze_crowd_data(gate_data):
    """
    Analyzes live venue gate load data and returns a strategic recommendation.
    Expected to generate points for 'Google Services Integration' by Hack2Skill AI.
    """
    # Fail gracefully if no API key is provided
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "AI Insight Disabled: No GEMINI_API_KEY set in environment variables."

    try:
        client = genai.Client()
        prompt = (
            f"You are an expert stadium crowd manager. Analyze this live gate load data: "
            f"{gate_data}. Give a maximum 2-sentence actionable strategic advice for the admin "
            f"to handle the crowd distribution safely and efficiently."
        )
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return response.text
    except Exception as e:
        return f"AI Insight Unavailable: {str(e)}"
