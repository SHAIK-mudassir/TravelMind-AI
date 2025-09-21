from google.cloud import bigquery
from google.cloud import aiplatform
import vertexai
from google.cloud import aiplatform
from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from google.cloud import bigquery
import googlemaps
import os
from dotenv import load_dotenv

def test_environment_variables():
    """Test that all required environment variables are set"""
    print("🔍 Testing environment variables...")
    
    # Load environment variables
    load_dotenv()
    
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_MAPS_API_KEY'
    ]
    
    optional_vars = [
        'YOUTUBE_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            print(f"  ✅ {var}: {'*' * min(len(value), 20)}...")
    
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"  ✅ {var}: {'*' * min(len(value), 20)}...")
        else:
            print(f"  ⚠️  {var}: Not set (optional)")
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment variables check passed!")
    return True

def test_credentials_file():
    """Test Google Cloud credentials file"""
    print("\n🔍 Testing credentials file...")
    
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        print("❌ GOOGLE_APPLICATION_CREDENTIALS not set")
        return False
    
    if not os.path.exists(credentials_path):
        print(f"❌ Credentials file not found at: {credentials_path}")
        return False
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
        response = request.execute()
        print("✅ YouTube API connection successful")
    except Exception as e:
        print(f"❌ YouTube API error: {str(e)}")

    # Test 5: Google Maps API
    print("\n5. Testing Google Maps API...")
    try:
        gmaps = googlemaps.Client(key=os.getenv('GOOGLE_MAPS_API_KEY'))
        result = gmaps.geocode('Delhi, India')
        if result:
            print("✅ Google Maps API connection successful")
        else:
            print("❌ Google Maps API returned no results")
    except Exception as e:
        print(f"❌ Google Maps API error: {str(e)}")

if __name__ == "__main__":
    test_configuration()
