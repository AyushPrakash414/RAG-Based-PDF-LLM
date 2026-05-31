import os
from dotenv import load_dotenv
from google import genai

# Load environment variables from .env
load_dotenv()

# Get the API key
api_key = os.getenv("GEMINI_API_KEY")
model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")

# if not :
#     print("❌ GEMINI_API_KEY is not set correctly in the .env file.")
#     exit(1)

print(f"Testing connection to Gemini using model: {model_name}...")

try:
    # Initialize the client
    client = genai.Client(api_key=api_key)
    
    # Send a simple test prompt
    response = client.models.generate_content(
        model=model_name,
        contents="Hello! Please reply with a short 'Hello, I am working!' message."
    )
    
    print("\n✅ Connection Successful! Received response:")
    print("-" * 40)
    print(response.text)
    print("-" * 40)
except Exception as e:
    print(f"\n❌ Connection Failed. Error details:")
    print(e)
