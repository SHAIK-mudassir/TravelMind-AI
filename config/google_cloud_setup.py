import os
from google.cloud import aiplatform
from google.oauth2 import service_account
from google.auth import default
import googlemaps

def setup_google_cloud():
    """Setup Google Cloud credentials and initialize services"""
    try:
        # Check if running in Cloud Shell (has default credentials)
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        if credentials_path and os.path.exists(credentials_path):
            # Local development with service account
            print("🔑 Using service account credentials")
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path
            )
        else:
            # Cloud Shell or other environment with default credentials
            print("🌟 Using default Google Cloud credentials (Cloud Shell)")
            credentials, project_from_creds = default()
            
        # Set up Google Cloud project
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            # Try to get from default credentials in Cloud Shell
            try:
                import subprocess
                result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    project_id = result.stdout.strip()
                    print(f"📋 Detected project ID: {project_id}")
            except:
                pass
                
        if not project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set and could not detect project")

        # Initialize Vertex AI
        aiplatform.init(
            credentials=credentials,
            project=project_id
        )

        # Initialize Maps client
        maps_api_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not maps_api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY environment variable not set")
        
        maps_client = googlemaps.Client(key=maps_api_key)

        return {
            'credentials': credentials,
            'project_id': project_id,
            'maps_client': maps_client
        }

    except Exception as e:
        raise Exception(f"Failed to setup Google Cloud: {str(e)}")

def validate_environment():
    """Validate all required environment variables are set"""
    # Check if running in Cloud Shell
    is_cloud_shell = os.path.exists('/google/devshell/bashrc') or 'DEVSHELL_GCLOUD_CONFIG' in os.environ
    
    if is_cloud_shell:
        # In Cloud Shell, only API keys are required
        required_vars = ['GOOGLE_MAPS_API_KEY']
        optional_vars = ['YOUTUBE_API_KEY']
    else:
        # Local development requires all variables
        required_vars = [
            'GOOGLE_MAPS_API_KEY',
            'GOOGLE_CLOUD_PROJECT',
            'GOOGLE_APPLICATION_CREDENTIALS'
        ]
        optional_vars = ['YOUTUBE_API_KEY']
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        if is_cloud_shell:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing_vars)}\n"
                "Please add your API keys to the .env file."
            )
        else:
            raise ValueError(
                f"Missing required environment variables: {', '.join(missing_vars)}\n"
                "Please check your .env file and make sure all required variables are set."
            )
