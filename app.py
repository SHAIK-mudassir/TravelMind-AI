import streamlit as st
import os
from dotenv import load_dotenv
from services.maps_service import MapsService
import folium
from streamlit_folium import folium_static
import json

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Validate and setup Google Cloud
from config.google_cloud_setup import setup_google_cloud, validate_environment

@st.cache_resource
def get_ai_service():
    """Initialize AI service with caching to prevent re-initialization"""
    # Try to initialize AI service with multiple fallbacks
    ai_service = None
    
    # Try 1: Enhanced AI Service (with multiple options and natural language)
    try:
        from services.ai_service_enhanced import AIServiceEnhanced
        ai_service = AIServiceEnhanced()
        st.success("✅ Using Enhanced AI Service with multiple itinerary options")
        return ai_service
    except Exception as enhanced_error:
        st.warning(f"⚠️ Enhanced AI not available: {str(enhanced_error)[:100]}...")
        
        # Try 2: GenAI SDK
        try:
            from services.ai_service_genai import AIServiceGenAI
            ai_service = AIServiceGenAI()
            st.success("✅ Using Google GenAI SDK")
            return ai_service
        except Exception as genai_error:
            st.warning(f"⚠️ GenAI SDK not available: {str(genai_error)[:100]}...")
            
            # Try 3: Legacy models fallback
            try:
                from services.ai_service_fallback import AIServiceFallback
                ai_service = AIServiceFallback()
                st.success("✅ Using legacy AI models (text-bison/chat-bison)")
                return ai_service
            except Exception as fallback_error:
                st.error(f"❌ No AI models available: {str(fallback_error)}")
                st.stop()
    
    if not ai_service:
        st.error("❌ Failed to initialize any AI service")
        st.stop()
    
    return ai_service

@st.cache_resource
def get_export_service():
    """Initialize export service with caching"""
    from services.export_service import ExportService
    return ExportService()

@st.cache_resource
def get_maps_service():
    """Initialize maps service with caching"""
    cloud_services = setup_google_cloud()
    return MapsService(cloud_services['maps_client'])

# Initialize services as None first
maps_service = None
ai_service = None

def validate_environment_for_cloud():
    """Validate environment variables for Cloud Run deployment"""
    required_vars = [
        'GOOGLE_CLOUD_PROJECT',
        'GOOGLE_MAPS_API_KEY',
        'VERTEXAI_LOCATION'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        st.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        st.error("Please check your environment configuration.")
        st.stop()
    
    # Only check credentials file if running locally (not in Cloud Run)
    if not os.getenv('K_SERVICE'):  # K_SERVICE is set in Cloud Run
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and not os.path.exists(creds_path):
            st.error(f"Credentials file not found at: {creds_path}")
            st.stop()
try:
    # Check if running in Cloud Shell
    is_cloud_shell = os.path.exists('/google/devshell/bashrc') or 'DEVSHELL_GCLOUD_CONFIG' in os.environ
    
    if is_cloud_shell:
        st.info("🌟 Running in Google Cloud Shell - using default credentials")
    else:
        # Validate environment variables for local development
        validate_environment_for_cloud()
        
        # Show credentials path for debugging
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if creds_path and not os.path.exists(creds_path):
            st.error(f"Credentials file not found at: {creds_path}")
            st.stop()
    
    # Initialize services with caching (prevents re-initialization)
    maps_service = get_maps_service()
    ai_service = get_ai_service()
    export_service = get_export_service()
except Exception as e:
    st.error(f"Failed to initialize Google Cloud services: {str(e)}")
    st.info("Please make sure you have set up your Google Cloud credentials correctly.")
    st.stop()



def main():
    st.title("🧠 TravelMind AI - Your Intelligent Travel Companion")
    
    # Sidebar for user inputs
    with st.sidebar:
        st.header("Trip Details")
        
        # Basic inputs
        origin = st.text_input("From", "Delhi")
        destination = st.text_input("To", "Goa")
        start_date = st.date_input("Start Date")
        duration = st.number_input("Number of Days", min_value=1, max_value=30, value=3)
        
        # Transport mode
        transport_mode = st.selectbox(
            "Preferred Mode of Transport",
            ["Flight", "Train", "Bus", "Car"]
        )
        
        # Budget slider
        budget = st.slider("Budget (₹)", 10000, 100000, 25000, step=5000)
        
        # Theme selection
        themes = st.multiselect(
            "Travel Themes",
            ["Heritage", "Nightlife", "Adventure", "Nature", "Luxury", "Family", "Food"]
        )
        
        # Language selection
        language = st.selectbox("Language", ["English", "Hindi", "Telugu", "Tamil"])
        
        # Generate button
        if st.button("Generate Itinerary", type="primary"):
            with st.spinner("🤖 Generating multiple itinerary options..."):
                try:
                    # Check if we have enhanced AI service
                    if hasattr(ai_service, 'generate_multiple_itineraries'):
                        # Generate multiple options
                        options = ai_service.generate_multiple_itineraries(destination, duration, budget, themes)
                        if options:
                            st.session_state.itinerary_options = options
                            st.session_state.selected_itinerary = ai_service._select_best_option(options, budget)
                        else:
                            # Fallback to single itinerary
                            itinerary = generate_itinerary(destination, duration, budget, themes)
                            st.session_state.selected_itinerary = itinerary
                            st.session_state.itinerary_options = [itinerary]
                    else:
                        # Single itinerary generation
                        itinerary = generate_itinerary(destination, duration, budget, themes)
                        st.session_state.selected_itinerary = itinerary
                        st.session_state.itinerary_options = [itinerary]
                    
                    st.session_state.generate_plan = True
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating itinerary: {str(e)}")
                    return
        
        # Load shared itinerary
        st.markdown("---")
        st.subheader("📤 Load Shared Itinerary")
        share_code = st.text_input("Enter share code:", placeholder="e.g., ABC123DEF456")
        if st.button("Load Shared Itinerary") and share_code:
            shared_itinerary = export_service.load_shared_itinerary(share_code.upper())
            if shared_itinerary:
                st.session_state.selected_itinerary = shared_itinerary
                st.session_state.generate_plan = True
                st.success("✅ Shared itinerary loaded successfully!")
                st.rerun()
            else:
                st.error("❌ Invalid share code or itinerary not found")

    # Main content area
    if 'generate_plan' in st.session_state and st.session_state.selected_itinerary is not None:
        # Show itinerary options if available
        if 'itinerary_options' in st.session_state and len(st.session_state.itinerary_options) > 1:
            st.subheader("🎯 Choose Your Preferred Itinerary")
            
            option_cols = st.columns(len(st.session_state.itinerary_options))
            
            for idx, option in enumerate(st.session_state.itinerary_options):
                with option_cols[idx]:
                    st.markdown(f"""
                    **{option.get('budget_type', 'Option')} Plan**  
                    💰 ₹{option.get('total_cost', option.get('budget', 0))}  
                    📊 {len(option.get('daily_plans', []))} days
                    """)
                    
                    if st.button(f"Select {option.get('budget_type', 'This')} Plan", key=f"select_{idx}"):
                        st.session_state.selected_itinerary = option
                        st.success(f"✅ Selected {option.get('budget_type', 'This')} Plan!")
                        st.rerun()
        
        # Display selected itinerary
        display_itinerary(st.session_state.selected_itinerary)
        
        # Natural language modification
        st.markdown("---")
        st.subheader("🗣️ Modify Your Itinerary")
        st.markdown("*Tell us what you'd like to change in plain English*")
        
        modification_request = st.text_area(
            "What would you like to modify?",
            placeholder="e.g., 'Add more adventure activities', 'Replace hotel with budget option', 'Include more local food experiences', 'Change Day 2 afternoon activity'"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔧 Apply Modifications") and modification_request:
                if hasattr(ai_service, 'modify_itinerary'):
                    with st.spinner("🤖 Applying your modifications..."):
                        try:
                            modified_itinerary = ai_service.modify_itinerary(
                                st.session_state.selected_itinerary, 
                                modification_request
                            )
                            st.session_state.selected_itinerary = modified_itinerary
                            st.success("✅ Itinerary modified successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error modifying itinerary: {str(e)}")
                else:
                    st.warning("⚠️ Modification feature requires Enhanced AI Service")
        
        with col2:
            if st.button("🔄 Generate New Options"):
                st.session_state.generate_plan = False
                st.rerun()

def generate_itinerary(destination, duration, budget, themes):
    """Generate travel itinerary using AI service"""
    try:
        itinerary = ai_service.generate_itinerary(destination, duration, budget, themes)
        
        # Validate the returned itinerary
        if not isinstance(itinerary, dict):
            raise ValueError("Invalid itinerary format returned")
        
        if not itinerary.get('daily_plans'):
            raise ValueError("No daily plans in itinerary")
        
        return itinerary
        
    except Exception as e:
        st.error(f"Error generating itinerary: {str(e)}")
        
        # Return a basic fallback itinerary
        daily_budget = budget // duration
        fallback_itinerary = {
            'destination': destination,
            'duration': duration,
            'budget': budget,
            'daily_plans': []
        }
        
        for day in range(1, duration + 1):
            fallback_itinerary['daily_plans'].append({
                'day': day,
                'activities': [
                    {
                        'time': '9:00 AM',
                        'activity': f'Explore popular attractions in {destination}',
                        'cost': daily_budget // 3,
                        'duration': '3 hours'
                    },
                    {
                        'time': '2:00 PM',
                        'activity': f'Visit local markets and restaurants in {destination}',
                        'cost': daily_budget // 3,
                        'duration': '4 hours'
                    },
                    {
                        'time': '7:00 PM',
                        'activity': f'Evening entertainment in {destination}',
                        'cost': daily_budget // 3,
                        'duration': '3 hours'
                    }
                ]
            })
        
        fallback_itinerary['data_sources'] = {
            'influencer_recommendations': 0,
            'youtube_content': 0,
            'template_based': True,
            'ai_powered': False
        }
        
        return fallback_itinerary

def display_itinerary(itinerary):
    if not isinstance(itinerary, dict):
        st.error("Invalid itinerary format. Please try again.")
        return

    # Check if daily_plans exists and is not empty
    if not itinerary.get('daily_plans') or len(itinerary['daily_plans']) == 0:
        st.error("No itinerary data available. Please try generating again.")
        st.info("💡 Tip: Try with a different destination or check your internet connection.")
        return

    # Display overview
    try:
        st.header(f"Your {itinerary.get('duration', '0')}-day trip to {itinerary.get('destination', 'Unknown')}")
        st.subheader(f"Budget: ₹{itinerary.get('budget', '0')}")
        
        # Show data sources if available
        if itinerary.get('data_sources'):
            sources = itinerary['data_sources']
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Influencer Tips", sources.get('influencer_recommendations', 0))
            with col2:
                st.metric("YouTube Videos", sources.get('youtube_content', 0))
            with col3:
                ai_status = "✅ AI Generated" if sources.get('ai_powered') else "📋 Template Based"
                st.info(ai_status)
                
    except Exception as e:
        st.error(f"Error displaying itinerary overview: {str(e)}")
        return

    # Create tabs for each day
    try:
        tabs = st.tabs([f"Day {day['day']}" for day in itinerary['daily_plans']])
    except Exception as e:
        st.error(f"Error creating day tabs: {str(e)}")
        return
    
    # Display daily activities in tabs
    for idx, tab in enumerate(tabs):
        with tab:
            daily_plan = itinerary['daily_plans'][idx]
            
            # Display activities
            for activity in daily_plan['activities']:
                # Special styling for different activity types
                if activity.get('hotel_recommendation'):
                    with st.expander(f"🏨 {activity.get('time', 'Night')}: {activity.get('activity', 'Accommodation')}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Location:** {activity.get('place', 'N/A')}")
                            st.write(f"**Duration:** {activity.get('duration', '8-10 hours')}")
                        with col2:
                            st.write(f"**Cost:** ₹{activity.get('cost', 0)}/night")
                            st.write(f"**Type:** Accommodation")
                        if activity.get('details'):
                            st.write(f"**Details:** {activity['details']}")
                elif activity.get('flight_recommendation'):
                    with st.expander(f"✈️ {activity.get('time', 'Morning')}: {activity.get('activity', 'Flight')}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Destination:** {activity.get('place', 'N/A')}")
                            st.write(f"**Duration:** {activity.get('duration', '2-3 hours')}")
                        with col2:
                            st.write(f"**Cost:** ₹{activity.get('cost', 0)}")
                            st.write(f"**Type:** Flight")
                        if activity.get('details'):
                            st.write(f"**Details:** {activity['details']}")
                elif activity.get('transport_recommendation'):
                    with st.expander(f"🚗 {activity.get('time', 'Morning')}: {activity.get('activity', 'Transport')}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Location:** {activity.get('place', 'N/A')}")
                            st.write(f"**Duration:** {activity.get('duration', '1 hour')}")
                        with col2:
                            st.write(f"**Cost:** ₹{activity.get('cost', 0)}/day")
                            st.write(f"**Type:** Transportation")
                        if activity.get('details'):
                            st.write(f"**Details:** {activity['details']}")
                else:
                    with st.expander(f"{activity.get('time', 'TBD')}: {activity.get('activity', 'Activity')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Duration:** {activity.get('duration', 'TBD')}")
                            st.write(f"**Cost:** ₹{activity.get('cost', 0)}")
                        with col2:
                            if activity.get('place'):
                                st.write(f"**Location:** {activity['place']}")
                        
                        # Show detailed description
                        if activity.get('details'):
                            st.write(f"**Details:** {activity['details']}")
                        
                        # Show recommendations
                        if activity.get('influencer_recommended'):
                            st.info("✨ Recommended by local influencer!")
                            if activity.get('tip'):
                                st.write(f"💡 **Tip:** {activity['tip']}")
                        if activity.get('youtube_recommended'):
                            video_title = activity.get('video_title', 'Travel Video')
                            st.info(f"📺 Featured in: {video_title}")
                            if activity.get('video_id'):
                                st.markdown(f"[Watch Video](https://youtube.com/watch?v={activity['video_id']})")

    # Add a map
    st.subheader("📍 Destinations on Map")
    if maps_service:
        try:
            # Get location coordinates using Maps service
            location_result = maps_service.gmaps.geocode(itinerary['destination'])
            if location_result:
                lat = location_result[0]['geometry']['location']['lat']
                lng = location_result[0]['geometry']['location']['lng']
                
                # Create map centered on destination
                m = folium.Map(location=[lat, lng], zoom_start=13)
                folium.Marker(
                    [lat, lng],
                    popup=itinerary['destination'],
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(m)
                
                # Display map using st_folium
                st.components.v1.html(m._repr_html_(), height=400)
            else:
                st.warning(f"Could not find coordinates for {itinerary['destination']}")
        except Exception as e:
            st.warning(f"Could not load map visualization: {str(e)}")
    else:
        st.warning("Map service is not initialized. Please check your Google Maps API configuration.")

    # Export and Share buttons
    st.markdown("---")
    st.subheader("📤 Export & Share")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📄 Export PDF", type="secondary"):
            with st.spinner("Generating PDF..."):
                pdf_path = export_service.export_to_pdf(itinerary)
                if pdf_path:
                    download_link = export_service.get_download_link(pdf_path)
                    if download_link:
                        st.markdown(download_link, unsafe_allow_html=True)
                        st.success("✅ PDF generated successfully!")
                    else:
                        st.error("❌ Failed to create download link")
                else:
                    st.error("❌ Failed to generate PDF")
    
    with col2:
        if st.button("📋 Export JSON", type="secondary"):
            with st.spinner("Generating JSON..."):
                json_path = export_service.export_to_json(itinerary)
                if json_path:
                    download_link = export_service.get_download_link(json_path)
                    if download_link:
                        st.markdown(download_link, unsafe_allow_html=True)
                        st.success("✅ JSON generated successfully!")
                    else:
                        st.error("❌ Failed to create download link")
                else:
                    st.error("❌ Failed to generate JSON")
    
    with col3:
        if st.button("🔗 Create Share Link", type="secondary"):
            with st.spinner("Creating shareable link..."):
                share_info = export_service.create_shareable_link(itinerary)
                if share_info:
                    st.success("✅ Share link created!")
                    st.code(f"Share Code: {share_info['share_code']}")
                    st.markdown(f"**Share URL:** {share_info['share_url']}")
                    st.info("💡 Others can use this share code to load your itinerary")
                else:
                    st.error("❌ Failed to create share link")
    
    with col4:
        if st.button("🎫 Book Now", type="primary"):
            st.info("🚀 Booking functionality will be integrated with travel partners soon!")
            st.markdown("""
            **Coming Soon:**
            - Hotel bookings via partner platforms
            - Flight/train reservations
            - Activity bookings
            - Local guide connections
            """)

if __name__ == "__main__":
    main()
