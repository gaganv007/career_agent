import os

## Gemini API Key (Get from Google AI Studio: https://aistudio.google.com/app/apikey)
#os.environ["GOOGLE_API_KEY"] = "AIzaSyBaFaHFk9SB_Ig6poQTjuGwonXZiqZW2qI"   #Sean's API Key
os.environ["GOOGLE_API_KEY"] = "AIzaSyC6ovmRO-u3hJOKqI2x1bCZql6-htTvhaM"    #Gagan's API Key
MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

# --- Verify Keys (Optional Check) ---
print(f"Google API Key set: {'Yes' if os.environ.get('GOOGLE_API_KEY') and os.environ['GOOGLE_API_KEY'] != 'YOUR_GOOGLE_API_KEY' else 'No (REPLACE PLACEHOLDER!)'}")
print("\nEnvironment configured.")