import vertexai
from vertexai.language_models import TextGenerationModel, ChatModel
from vertexai.generative_models import GenerativeModel
import os
from dotenv import load_dotenv

def test_ai_models_direct():
    """Test AI models directly using service account credentials"""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    location = os.getenv('VERTEXAI_LOCATION', 'us-central1')
    
    print(f"🔍 Testing AI models directly")
    print(f"📋 Project: {project_id}")
    print(f"📍 Location: {location}")
    print("=" * 50)
    
    # Initialize Vertex AI
    try:
        vertexai.init(project=project_id, location=location)
        print("✅ Vertex AI initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Vertex AI: {str(e)}")
        return
    
    # Test different model categories
    model_tests = [
        # Legacy text generation models (most likely to work)
        ("Legacy Text Models", [
            ("text-bison@002", "legacy_text"),
            ("text-bison@001", "legacy_text"),
            ("text-bison", "legacy_text")
        ]),
        
        # Legacy chat models
        ("Legacy Chat Models", [
            ("chat-bison@002", "legacy_chat"),
            ("chat-bison@001", "legacy_chat"),
            ("chat-bison", "legacy_chat")
        ]),
        
        # New Gemini models (might not be available)
        ("Gemini Models", [
            ("gemini-pro", "gemini"),
            ("gemini-1.0-pro", "gemini"),
            ("gemini-1.5-pro", "gemini"),
            ("gemini-1.5-flash", "gemini")
        ])
    ]
    
    working_models = []
    
    for category, models in model_tests:
        print(f"\n🧪 Testing {category}:")
        print("-" * 30)
        
        for model_name, model_type in models:
            try:
                print(f"  Testing {model_name}...", end=" ")
                
                if model_type == "legacy_text":
                    model = TextGenerationModel.from_pretrained(model_name)
                    response = model.predict("Hello", max_output_tokens=10)
                    if response and response.text:
                        print("✅ WORKING")
                        working_models.append((model_name, model_type))
                    else:
                        print("⚠️  NO RESPONSE")
                        
                elif model_type == "legacy_chat":
                    model = ChatModel.from_pretrained(model_name)
                    chat = model.start_chat()
                    response = chat.send_message("Hello", max_output_tokens=10)
                    if response and response.text:
                        print("✅ WORKING")
                        working_models.append((model_name, model_type))
                    else:
                        print("⚠️  NO RESPONSE")
                        
                elif model_type == "gemini":
                    model = GenerativeModel(model_name)
                    response = model.generate_content("Hello")
                    if response and response.text:
                        print("✅ WORKING")
                        working_models.append((model_name, model_type))
                    else:
                        print("⚠️  NO RESPONSE")
                        
            except Exception as e:
                error_msg = str(e).lower()
                if "not found" in error_msg or "does not exist" in error_msg:
                    print("❌ NOT FOUND")
                elif "permission" in error_msg or "access" in error_msg:
                    print("🔒 NO ACCESS")
                elif "quota" in error_msg or "limit" in error_msg:
                    print("⚠️  QUOTA EXCEEDED")
                else:
                    print(f"❌ ERROR: {str(e)[:50]}...")
    
    # Summary
    print("\n" + "="*50)
    print("📊 RESULTS SUMMARY")
    print("="*50)
    
    if working_models:
        print(f"✅ Found {len(working_models)} working model(s):")
        for model_name, model_type in working_models:
            print(f"  • {model_name} ({model_type})")
        
        # Recommend the best model
        best_model = working_models[0]
        print(f"\n🎯 RECOMMENDED MODEL: {best_model[0]}")
        print(f"📝 Model Type: {best_model[1]}")
        
        # Create a simple test
        print(f"\n🧪 Testing recommended model with travel query...")
        try:
            if best_model[1] == "legacy_text":
                model = TextGenerationModel.from_pretrained(best_model[0])
                response = model.predict(
                    "Create a 1-day itinerary for Delhi with budget ₹2000",
                    max_output_tokens=200
                )
                print(f"✅ Travel test successful!")
                print(f"📝 Sample response: {response.text[:100]}...")
                
            elif best_model[1] == "legacy_chat":
                model = ChatModel.from_pretrained(best_model[0])
                chat = model.start_chat()
                response = chat.send_message(
                    "Create a 1-day itinerary for Delhi with budget ₹2000",
                    max_output_tokens=200
                )
                print(f"✅ Travel test successful!")
                print(f"📝 Sample response: {response.text[:100]}...")
                
            elif best_model[1] == "gemini":
                model = GenerativeModel(best_model[0])
                response = model.generate_content(
                    "Create a 1-day itinerary for Delhi with budget ₹2000"
                )
                print(f"✅ Travel test successful!")
                print(f"📝 Sample response: {response.text[:100]}...")
                
        except Exception as e:
            print(f"⚠️  Travel test failed: {str(e)[:100]}...")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Your app will automatically use: {best_model[0]}")
        print(f"2. Run: streamlit run app.py")
        print(f"3. Test the travel planner!")
        
    else:
        print("❌ No working models found!")
        print("\n🔧 TROUBLESHOOTING:")
        print("1. Check if Vertex AI API is enabled in Google Cloud Console")
        print("2. Verify your service account has 'Vertex AI User' role")
        print("3. Ensure billing is enabled on your project")
        print("4. Try a different region in your .env file:")
        print("   VERTEXAI_LOCATION=us-east1")

if __name__ == "__main__":
    test_ai_models_direct()
