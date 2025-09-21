import os
from google import genai
from google.genai.types import GenerateContentConfig

def test_locations():
    locations = [
        'us-central1',
        'us-east1', 
        'us-west1',
        'europe-west1',
        'asia-southeast1'
    ]
    
    print("🌍 Testing Vertex AI locations for your project...")
    
    for location in locations:
        print(f"\n📍 Testing {location}:")
        
        try:
            # Set environment variable for this test
            os.environ['VERTEXAI_LOCATION'] = location
            
            # Try to initialize GenAI client
            client = genai.Client()
            
            # Test with a simple model
            response = client.models.generate_content(
                model="gemini-1.5-flash",
                contents="Hello",
                config=GenerateContentConfig(
                    candidate_count=1,
                    max_output_tokens=10
                )
            )
            
            if response and response.candidates:
                print(f"  ✅ {location} - WORKING")
            else:
                print(f"  ⚠️  {location} - No response")
                
        except Exception as e:
            error_msg = str(e)
            if "not found" in error_msg.lower():
                print(f"  ❌ {location} - Models not available")
            elif "permission" in error_msg.lower():
                print(f"  🔒 {location} - Permission denied")
            else:
                print(f"  ❌ {location} - Error: {error_msg[:50]}...")

if __name__ == "__main__":
    test_locations()