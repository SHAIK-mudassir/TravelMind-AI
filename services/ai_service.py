from google import genai
from google.genai.types import GenerateContentConfig
from google.cloud import bigquery
import json
import os
from datetime import datetime, timedelta
from services.youtube_service import YouTubeService

class AIServiceGenAI:
    """AI service using the new Google GenAI SDK"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        try:
            # Initialize the new GenAI client with project configuration
            self.client = genai.Client(
                project=self.project_id,
                location=os.getenv('VERTEXAI_LOCATION', 'us-central1')
            )
            
            # Test available models
            available_models = [
                "gemini-2.0-flash-exp",
                "gemini-1.5-flash",
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            self.model_name = None
            for model in available_models:
                try:
                    # Test the model with a simple request
                    test_response = self.client.models.generate_content(
                        model=model,
                        contents="Hello",
                        config=GenerateContentConfig(
                            candidate_count=1,
                            max_output_tokens=10
                        )
                    )
                    if test_response and test_response.candidates:
                        self.model_name = model
                        print(f"✅ Successfully initialized GenAI model: {model}")
                        break
                except Exception as e:
                    print(f"❌ Model {model} not available: {str(e)[:100]}...")
                    continue
            
            if not self.model_name:
                raise Exception("No GenAI models are available")
            
            self.bq_client = bigquery.Client()
            print(f"✅ GenAI service initialized with model: {self.model_name}")
                
        except Exception as e:
            print(f"Detailed error during GenAI service initialization: {str(e)}")
            raise Exception(f"Failed to initialize GenAI service: {str(e)}")
        
    def _get_influencer_recommendations(self, destination):
        """Get influencer recommendations from BigQuery"""
        if not self.bq_client:
            return []
            
        query = f"""
        SELECT 
            platform,
            influencer_name,
            place_name,
            recommendation,
            category,
            budget_range,
            best_time,
            latitude,
            longitude
        FROM `{self.project_id}.travel_data.influencer_recommendations`
        WHERE LOWER(destination) = LOWER(@destination)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("destination", "STRING", destination)
            ]
        )
        
        try:
            results = self.bq_client.query(query, job_config=job_config).result()
            recommendations = []
            for row in results:
                recommendations.append({
                    'platform': row.platform,
                    'influencer': row.influencer_name,
                    'place': row.place_name,
                    'tip': row.recommendation,
                    'category': row.category,
                    'budget_range': row.budget_range,
                    'best_time': row.best_time,
                    'coordinates': {
                        'lat': row.latitude,
                        'lng': row.longitude
                    }
                })
            return recommendations
        except Exception as e:
            print(f"Error fetching influencer data: {str(e)}")
            return []
            
    def generate_itinerary(self, destination, duration, budget, themes):
        """Generate an itinerary using Google GenAI"""
        try:
            # Create basic itinerary structure
            itinerary = {
                'destination': destination,
                'duration': duration,
                'budget': budget,
                'daily_plans': []
            }

            # Get influencer recommendations from BigQuery
            try:
                influencer_recommendations = self._get_influencer_recommendations(destination)
                print(f"📱 Found {len(influencer_recommendations)} influencer recommendations")
            except Exception as e:
                print(f"Error getting influencer recommendations: {str(e)}")
                influencer_recommendations = []
            
            # Get YouTube travel content
            try:
                youtube_service = YouTubeService()
                youtube_content = youtube_service.get_travel_content(destination)
                print(f"📺 Found {len(youtube_content)} YouTube recommendations")
            except Exception as e:
                print(f"Error getting YouTube content: {str(e)}")
                youtube_content = []
            
            # Combine recommendations
            all_recommendations = {
                'influencer_recommendations': influencer_recommendations,
                'youtube_content': youtube_content
            }
            
            # Create AI prompt
            prompt = self._create_prompt(destination, duration, budget, themes, all_recommendations)
            
            try:
                # Generate itinerary using Google GenAI
                print(f"🤖 Generating itinerary using {self.model_name}...")
                
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=GenerateContentConfig(
                        candidate_count=1,
                        max_output_tokens=2048,
                        temperature=0.7,
                        top_p=0.8,
                        top_k=40
                    )
                )
                
                if not response or not response.candidates:
                    raise Exception("Empty response from GenAI model")
                
                # Extract text from response
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if part.text:
                        response_text += part.text
                
                if not response_text:
                    raise Exception("No text content in GenAI response")
                    
                print(f"✅ Received response from GenAI model, length: {len(response_text)}")
                
                # Parse and structure the response
                ai_response = self._structure_ai_response(response_text, destination, duration, budget, all_recommendations)
                if ai_response:
                    itinerary.update(ai_response)
                    
            except Exception as e:
                print(f"Error in GenAI generation: {str(e)}")
                # Return basic itinerary with sample structure if AI fails
                itinerary['daily_plans'] = [
                    {
                        'day': 1,
                        'activities': [
                            {
                                'time': 'Morning',
                                'activity': f'Explore {destination} attractions',
                                'cost': budget // duration // 3,
                                'duration': '3 hours'
                            }
                        ]
                    }
                ]
            
            return itinerary
            
        except Exception as e:
            print(f"Error generating itinerary: {str(e)}")
            raise e

    def _create_prompt(self, destination, duration, budget, themes, recommendations):
        """Create prompt for AI generation"""
        theme_str = ', '.join(themes) if themes else 'general sightseeing'
        daily_budget = budget / duration
        
        # Process influencer recommendations
        influencer_tips = []
        if recommendations.get('influencer_recommendations'):
            influencer_tips.extend([
                f"- {rec['place']}: {rec['tip']} (Best time: {rec['best_time']}, Budget: {rec['budget_range']})"
                for rec in recommendations['influencer_recommendations']
            ])
            
        # Add YouTube content
        youtube_insights = []
        if recommendations.get('youtube_content'):
            for video in recommendations['youtube_content']:
                if video.get('locations'):
                    for location in video['locations']:
                        youtube_insights.append(f"- {location} (Featured in popular travel vlog: {video['title']})")
                        
        all_tips = "Local Expert Recommendations:\n" + '\n'.join(influencer_tips) if influencer_tips else "No local recommendations available."
        youtube_content = "\nTravel Vlog Highlights:\n" + '\n'.join(youtube_insights) if youtube_insights else ""
        
        prompt = f"""Create a detailed {duration}-day travel itinerary for {destination} with the following parameters:

Budget: ₹{budget} total (₹{daily_budget:.0f} per day)
Travel Themes: {theme_str}

{all_tips}
{youtube_content}

Please create a comprehensive day-by-day itinerary that:
1. Spans exactly {duration} days with multiple activities each day
2. Includes for each day:
   - Morning activities (8 AM - 12 PM)
   - Afternoon activities (12 PM - 4 PM)
   - Evening activities (4 PM - 8 PM)
   - Night activities if relevant (8 PM onwards)
3. For each activity specify:
   - Exact time slot
   - Estimated duration
   - Approximate cost
   - Transportation method
   - Any special tips or local insights
4. Incorporates the local expert recommendations where they fit the themes
5. Balances the daily budget to stay within ₹{daily_budget:.0f}
6. Considers the best time to visit each place
7. Includes popular local food recommendations
8. Suggests photo opportunities and viewpoints

Format each day as:
Day X:
[Time]: [Activity] - [Duration] - ₹[Cost]
[Description and tips]

Remember to:
- Space out activities to allow for travel time
- Include meal times and recommendations
- Mix popular attractions with hidden gems
- Consider local transportation options
- Add relevant local cultural insights"""
        
        return prompt

    def _structure_ai_response(self, ai_text, destination, duration, budget, recommendations):
        """Structure the AI response into a formatted itinerary"""
        try:
            # Initialize the structured itinerary
            itinerary = {
                "destination": destination,
                "duration": duration,
                "budget": budget,
                "daily_plans": []
            }
            
            # Process AI response and extract daily plans
            # Split by days and parse activities
            day_splits = ai_text.split("Day")
            
            for day_num, day_text in enumerate(day_splits[1:], 1):
                activities = []
                current_activity = {}
                
                # Parse activities from the day's text
                lines = day_text.strip().split('\n')
                for line in lines[1:]:  # Skip the day number line
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Try to extract time and activity
                    if ':' in line:
                        # Save previous activity if exists
                        if current_activity:
                            activities.append(current_activity)
                            current_activity = {}
                            
                        # Parse new activity
                        time_part = line.split(':')[0].strip()
                        activity_part = ':'.join(line.split(':')[1:]).strip()
                        
                        current_activity = {
                            "time": time_part,
                            "activity": activity_part,
                            "cost": self._extract_cost(line),
                            "duration": self._extract_duration(line)
                        }
                        
                        # Check if this activity matches any influencer recommendations
                        if recommendations.get('influencer_recommendations'):
                            for rec in recommendations['influencer_recommendations']:
                                if rec['place'].lower() in activity_part.lower():
                                    current_activity["influencer_recommended"] = True
                                    current_activity["tip"] = rec['tip']
                                    break
                                    
                        # Check if this activity matches any YouTube recommendations
                        if recommendations.get('youtube_content'):
                            for video in recommendations['youtube_content']:
                                if video.get('locations'):
                                    for location in video['locations']:
                                        if location.lower() in activity_part.lower():
                                            current_activity["youtube_recommended"] = True
                                            current_activity["video_title"] = video['title']
                                            current_activity["video_id"] = video['video_id']
                                            break
                
                # Add the last activity
                if current_activity:
                    activities.append(current_activity)
                
                # Add the day's plan
                if activities:
                    itinerary["daily_plans"].append({
                        "day": day_num,
                        "activities": activities
                    })
            
            return itinerary
            
        except Exception as e:
            print(f"Error structuring AI response: {str(e)}")
            return None
            
    def _extract_cost(self, text):
        """Extract cost from text"""
        import re
        cost_match = re.search(r'₹(\d+)', text)
        return int(cost_match.group(1)) if cost_match else 0
        
    def _extract_duration(self, text):
        """Extract duration from text"""
        import re
        duration_match = re.search(r'(\d+)\s*(hour|hr|minute|min)s?', text.lower())
        if duration_match:
            amount = int(duration_match.group(1))
            unit = duration_match.group(2)
            if 'hour' in unit or 'hr' in unit:
                return f"{amount} hours"
            else:
                return f"{amount} minutes"
        return "1 hour"  # default duration
