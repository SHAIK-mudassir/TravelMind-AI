#!/usr/bin/env python3
"""
Check what AI models are actually available in your Google Cloud project
"""

import os
import subprocess
from dotenv import load_dotenv

def check_available_models():
    """Check what models are available via gcloud"""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'idyllic-aspect-472419-i8')
    
    print("🔍 Checking available AI models in your project")
    print(f"📋 Project: {project_id}")
    print("=" * 60)
    
    # Check Vertex AI models
    print("\n🤖 Checking Vertex AI models...")
    locations = ['us-central1', 'us-east1', 'us-west1']
    
    for location in locations:
        print(f"\n📍 Location: {location}")
        try:
            # Try to list models in this location
            cmd = f"gcloud ai models list --region={location} --project={project_id}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                if result.stdout.strip():
                    print(f"  ✅ Models available:")
                    print(f"  {result.stdout}")
                else:
                    print(f"  ⚠️  No models listed (but API accessible)")
            else:
                print(f"  ❌ Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"  ⏰ Timeout checking {location}")
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
    
    # Check if we can access any text generation models
    print(f"\n📝 Checking legacy text models...")
    try:
        import vertexai
        from vertexai.language_models import TextGenerationModel
        
        vertexai.init(project=project_id, location='us-central1')
        
        legacy_models = ['text-bison', 'text-bison@001', 'text-bison@002']
        
        for model_name in legacy_models:
            try:
                print(f"  🧪 Testing {model_name}...", end=" ")
                model = TextGenerationModel.from_pretrained(model_name)
                response = model.predict("Hello", max_output_tokens=5)
                if response and response.text:
                    print("✅ WORKING")
                    return model_name  # Return first working model
                else:
                    print("⚠️  NO RESPONSE")
            except Exception as e:
                error_msg = str(e)
                if "not found" in error_msg.lower():
                    print("❌ NOT FOUND")
                else:
                    print(f"❌ ERROR: {error_msg[:30]}...")
                    
    except ImportError:
        print("  ❌ Vertex AI SDK not available")
    except Exception as e:
        print(f"  ❌ Error initializing Vertex AI: {str(e)}")
    
    print(f"\n" + "="*60)
    print("📊 SUMMARY:")
    print("❌ No Gemini models available in your project")
    print("❌ No legacy text models available")
    
    print(f"\n💡 SOLUTIONS:")
    print("1. Your project might need to be allowlisted for Gemini models")
    print("2. Try requesting access through Google Cloud Console")
    print("3. For hackathon, we can use a mock AI service")
    
    return None

if __name__ == "__main__":
    working_model = check_available_models()
    
    if working_model:
        print(f"\n🎉 Found working model: {working_model}")
    else:
        print(f"\n🔄 Recommendation: Use mock AI service for hackathon demo")
        print(f"   Your app will still work with all other features!")
