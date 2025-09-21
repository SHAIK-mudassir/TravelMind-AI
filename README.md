# 🌍 AI Travel Planner - Hackathon Project

## 🎯 Project Overview

An AI-powered personalized trip planner that dynamically creates end-to-end itineraries tailored to individual budgets, interests, and real-time conditions with seamless booking capabilities. Built using Google Cloud technologies for the hackathon.

## 🚀 Key Features

### Core Capabilities
- **🤖 AI-Powered Itineraries**: Uses Google's Gemini 1.0 Pro via Vertex AI to generate personalized travel plans
- **💰 Budget-Aware Planning**: Intelligent budget distribution across activities and days
- **🎨 Theme-Based Recommendations**: Heritage, Adventure, Nature, Nightlife, Food, Family, Luxury
- **🗺️ Interactive Maps**: Real-time location visualization using Google Maps API
- **🌐 Multi-Language Support**: English, Hindi, Telugu, Tamil

### 🌟 Unique Selling Points (USP)

#### 1. **Influencer-Powered Recommendations** 
- Integration with social media influencer content stored in BigQuery
- Real recommendations from travel influencers for authentic local experiences
- Platform-specific insights (Instagram, YouTube, etc.)
- Budget ranges and best visiting times from local experts

#### 2. **YouTube Travel Content Integration**
- Automatic extraction of travel recommendations from popular YouTube vlogs
- Links to relevant travel videos for visual inspiration
- Location-specific content from verified travel creators
- Real-time content caching for performance

#### 3. **Real-Time Adaptive Planning**
- Weather-based activity adjustments
- Event-based recommendations
- Last-minute booking capabilities
- Dynamic itinerary modifications

#### 4. **One-Click Booking System** (Planned)
- Integrated booking through EMT inventory
- Seamless payment processing
- Complete end-to-end travel booking experience

## 🛠️ Tech Stack

### Google Cloud Technologies (As Required)
- **Vertex AI**: Gemini 1.0 Pro for AI-powered itinerary generation
- **BigQuery**: Data warehouse for influencer recommendations and analytics
- **Google Maps API**: Location services and map visualization
- **Firebase**: User authentication and real-time data (planned)
- **Cloud Translation API**: Multi-language support

### Additional Technologies
- **Frontend**: Streamlit for rapid prototyping and demo
- **Backend**: Python with Google Cloud SDKs
- **Data Processing**: Pandas for data manipulation
- **Visualization**: Folium for interactive maps, Plotly for charts

## 📁 Project Structure

```
TravelPlanner/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── .env.template                   # Environment variables template
├── SETUP_GUIDE.md                 # Detailed setup instructions
├── README.md                       # This file
│
├── config/
│   └── google_cloud_setup.py      # Google Cloud configuration
│
├── services/
│   ├── ai_service.py              # Vertex AI Gemini integration
│   ├── maps_service.py            # Google Maps API wrapper
│   └── youtube_service.py         # YouTube content integration
│
├── utils/
│   ├── setup_bigquery.py          # BigQuery table creation
│   ├── populate_sample_data.py    # Sample data insertion
│   └── test_complete_setup.py     # Comprehensive testing
│
└── data/
    └── influencer_data.json       # Sample influencer data
```

## 🚀 Quick Start

### 1. Prerequisites
- Google Cloud Project with billing enabled
- Google Cloud credits (for hackathon)
- Python 3.8+

### 2. Setup Environment
```bash
# Clone and navigate to project
cd TravelPlanner

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env
# Edit .env with your actual values
```

### 3. Configure Google Cloud
```bash
# Enable required APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable maps-backend.googleapis.com
gcloud services enable youtube.googleapis.com

# Create service account with required roles:
# - Vertex AI User
# - BigQuery Data Editor
# - BigQuery Job User
```

### 4. Initialize Database
```bash
# Create BigQuery tables
python utils/setup_bigquery.py

# Populate with sample data
python utils/populate_sample_data.py
```

### 5. Test Setup
```bash
# Run comprehensive tests
python utils/test_complete_setup.py
```

### 6. Launch Application
```bash
# Start the Streamlit app
streamlit run app.py
```

## 🎨 User Experience Flow

1. **Input Travel Preferences**
   - Origin and destination
   - Travel dates and duration
   - Budget range
   - Preferred themes
   - Language preference

2. **AI Processing**
   - Gemini analyzes preferences
   - Fetches influencer recommendations from BigQuery
   - Integrates YouTube travel content
   - Generates personalized itinerary

3. **Interactive Itinerary**
   - Day-by-day activity breakdown
   - Cost estimates and time slots
   - Influencer tips and recommendations
   - YouTube video links for inspiration
   - Interactive map visualization

4. **Booking & Export** (Planned)
   - One-click booking integration
   - PDF export functionality
   - Email sharing capabilities

## 🌟 Hackathon Highlights

### Innovation Points
- **First-of-its-kind** influencer integration in travel planning
- **Real-time content** from social media platforms
- **AI-driven personalization** using latest Gemini models
- **Complete Google Cloud ecosystem** utilization

### Technical Excellence
- **Scalable architecture** using BigQuery for data storage
- **Real-time processing** with caching mechanisms
- **Multi-modal AI** combining text and location data
- **Responsive design** for mobile and desktop

### Business Impact
- **Addresses real pain points** in travel planning
- **Monetization ready** with booking integration
- **Scalable to global markets** with multi-language support
- **Data-driven insights** for travel industry

## 🔧 Configuration

### Required Environment Variables
```env
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
GOOGLE_MAPS_API_KEY=your-maps-api-key
YOUTUBE_API_KEY=your-youtube-api-key  # Optional
```

### Google Cloud APIs to Enable
- Vertex AI API
- BigQuery API
- Maps JavaScript API
- Maps Places API
- Maps Geocoding API
- YouTube Data API v3
- Cloud Translation API

## 📊 Sample Data

The project includes sample influencer recommendations for popular Indian destinations:
- **Goa**: Beach activities, heritage sites, adventure sports
- **Delhi**: Historical monuments, street food, cultural experiences
- **Mumbai**: Nightlife, heritage, local attractions
- **Jaipur**: Royal palaces, heritage walks, cultural tours
- **Kerala**: Backwaters, tea gardens, nature experiences

## 🚧 Future Enhancements

### Phase 2 Features
- **Real-time booking** integration with travel APIs
- **Payment gateway** integration
- **Mobile app** development
- **Advanced ML models** for better personalization

### Phase 3 Features
- **Social sharing** capabilities
- **Group travel** planning
- **Offline map** support
- **AR/VR** destination previews

## 🤝 Contributing

This is a hackathon project, but contributions are welcome:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is created for hackathon purposes. Please respect Google Cloud terms of service and API usage limits.

## 🆘 Support

For setup issues:
1. Check `SETUP_GUIDE.md` for detailed instructions
2. Run `python utils/test_complete_setup.py` for diagnostics
3. Verify Google Cloud API enablement and permissions

## 🏆 Hackathon Submission

**Team**: [Your Team Name]  
**Challenge**: Personalized Trip Planner with AI  
**Tech Stack**: Google Cloud (Vertex AI, BigQuery, Maps API)  
**Unique Features**: Influencer recommendations, YouTube integration, Real-time adaptations  

---

*Built with ❤️ using Google Cloud technologies for the hackathon*
