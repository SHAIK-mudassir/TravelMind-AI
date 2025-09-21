import subprocess
import os
from dotenv import load_dotenv
import time

def run_gcloud_command(command):
    """Run a gcloud command and return the result"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_and_enable_apis():
    """Check and enable required APIs for Vertex AI"""
    load_dotenv()
    
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    print(f"🔍 Checking APIs for project: {project_id}")
    print("=" * 50)
    
    # Required APIs
    apis = [
        ("aiplatform.googleapis.com", "Vertex AI API"),
        ("ml.googleapis.com", "AI Platform API"), 
        ("compute.googleapis.com", "Compute Engine API"),
        ("bigquery.googleapis.com", "BigQuery API"),
        ("maps-backend.googleapis.com", "Maps API")
    ]
    
    # Check current API status
    print("📋 Checking current API status...")
    success, stdout, stderr = run_gcloud_command(f"gcloud services list --enabled --project={project_id}")
    
    if not success:
        print(f"❌ Failed to check APIs: {stderr}")
        return False
    
    enabled_apis = stdout.lower()
    
    # Enable missing APIs
    for api, description in apis:
        if api in enabled_apis:
            print(f"✅ {description} ({api}) - Already enabled")
        else:
            print(f"🔄 Enabling {description} ({api})...")
            success, stdout, stderr = run_gcloud_command(f"gcloud services enable {api} --project={project_id}")
            
            if success:
                print(f"✅ {description} enabled successfully")
            else:
                print(f"❌ Failed to enable {description}: {stderr}")
    
    print("\n⏳ Waiting for APIs to propagate (30 seconds)...")
    time.sleep(30)
    
    return True

def check_vertex_ai_access():
    """Check if Vertex AI is accessible"""
    print("\n🔍 Testing Vertex AI access...")
    
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        
        # Try different locations
        locations = ['us-central1', 'us-east1', 'us-west1', 'europe-west1']
        
        for location in locations:
            print(f"\n📍 Testing location: {location}")
            try:
                vertexai.init(project=project_id, location=location)
                print(f"✅ Vertex AI initialized in {location}")
                
                # Try to list models (this will fail if no access)
                try:
                    # Simple test - try to create a model instance
                    model = GenerativeModel("gemini-pro")
                    print(f"✅ Model access confirmed in {location}")
                    return location
                except Exception as model_error:
                    print(f"❌ No model access in {location}: {str(model_error)[:100]}...")
                    
            except Exception as location_error:
                print(f"❌ Failed to initialize in {location}: {str(location_error)[:100]}...")
        
        return None
        
    except Exception as e:
        print(f"❌ Vertex AI test failed: {str(e)}")
        return None

def main():
    """Main function to enable and test Vertex AI"""
    print("🚀 Vertex AI Setup and Testing")
    print("=" * 50)
    
    # Step 1: Check gcloud authentication
    print("1️⃣ Checking gcloud authentication...")
    success, stdout, stderr = run_gcloud_command("gcloud auth list")
    
    if not success:
        print("❌ gcloud not authenticated. Please run: gcloud auth login")
        return
    
    print("✅ gcloud authenticated")
    
    # Step 2: Enable APIs
    print("\n2️⃣ Enabling required APIs...")
    if not check_and_enable_apis():
        print("❌ Failed to enable APIs")
        return
    
    # Step 3: Test Vertex AI access
    print("\n3️⃣ Testing Vertex AI access...")
    working_location = check_vertex_ai_access()
    
    if working_location:
        print(f"\n🎉 SUCCESS! Vertex AI is working in location: {working_location}")
        print(f"\n💡 Update your .env file:")
        print(f"VERTEXAI_LOCATION={working_location}")
        
        # Update .env file
        try:
            with open('.env', 'r') as f:
                content = f.read()
            
            if 'VERTEXAI_LOCATION=' in content:
                # Replace existing
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if line.startswith('VERTEXAI_LOCATION='):
                        lines[i] = f'VERTEXAI_LOCATION={working_location}'
                        break
                content = '\n'.join(lines)
            else:
                # Add new
                content += f'\nVERTEXAI_LOCATION={working_location}'
            
            with open('.env', 'w') as f:
                f.write(content)
            
            print("✅ .env file updated automatically")
            
        except Exception as e:
            print(f"⚠️  Could not update .env file automatically: {e}")
    
    else:
        print("\n❌ Vertex AI is not accessible in any location")
        print("\n🔧 Troubleshooting steps:")
        print("1. Ensure billing is enabled on your project")
        print("2. Check that your service account has 'Vertex AI User' role")
        print("3. Try running: gcloud auth application-default login")
        print("4. Contact Google Cloud support if the issue persists")

if __name__ == "__main__":
    main()
