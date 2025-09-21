#!/usr/bin/env python3
"""
Simple test to check if Vertex AI is working in Cloud Shell
"""

import os
import vertexai
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

def test_vertex_ai_simple():
    """Test basic Vertex AI functionality"""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'idyllic-aspect-472419-i8')
    
    locations_to_test = ['us-central1', 'us-east1', 'us-west1']
    models_to_test = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-pro']
    
    print("🧪 Testing Vertex AI in Cloud Shell")
    print(f"📋 Project: {project_id}")
    print("=" * 50)
    
    for location in locations_to_test:
        print(f"\n📍 Testing location: {location}")
        
        try:
            # Initialize Vertex AI
            vertexai.init(project=project_id, location=location)
            print(f"  ✅ Vertex AI initialized in {location}")
            
            for model_name in models_to_test:
                try:
                    print(f"    🤖 Testing model: {model_name}...", end=" ")
                    
                    # Create model instance
                    model = GenerativeModel(model_name)
                    
                    # Test with simple prompt
                    response = model.generate_content("Say hello")
                    
                    if response and response.text:
                        print("✅ WORKING")
                        print(f"      📝 Response: {response.text[:50]}...")
                        
                        # If we found a working combination, return it
                        return location, model_name
                    else:
                        print("⚠️  NO RESPONSE")
                        
                except Exception as model_error:
                    error_msg = str(model_error)
                    if "not found" in error_msg.lower():
                        print("❌ NOT FOUND")
                    elif "permission" in error_msg.lower() or "access" in error_msg.lower():
                        print("🔒 NO ACCESS")
                    else:
                        print(f"❌ ERROR: {error_msg[:30]}...")
                        
        except Exception as location_error:
            print(f"  ❌ Failed to initialize in {location}: {str(location_error)[:50]}...")
    
    print("\n" + "="*50)
    print("❌ No working Vertex AI configuration found")
    print("\n💡 Troubleshooting:")
    print("1. Make sure you're in Google Cloud Shell")
    print("2. Check if Vertex AI API is enabled:")
    print("   gcloud services enable aiplatform.googleapis.com")
    print("3. Verify your project has access to Gemini models")
    
    return None, None

if __name__ == "__main__":
    working_location, working_model = test_vertex_ai_simple()
    
    if working_location and working_model:
        print(f"\n🎉 SUCCESS!")
        print(f"✅ Working configuration found:")
        print(f"   Location: {working_location}")
        print(f"   Model: {working_model}")
        
        print(f"\n📝 Update your .env file:")
        print(f"VERTEXAI_LOCATION={working_location}")
        
        print(f"\n🚀 Now you can run:")
        print(f"streamlit run app.py")
    else:
        print(f"\n❌ No working configuration found")
        print(f"💡 Your app will fall back to mock/template responses")
