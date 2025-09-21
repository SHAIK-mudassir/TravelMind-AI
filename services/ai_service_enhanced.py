from google import genai
from google.genai.types import GenerateContentConfig
from google.cloud import bigquery
import json
import os
import random
import re
from datetime import datetime, timedelta
from services.youtube_service import YouTubeService

class AIServiceEnhanced:
    """Enhanced AI service with multiple itinerary generation and natural language processing"""
    
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        if not self.project_id:
            raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set")
        
        try:
            # Initialize the GenAI client
            self.client = genai.Client(
                project=self.project_id,
                location=os.getenv('VERTEXAI_LOCATION', 'us-central1')
            )
            
            # Test available models
            available_models = [
                "gemini-2.5-flash",
                "gemini-1.5-flash", 
                "gemini-1.5-pro",
                "gemini-pro"
            ]
            
            self.model_name = None
            for model in available_models:
                try:
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
                        print(f"✅ Successfully initialized Enhanced AI with model: {model}")
                        break
                except Exception as e:
                    continue
            
            if not self.model_name:
                raise Exception("No GenAI models are available")
            
            self.bq_client = bigquery.Client()
                
        except Exception as e:
            print(f"Enhanced AI service initialization failed: {str(e)}")
            raise Exception(f"Failed to initialize Enhanced AI service: {str(e)}")
    
    def generate_multiple_itineraries(self, destination, duration, budget, themes, num_options=3):
        """Generate multiple itinerary options with varying budgets and styles"""
        try:
            print(f"🎯 Generating {num_options} itinerary options for {destination}")
            
            # Get real data
            influencer_recommendations = self._get_influencer_recommendations(destination)
            youtube_content = self._get_youtube_content(destination)
            
            # Create budget variations
            budget_variations = [
                {"budget": int(budget * 0.8), "type": "Budget-Friendly", "style": "economical"},
                {"budget": budget, "type": "Standard", "style": "balanced"},
                {"budget": int(budget * 1.3), "type": "Premium", "style": "luxury"}
            ]
            
            itinerary_options = []
            
            for i, budget_option in enumerate(budget_variations):
                try:
                    print(f"  📋 Generating {budget_option['type']} option (₹{budget_option['budget']})")
                    
                    # Create specific prompt for this budget/style
                    prompt = self._create_enhanced_prompt(
                        destination, duration, budget_option['budget'], 
                        themes, budget_option['style'], influencer_recommendations, youtube_content
                    )
                    
                    # Generate with Gemini
                    response = self._generate_with_gemini(prompt)
                    
                    if response:
                        print(f"    📝 Gemini response length: {len(response)} characters")
                        print(f"    📝 First 200 chars: {response[:200]}...")
                        
                        itinerary = self._parse_gemini_response(
                            response, destination, duration, budget_option['budget'], 
                            budget_option['type'], influencer_recommendations, youtube_content
                        )
                        if itinerary and itinerary.get('daily_plans'):
                            itinerary_options.append(itinerary)
                            print(f"    ✅ Successfully parsed {budget_option['type']} itinerary")
                        else:
                            print(f"    ❌ Failed to parse {budget_option['type']} itinerary - no daily plans")
                    else:
                        print(f"    ❌ No response from Gemini for {budget_option['type']} option")
                    
                except Exception as e:
                    print(f"    ❌ Failed to generate {budget_option['type']} option: {str(e)}")
                    continue
            
            # If no AI options generated, create fallback options
            if not itinerary_options:
                print("🔄 Creating fallback options using templates")
                itinerary_options = self._create_fallback_options(
                    destination, duration, budget, themes, influencer_recommendations, youtube_content
                )
            
            return itinerary_options
            
        except Exception as e:
            print(f"Error generating multiple itineraries: {str(e)}")
            return []
    
    def generate_itinerary(self, destination, duration, budget, themes):
        """Main itinerary generation method - returns best option from multiple choices"""
        options = self.generate_multiple_itineraries(destination, duration, budget, themes)
        
        if not options:
            raise Exception("Failed to generate any itinerary options")
        
        # Select best option based on budget
        best_option = self._select_best_option(options, budget)
        best_option['all_options'] = options  # Store all options for user choice
        
        return best_option
    
    def modify_itinerary(self, current_itinerary, user_request):
        """Modify existing itinerary based on natural language input using AI intent analysis"""
        try:
            print(f"🔧 Processing modification request: {user_request}")
            
            # Step 1: Use Gemini to analyze user intent and extract modification parameters
            intent_analysis = self._analyze_modification_intent(current_itinerary, user_request)
            print(f"🧠 Intent analysis: {intent_analysis}")
            
            # Step 2: Generate new itinerary with updated context based on intent
            modified_itinerary = self._regenerate_with_updated_context(current_itinerary, intent_analysis, user_request)
            
            modified_itinerary['modification_applied'] = user_request
            print(f"✅ Successfully modified itinerary using AI intent analysis")
            return modified_itinerary
                
        except Exception as e:
            print(f"❌ Error modifying itinerary: {str(e)}")
            # Fallback to original itinerary if everything fails
            return current_itinerary
    
    def _analyze_modification_intent(self, current_itinerary, user_request):
        """Use Gemini to analyze user intent and extract modification parameters"""
        current_summary = self._summarize_current_itinerary(current_itinerary)
        
        intent_prompt = f"""
        Analyze this travel itinerary modification request and extract the key parameters for regeneration.
        
        CURRENT ITINERARY SUMMARY:
        {current_summary}
        
        USER MODIFICATION REQUEST: "{user_request}"
        
        Please analyze the user's intent and provide a structured response with these parameters:
        
        1. MODIFICATION_TYPE: (redistribute_activities, add_theme, change_budget, modify_day, change_accommodation, add_activities, remove_activities, change_focus)
        2. SPECIFIC_CHANGES: What exactly needs to be changed
        3. NEW_THEMES: Any new themes to add (adventure, food, culture, nature, luxury, budget, etc.)
        4. BUDGET_ADJUSTMENT: (increase, decrease, maintain) and percentage if applicable
        5. DAY_FOCUS: Specific day number if mentioned, or "all" for general changes
        6. ACTIVITY_DISTRIBUTION: (even, front_loaded, back_loaded, maintain) 
        7. ACCOMMODATION_PREFERENCE: (budget, standard, luxury, maintain)
        8. ADDITIONAL_CONTEXT: Any other specific requirements
        
        Respond in this exact format:
        MODIFICATION_TYPE: [type]
        SPECIFIC_CHANGES: [description]
        NEW_THEMES: [themes separated by commas]
        BUDGET_ADJUSTMENT: [adjustment]
        DAY_FOCUS: [day or all]
        ACTIVITY_DISTRIBUTION: [distribution]
        ACCOMMODATION_PREFERENCE: [preference]
        ADDITIONAL_CONTEXT: [context]
        """
        
        response = self._generate_with_gemini(intent_prompt)
        return self._parse_intent_response(response) if response else {}
    
    def _summarize_current_itinerary(self, itinerary):
        """Create a concise summary of the current itinerary"""
        summary = f"Destination: {itinerary['destination']}\n"
        summary += f"Duration: {itinerary['duration']} days\n"
        summary += f"Budget: ₹{itinerary['budget']}\n"
        summary += f"Budget Type: {itinerary.get('budget_type', 'Standard')}\n\n"
        
        for day_plan in itinerary['daily_plans']:
            activity_count = len([a for a in day_plan['activities'] 
                                if not a.get('hotel_recommendation') and not a.get('flight_recommendation')])
            summary += f"Day {day_plan['day']}: {activity_count} activities\n"
        
        return summary
    
    def _parse_intent_response(self, response):
        """Parse the structured intent analysis response"""
        intent = {}
        if not response:
            return intent
            
        lines = response.strip().split('\n')
        for line in lines:
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                intent[key] = value
        
        return intent
    
    def _regenerate_with_updated_context(self, original_itinerary, intent_analysis, user_request):
        """Regenerate itinerary with updated context based on intent analysis"""
        print(f"🔄 Regenerating itinerary with updated context")
        
        # Extract parameters from intent analysis
        modification_type = intent_analysis.get('modification_type', '')
        new_themes = intent_analysis.get('new_themes', '').split(',') if intent_analysis.get('new_themes') else []
        new_themes = [theme.strip() for theme in new_themes if theme.strip()]
        
        budget_adjustment = intent_analysis.get('budget_adjustment', 'maintain')
        accommodation_pref = intent_analysis.get('accommodation_preference', 'maintain')
        
        # Calculate adjusted budget
        adjusted_budget = original_itinerary['budget']
        if 'increase' in budget_adjustment.lower():
            adjusted_budget = int(adjusted_budget * 1.2)  # 20% increase
        elif 'decrease' in budget_adjustment.lower():
            adjusted_budget = int(adjusted_budget * 0.8)  # 20% decrease
        
        # Determine budget type based on accommodation preference
        if accommodation_pref == 'budget':
            budget_type = 'Budget-Friendly'
        elif accommodation_pref == 'luxury':
            budget_type = 'Premium'
        else:
            budget_type = original_itinerary.get('budget_type', 'Standard')
        
        # Create enhanced prompt with modification context
        modification_context = f"""
        MODIFICATION REQUEST: {user_request}
        MODIFICATION TYPE: {modification_type}
        SPECIFIC CHANGES NEEDED: {intent_analysis.get('specific_changes', 'General improvements')}
        FOCUS AREAS: {', '.join(new_themes) if new_themes else 'Maintain current themes'}
        BUDGET ADJUSTMENT: {budget_adjustment}
        ACCOMMODATION LEVEL: {accommodation_pref}
        ACTIVITY DISTRIBUTION: {intent_analysis.get('activity_distribution', 'maintain')}
        """
        
        # Generate new itinerary using the enhanced AI service with modification context
        try:
            # Create enhanced prompt that includes modification context
            enhanced_prompt = self._create_modification_prompt(
                original_itinerary['destination'],
                original_itinerary['duration'],
                adjusted_budget,
                budget_type,
                new_themes if new_themes else ['General'],
                modification_context,
                original_itinerary
            )
            
            # Generate with Gemini
            response = self._generate_with_gemini(enhanced_prompt)
            
            if response:
                # Parse the response
                modified_itinerary = self._parse_gemini_response(
                    response,
                    original_itinerary['destination'],
                    original_itinerary['duration'],
                    adjusted_budget,
                    budget_type,
                    [], []  # No additional recommendations for modifications
                )
                
                # If parsing fails, use enhanced fallback
                if not modified_itinerary or not modified_itinerary.get('daily_plans'):
                    print("🔄 Using enhanced fallback for modification")
                    modified_itinerary = self._create_enhanced_fallback_plans(
                        original_itinerary['destination'],
                        original_itinerary['duration'],
                        adjusted_budget,
                        budget_type
                    )
                    modified_itinerary = {
                        'destination': original_itinerary['destination'],
                        'duration': original_itinerary['duration'],
                        'budget': adjusted_budget,
                        'budget_type': budget_type,
                        'daily_plans': modified_itinerary
                    }
                
                return modified_itinerary
            else:
                raise Exception("No response from Gemini")
            
        except Exception as e:
            print(f"❌ Error in regeneration: {str(e)}")
            return original_itinerary
    
    def _create_modification_prompt(self, destination, duration, budget, budget_type, themes, modification_context, original_itinerary):
        """Create a specialized prompt for itinerary modification"""
        theme_str = ', '.join(themes) if themes else 'general exploration'
        daily_budget = budget / duration
        
        # Get current itinerary summary for reference
        current_summary = self._itinerary_to_text(original_itinerary)
        
        prompt = f"""
        You are an expert travel planner. I need you to modify an existing travel itinerary based on specific user feedback.
        
        ORIGINAL ITINERARY:
        {current_summary}
        
        MODIFICATION REQUIREMENTS:
        {modification_context}
        
        NEW PARAMETERS:
        - Destination: {destination}
        - Duration: {duration} days
        - Budget: ₹{budget} (₹{daily_budget:.0f} per day)
        - Style: {budget_type}
        - Themes: {theme_str}
        
        INSTRUCTIONS:
        1. Analyze the user's modification request carefully
        2. Create a NEW itinerary that addresses their specific concerns
        3. Keep the same destination and duration
        4. Adjust activities, timing, and budget allocation based on their feedback
        5. Maintain the quality and completeness of the original itinerary
        6. Include hotels, transportation, and activities as appropriate
        
        FORMAT EXACTLY LIKE THIS:
        
        Day 1:
        9:00 AM: Visit Charminar - Historic monument and bustling market (₹200, 3 hours)
        Location: Charminar, Old City
        Details: Explore the iconic 16th-century monument and surrounding Laad Bazaar for traditional shopping
        
        1:00 PM: Lunch at Paradise Restaurant - Famous Hyderabadi Biryani (₹800, 2 hours)
        Location: Paradise Restaurant, Secunderabad
        Details: Authentic Hyderabadi cuisine experience with world-famous biryani
        
        [Continue for all days...]
        
        IMPORTANT:
        - Address the specific modification request in your new itinerary
        - Ensure activities are distributed appropriately based on user feedback
        - Include realistic costs and timing
        - Provide detailed descriptions for each activity
        - Include accommodation and transportation recommendations
        """
        
        return prompt
    
    # Note: Old hardcoded modification methods removed in favor of AI-powered intent analysis
    # The system now uses Gemini to understand user intent and regenerate itineraries accordingly
    
    def _extract_attractions_from_text(self, response_text, destination):
        """Extract attractions from Gemini response text"""
        attractions = []
        
        # Common attraction patterns
        patterns = [
            r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'explore\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Fort|Temple|Beach|Market|Palace|Museum)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, response_text, re.IGNORECASE)
            for match in matches:
                clean_match = match.strip()
                if len(clean_match) > 3 and len(clean_match) < 30:
                    attractions.append(clean_match)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_attractions = []
        for attraction in attractions:
            if attraction.lower() not in seen:
                seen.add(attraction.lower())
                unique_attractions.append(attraction)
        
        # If no attractions found, use destination-specific defaults
        if not unique_attractions:
            if destination.lower() == 'hyderabad':
                attractions = ['Charminar', 'Golconda Fort', 'Hussain Sagar Lake', 'Ramoji Film City', 'Birla Mandir', 'Salar Jung Museum']
            elif destination.lower() == 'goa':
                attractions = ['Baga Beach', 'Fort Aguada', 'Old Goa Churches', 'Anjuna Beach', 'Dudhsagar Falls', 'Palolem Beach']
            else:
                attractions = [f'{destination} City Center', f'{destination} Market', f'{destination} Heritage Sites']
        
        return attractions[:9]  # Limit to 9 attractions (3 per day for 3 days)
    
    def _create_enhanced_prompt(self, destination, duration, budget, themes, style, influencer_recs, youtube_content):
        """Create detailed prompt for Gemini generation"""
        theme_str = ', '.join(themes) if themes else 'general exploration'
        daily_budget = budget / duration
        
        # Process recommendations
        influencer_tips = []
        if influencer_recs:
            for rec in influencer_recs[:5]:  # Limit to top 5
                influencer_tips.append(f"- {rec['place']}: {rec['tip']} (Budget: {rec['budget_range']}, Best time: {rec['best_time']})")
        
        youtube_insights = []
        if youtube_content:
            for video in youtube_content[:3]:  # Limit to top 3
                if video.get('locations'):
                    for location in video['locations'][:2]:
                        youtube_insights.append(f"- {location} (Featured in: {video['title']})")
        
        prompt = f"""
        Create a detailed {duration}-day {style} travel itinerary for {destination}.
        
        REQUIREMENTS:
        - Total Budget: ₹{budget} (₹{daily_budget:.0f} per day)
        - Style: {style.title()} (adjust luxury level accordingly)
        - Themes: {theme_str}
        
        LOCAL EXPERT RECOMMENDATIONS:
        {chr(10).join(influencer_tips) if influencer_tips else "No local recommendations available"}
        
        POPULAR ATTRACTIONS (from travel vlogs):
        {chr(10).join(youtube_insights) if youtube_insights else "No video recommendations available"}
        
        FORMAT EXACTLY LIKE THIS:
        
        Day 1:
        9:00 AM: Visit Anjuna Beach - Enjoy sunrise and morning walk (₹200, 3 hours)
        Location: Anjuna Beach, North Goa
        Details: Beautiful sunrise views, morning yoga, beach cafes for breakfast
        
        1:00 PM: Explore Fort Aguada - Historical Portuguese fort tour (₹300, 2 hours)  
        Location: Fort Aguada, Candolim
        Details: 17th-century fort, lighthouse, panoramic sea views
        
        6:00 PM: Sunset at Baga Beach - Beach activities and dinner (₹800, 4 hours)
        Location: Baga Beach, North Goa
        Details: Water sports, beach shacks, famous nightlife area
        
        Day 2:
        [Continue same format for all {duration} days]
        
        COST GUIDELINES ({style}):
        - Economical: Activities ₹100-500, Food ₹200-400, Hotels ₹1000-2000
        - Balanced: Activities ₹300-800, Food ₹400-800, Hotels ₹2000-4000  
        - Luxury: Activities ₹500-1500, Food ₹800-2000, Hotels ₹4000-8000
        
        Include specific place names, exact costs in ₹, and detailed descriptions for each activity.
        """
        
        return prompt
    
    def _generate_with_gemini(self, prompt):
        """Generate content using Gemini with rate limiting"""
        try:
            import time
            time.sleep(1)  # Rate limiting
            
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=GenerateContentConfig(
                    candidate_count=1,
                    max_output_tokens=2048,
                    temperature=0.8,
                    top_p=0.9
                )
            )
            
            if response and response.candidates:
                response_text = ""
                for part in response.candidates[0].content.parts:
                    if part.text:
                        response_text += part.text
                return response_text
            
            return None
            
        except Exception as e:
            print(f"Gemini generation error: {str(e)}")
            return None
    
    def _parse_gemini_response(self, response_text, destination, duration, budget, budget_type, influencer_recs, youtube_content):
        """Parse Gemini response into structured itinerary"""
        try:
            print(f"    🔍 Parsing response for {budget_type}: {len(response_text)} chars")
            
            # Extract daily activities using regex patterns
            daily_plans = []
            
            # Try multiple parsing approaches
            # Approach 1: Look for "Day X" patterns
            day_pattern = r'Day\s*(\d+)[:.]?\s*(.*?)(?=Day\s*\d+|$)'
            day_matches = re.findall(day_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            print(f"    📋 Found {len(day_matches)} day matches using Day pattern")
            
            if day_matches:
                for day_num, day_content in day_matches:
                    if int(day_num) > duration:
                        break
                        
                    activities = self._extract_activities_from_text(day_content, influencer_recs, youtube_content)
                    
                    if activities:
                        daily_plans.append({
                            'day': int(day_num),
                            'activities': activities
                        })
                        print(f"      ✅ Day {day_num}: {len(activities)} activities")
                    else:
                        print(f"      ❌ Day {day_num}: No activities extracted")
            
            # Approach 2: If no structured days found, use enhanced fallback with hotels/transport
            if not daily_plans:
                print(f"    🔄 No structured days found, using enhanced fallback with hotels/transport")
                daily_plans = self._create_enhanced_fallback_plans(
                    destination, duration, budget, budget_type
                )
            
            # Approach 3: If still no plans, use enhanced fallback
            if not daily_plans:
                print(f"    🔄 Using enhanced fallback for {destination}")
                daily_plans = self._create_enhanced_fallback_plans(destination, duration, budget, budget_type)
            
            # Calculate total cost
            total_cost = sum(
                sum(activity.get('cost', 0) for activity in day['activities'])
                for day in daily_plans
            )
            
            result = {
                'destination': destination,
                'duration': duration,
                'budget': budget,
                'budget_type': budget_type,
                'total_cost': total_cost,
                'daily_plans': daily_plans,
                'ai_generated': True,
                'data_sources': {
                    'gemini_ai': True,
                    'influencer_recs': len(influencer_recs) if influencer_recs else 0,
                    'youtube_content': len(youtube_content) if youtube_content else 0
                }
            }
            
            print(f"    ✅ Generated {budget_type} itinerary: {len(daily_plans)} days, ₹{total_cost}")
            return result
            
        except Exception as e:
            print(f"    ❌ Error parsing response: {str(e)}")
            return None
    
    def _extract_activities_from_text(self, day_content, influencer_recs, youtube_content):
        """Extract structured activities from day content text"""
        activities = []
        
        # Common time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))',
            r'(\d{1,2}\s*(?:AM|PM))',
            r'(Morning|Afternoon|Evening|Night)',
            r'(\d{1,2}-\d{1,2}\s*(?:AM|PM))',
        ]
        
        # Extract activities with time, cost, and description
        lines = day_content.split('\n')
        current_activity = {}
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Check for time indicators
            time_found = False
            for pattern in time_patterns:
                time_match = re.search(pattern, line, re.IGNORECASE)
                if time_match:
                    # Save previous activity
                    if current_activity and current_activity.get('activity'):
                        activities.append(current_activity)
                    
                    # Start new activity
                    current_activity = {
                        'time': time_match.group(1),
                        'activity': line.replace(time_match.group(1), '').strip(' :-'),
                        'duration': self._extract_duration(line),
                        'cost': self._extract_cost(line),
                        'place': self._extract_place(line),
                        'details': line,
                        'influencer_recommended': self._check_influencer_match(line, influencer_recs),
                        'youtube_recommended': self._check_youtube_match(line, youtube_content),
                        'hotel_recommendation': False,
                        'transport_recommendation': False,
                        'flight_recommendation': False
                    }
                    time_found = True
                    break
            
            if not time_found and current_activity:
                # Add to current activity details
                current_activity['details'] += ' ' + line
                # Update place and cost if found in additional lines
                if not current_activity.get('place'):
                    current_activity['place'] = self._extract_place(line)
                if not current_activity.get('cost') or current_activity.get('cost') == 0:
                    current_activity['cost'] = self._extract_cost(line)
        
        # Add the last activity
        if current_activity and current_activity.get('activity'):
            activities.append(current_activity)
        
        # Ensure all activities have required fields
        for activity in activities:
            activity.setdefault('time', '9:00 AM')
            activity.setdefault('duration', '2 hours')
            activity.setdefault('cost', 500)
            activity.setdefault('place', 'Local Area')
            activity.setdefault('details', activity.get('activity', 'Activity'))
            activity.setdefault('influencer_recommended', False)
            activity.setdefault('youtube_recommended', False)
            activity.setdefault('hotel_recommendation', False)
            activity.setdefault('transport_recommendation', False)
            activity.setdefault('flight_recommendation', False)
        
        return activities
    
    def _extract_cost(self, text):
        """Extract cost from text"""
        import random
        cost_patterns = [
            r'₹(\d+(?:,\d+)*)',
            r'Rs\.?\s*(\d+(?:,\d+)*)',
            r'INR\s*(\d+(?:,\d+)*)',
            r'\$(\d+(?:,\d+)*)',
            r'(\d+(?:,\d+)*)\s*(?:rupees|rs|inr)',
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                return int(cost_str)
        
        return random.randint(200, 2000)  # Default random cost
    
    def _extract_duration(self, text):
        """Extract duration from text"""
        duration_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*hrs?',
            r'(\d+)\s*h',
            r'(\d+)-(\d+)\s*hours?',
            r'half\s*day',
            r'full\s*day',
            r'whole\s*day',
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'half' in pattern:
                    return "4 hours"
                elif 'full' in pattern or 'whole' in pattern:
                    return "8 hours"
                elif len(match.groups()) > 1:  # Range like "2-3 hours"
                    return f"{match.group(1)}-{match.group(2)} hours"
                else:
                    return f"{match.group(1)} hours"
        
        return "2-3 hours"  # Default duration
    
    def _extract_place(self, text):
        """Extract place/location from text"""
        # Common location indicators
        location_patterns = [
            r'Location:\s*([A-Z][a-zA-Z\s,]+?)(?:\n|$)',
            r'at\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'in\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\|)',
            r'explore\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\|)',
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Beach|Fort|Temple|Market|Palace|Garden|Museum)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                if len(place) > 2 and len(place) < 50:  # Reasonable place name length
                    return place
        
        return ""  # Return empty string if no place found
    
    def _create_enhanced_prompt(self, destination, duration, budget, themes, style, influencer_recs, youtube_content):
        """Create detailed prompt for Gemini generation"""
        theme_str = ', '.join(themes) if themes else 'general exploration'
        daily_budget = budget / duration
        
        # Process recommendations
        influencer_tips = []
        if influencer_recs:
            for rec in influencer_recs[:5]:  # Limit to top 5
                influencer_tips.append(f"- {rec['place']}: {rec['tip']} (Budget: {rec['budget_range']}, Best time: {rec['best_time']})")
        
        youtube_insights = []
        if youtube_content:
            for video in youtube_content[:3]:  # Limit to top 3
                if video.get('locations'):
                    for location in video['locations'][:2]:
                        youtube_insights.append(f"- {location} (Featured in: {video['title']})")
        
        prompt = f"""
        Create a detailed {duration}-day {style} travel itinerary for {destination}.
        
        REQUIREMENTS:
        - Total Budget: ₹{budget} (₹{daily_budget:.0f} per day)
        - Style: {style.title()} (adjust luxury level accordingly)
        - Themes: {theme_str}
        
        LOCAL EXPERT RECOMMENDATIONS:
        {chr(10).join(influencer_tips) if influencer_tips else "No local recommendations available"}
        
        POPULAR ATTRACTIONS (from travel vlogs):
        {chr(10).join(youtube_insights) if youtube_insights else "No video recommendations available"}
        
        FORMAT EXACTLY LIKE THIS:
        
        Day 1:
        9:00 AM: Visit Anjuna Beach - Enjoy sunrise and morning walk (₹200, 3 hours)
        Location: Anjuna Beach, North Goa
        Details: Beautiful sunrise views, morning yoga, beach cafes for breakfast
        
        1:00 PM: Explore Fort Aguada - Historical Portuguese fort tour (₹300, 2 hours)  
        Location: Fort Aguada, Candolim
        Details: 17th-century fort, lighthouse, panoramic sea views
        
        6:00 PM: Sunset at Baga Beach - Beach activities and dinner (₹800, 4 hours)
        Location: Baga Beach, North Goa
        Details: Water sports, beach shacks, famous nightlife area
        
        Day 2:
        [Continue same format for all {duration} days]
        
        COST GUIDELINES ({style}):
        - Economical: Activities ₹100-500, Food ₹200-400, Hotels ₹1000-2000
        - Balanced: Activities ₹300-800, Food ₹400-800, Hotels ₹2000-4000  
        - Luxury: Activities ₹500-1500, Food ₹800-2000, Hotels ₹4000-8000
        
        Include specific place names, exact costs in ₹, and detailed descriptions for each activity.
        """
        
        return prompt
    
    def _generate_with_gemini(self, prompt):
        """Generate content using Gemini with rate limiting"""
        try:
            import time
            time.sleep(1)  # Rate limiting
        
            response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=GenerateContentConfig(
                candidate_count=1,
                max_output_tokens=2048,
                temperature=0.8,
                top_p=0.9
            )
        )
        
            print(f"🔍 Response type: {type(response)}")
            print(f"🔍 Response attributes: {dir(response)}")
        
        # Handle different response structures from Google GenAI
            if response:
            # Method 1: Direct text attribute
                if hasattr(response, 'text') and response.text:
                    print(f"✅ Found text via direct attribute: {len(response.text)} chars")
                    return response.text
            
            # Method 2: Candidates structure
                if hasattr(response, 'candidates') and response.candidates:
                    print(f"🔍 Found {len(response.candidates)} candidates")
                    candidate = response.candidates[0]
                    print(f"🔍 Candidate type: {type(candidate)}")
                    print(f"🔍 Candidate attributes: {dir(candidate)}")
                
                    if hasattr(candidate, 'content') and candidate.content:
                        content = candidate.content
                        print(f"🔍 Content type: {type(content)}")
                        print(f"🔍 Content attributes: {dir(content)}")
                    
                    # Try parts structure
                        if hasattr(content, 'parts') and content.parts:
                            print(f"🔍 Found {len(content.parts)} parts")
                            response_text = ""
                            for i, part in enumerate(content.parts):
                                print(f"🔍 Part {i} type: {type(part)}")
                                print(f"🔍 Part {i} attributes: {dir(part)}")
                                if hasattr(part, 'text') and part.text:
                                    response_text += part.text
                                    print(f"✅ Added text from part {i}: {len(part.text)} chars")
                            if response_text:
                                return response_text
                    
                    # Try direct content text
                        if hasattr(content, 'text') and content.text:
                            print(f"✅ Found text via content.text: {len(content.text)} chars")
                            return content.text
                
                # Try direct candidate text
                    if hasattr(candidate, 'text') and candidate.text:
                        print(f"✅ Found text via candidate.text: {len(candidate.text)} chars")
                        return candidate.text
            
            # Method 3: String response
                if isinstance(response, str):
                    print(f"✅ Response is string: {len(response)} chars")
                    return response
            
            # Method 4: Dictionary response
                if isinstance(response, dict):
                    print(f"🔍 Response is dict with keys: {response.keys()}")
                    if 'text' in response and response['text']:
                        return response['text']
                    if 'candidates' in response and response['candidates']:
                        candidate = response['candidates'][0]
                        if 'content' in candidate:
                            content = candidate['content']
                            if 'parts' in content:
                                text_parts = []
                                for part in content['parts']:
                                    if 'text' in part and part['text']:
                                        text_parts.append(part['text'])
                                if text_parts:
                                    return ''.join(text_parts)
                            if 'text' in content and content['text']:
                                return content['text']
        
            print(f"❌ Could not extract text from response structure")
            return None
        
        except Exception as e:
            print(f"Gemini generation error: {str(e)}")
            print(f"🔍 Error type: {type(e)}")
            import traceback
            print(f"🔍 Full traceback: {traceback.format_exc()}")
            return None
    
    def _parse_gemini_response(self, response_text, destination, duration, budget, budget_type, influencer_recs, youtube_content):
        """Parse Gemini response into structured itinerary"""
        try:
            print(f"    🔍 Parsing response for {budget_type}: {len(response_text)} chars")
            
            # Extract daily activities using regex patterns
            daily_plans = []
            
            # Try multiple parsing approaches
            # Approach 1: Look for "Day X" patterns
            day_pattern = r'Day\s*(\d+)[:.]?\s*(.*?)(?=Day\s*\d+|$)'
            day_matches = re.findall(day_pattern, response_text, re.DOTALL | re.IGNORECASE)
            
            print(f"    📋 Found {len(day_matches)} day matches using Day pattern")
            
            if day_matches:
                for day_num, day_content in day_matches:
                    if int(day_num) > duration:
                        break
                        
                    activities = self._extract_activities_from_text(day_content, influencer_recs, youtube_content)
                    
                    if activities:
                        daily_plans.append({
                            'day': int(day_num),
                            'activities': activities
                        })
                        print(f"      ✅ Day {day_num}: {len(activities)} activities")
                    else:
                        print(f"      ❌ Day {day_num}: No activities extracted")
            
            # Approach 2: If no structured days found, use enhanced fallback with hotels/transport
            if not daily_plans:
                print(f"    🔄 No structured days found, using enhanced fallback with hotels/transport")
                daily_plans = self._create_enhanced_fallback_plans(
                    destination, duration, budget, budget_type
                )
            
            # Approach 3: If still no plans, use enhanced fallback
            if not daily_plans:
                print(f"    🔄 Using enhanced fallback for {destination}")
                daily_plans = self._create_enhanced_fallback_plans(destination, duration, budget, budget_type)
            
            # Calculate total cost
            total_cost = sum(
                sum(activity.get('cost', 0) for activity in day['activities'])
                for day in daily_plans
            )
            
            result = {
                'destination': destination,
                'duration': duration,
                'budget': budget,
                'budget_type': budget_type,
                'total_cost': total_cost,
                'daily_plans': daily_plans,
                'ai_generated': len(daily_plans) > 0,
                'gemini_response_length': len(response_text),
                'data_sources': {
                    'influencer_recommendations': len(influencer_recs),
                    'youtube_content': len(youtube_content),
                    'ai_powered': True,
                    'template_based': len(daily_plans) == 0
                }
            }
            
            print(f"    📊 Final result: {len(daily_plans)} days, ₹{total_cost} total cost")
            return result
            
        except Exception as e:
            print(f"    ❌ Error parsing Gemini response: {str(e)}")
            return self._create_fallback_itinerary(destination, duration, budget, budget_type)
    
    def _extract_activities_from_text(self, day_content, influencer_recs, youtube_content):
        """Extract structured activities from day content text"""
        activities = []
        
        # Common time patterns
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM))',
            r'(\d{1,2}\s*(?:AM|PM))',
            r'(Morning|Afternoon|Evening|Night)',
            r'(\d{1,2}-\d{1,2}\s*(?:AM|PM))',
        ]
        
        # Extract activities with time, cost, and description
        lines = day_content.split('\n')
        current_activity = {}
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 3:
                continue
            
            # Check for time indicators
            time_found = False
            for pattern in time_patterns:
                time_match = re.search(pattern, line, re.IGNORECASE)
                if time_match:
                    # Save previous activity
                    if current_activity and current_activity.get('activity'):
                        activities.append(current_activity)
                    
                    # Start new activity
                    current_activity = {
                        'time': time_match.group(1),
                        'activity': line.replace(time_match.group(1), '').strip(' :-'),
                        'duration': self._extract_duration(line),
                        'cost': self._extract_cost(line),
                        'place': self._extract_place(line),
                        'details': line,
                        'influencer_recommended': self._check_influencer_match(line, influencer_recs),
                        'youtube_recommended': self._check_youtube_match(line, youtube_content)
                    }
                    time_found = True
                    break
            
            if not time_found and current_activity:
                # Add to current activity details
                current_activity['details'] += ' ' + line
                # Update place and cost if found in additional lines
                if not current_activity.get('place'):
                    current_activity['place'] = self._extract_place(line)
                if current_activity.get('cost', 0) == 0:
                    new_cost = self._extract_cost(line)
                    if new_cost > 0:
                        current_activity['cost'] = new_cost
        
        # Add last activity
        if current_activity and current_activity.get('activity'):
            activities.append(current_activity)
        
        # Ensure we have at least basic activities
        if not activities:
            activities = self._create_basic_activities(day_content)
        
        # Validate and clean activities
        cleaned_activities = []
        for activity in activities:
            if activity.get('activity') and len(activity['activity'].strip()) > 0:
                # Ensure all required fields exist with safe defaults
                cleaned_activity = {
                    'time': activity.get('time', '9:00 AM'),
                    'activity': activity.get('activity', 'Local Activity'),
                    'duration': activity.get('duration', '2-3 hours'),
                    'cost': int(activity.get('cost', 500)) if activity.get('cost') else 500,
                    'place': activity.get('place', 'Local area'),
                    'details': activity.get('details', activity.get('activity', 'Explore local attractions and experiences')),
                    'influencer_recommended': activity.get('influencer_recommended', False),
                    'youtube_recommended': activity.get('youtube_recommended', False),
                    'hotel_recommendation': activity.get('hotel_recommendation', False),
                    'transport_recommendation': activity.get('transport_recommendation', False),
                    'flight_recommendation': activity.get('flight_recommendation', False)
                }
                
                # Add optional fields if they exist
                if activity.get('tip'):
                    cleaned_activity['tip'] = activity['tip']
                if activity.get('video_title'):
                    cleaned_activity['video_title'] = activity['video_title']
                if activity.get('video_id'):
                    cleaned_activity['video_id'] = activity['video_id']
                
                cleaned_activities.append(cleaned_activity)
        
        return cleaned_activities if cleaned_activities else self._create_basic_activities(day_content)
    
    def _extract_cost(self, text):
        """Extract cost from text"""
        cost_patterns = [
            r'₹(\d+(?:,\d+)*)',
            r'INR\s*(\d+(?:,\d+)*)',
            r'Rs\.?\s*(\d+(?:,\d+)*)',
            r'(\d+(?:,\d+)*)\s*rupees'
        ]
        
        for pattern in cost_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                cost_str = match.group(1).replace(',', '')
                return int(cost_str)
        
        return random.randint(200, 2000)  # Default random cost
    
    def _extract_duration(self, text):
        """Extract duration from text"""
        duration_patterns = [
            r'(\d+)\s*hours?',
            r'(\d+)\s*hrs?',
            r'(\d+)\s*minutes?',
            r'(\d+)\s*mins?'
        ]
        
        for pattern in duration_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                num = int(match.group(1))
                if 'min' in text.lower():
                    return f"{num} minutes"
                else:
                    return f"{num} hours"
        
        return "2-3 hours"  # Default duration
    
    def _extract_place(self, text):
        """Extract place/location from text"""
        # Common location indicators
        location_patterns = [
            r'at\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\|)',
            r'in\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\|)',
            r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\|)',
            r'explore\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\|)',
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Beach|Fort|Temple|Market|Palace|Garden|Museum)',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                place = match.group(1).strip()
                if len(place) > 2 and len(place) < 50:  # Reasonable place name length
                    return place
        
        return ""  # Return empty string if no place found
    
    def _create_smart_daily_plans_from_text(self, response_text, destination, duration, budget, budget_type):
        """Create daily plans from general Gemini response text"""
        daily_plans = []
        daily_budget = budget / duration
        
        # Extract key attractions/activities mentioned in the response
        attractions = self._extract_attractions_from_text(response_text, destination)
        
        # Create activities for each day
        for day in range(1, duration + 1):
            activities = []
            
            # Distribute attractions across days
            day_attractions = attractions[(day-1)*3:day*3] if attractions else []
            
            # Morning activity
            morning_attraction = day_attractions[0] if len(day_attractions) > 0 else f"Explore {destination}"
            activities.append({
                'time': '9:00 AM',
                'activity': f'Visit {morning_attraction}',
                'duration': '3 hours',
                'cost': int(daily_budget * 0.3),
                'place': morning_attraction,
                'details': f'Morning exploration of {morning_attraction} with local sightseeing and photography'
            })
            
            # Afternoon activity  
            afternoon_attraction = day_attractions[1] if len(day_attractions) > 1 else f"Local markets in {destination}"
            activities.append({
                'time': '2:00 PM',
                'activity': f'Explore {afternoon_attraction}',
                'duration': '4 hours',
                'cost': int(daily_budget * 0.4),
                'place': afternoon_attraction,
                'details': f'Afternoon visit to {afternoon_attraction} with cultural experiences and local cuisine'
            })
            
            # Evening activity
            evening_attraction = day_attractions[2] if len(day_attractions) > 2 else f"Evening entertainment in {destination}"
            activities.append({
                'time': '7:00 PM',
                'activity': f'Experience {evening_attraction}',
                'duration': '3 hours',
                'cost': int(daily_budget * 0.3),
                'place': evening_attraction,
                'details': f'Evening activities at {evening_attraction} with dinner and local nightlife'
            })
            
            daily_plans.append({
                'day': day,
                'activities': activities
            })
        
        return daily_plans
    
    def _extract_attractions_from_text(self, text, destination):
        """Extract attraction names from Gemini response text"""
        attractions = []
        
        # Common attraction patterns
        patterns = [
            r'visit\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'explore\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'see\s+([A-Z][a-zA-Z\s]+?)(?:\s|,|\.|\n)',
            r'([A-Z][a-zA-Z\s]+?)\s+(?:Fort|Palace|Temple|Museum|Market|Beach|Lake|Garden)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                attraction = match.strip()
                if len(attraction) > 3 and len(attraction) < 30 and attraction not in attractions:
                    attractions.append(attraction)
        
        # Add some default attractions if none found
        if not attractions:
            if destination.lower() == 'hyderabad':
                attractions = ['Charminar', 'Golconda Fort', 'Hussain Sagar Lake', 'Ramoji Film City', 'Birla Mandir', 'Salar Jung Museum']
            elif destination.lower() == 'goa':
                attractions = ['Baga Beach', 'Fort Aguada', 'Old Goa Churches', 'Anjuna Beach', 'Dudhsagar Falls', 'Palolem Beach']
            else:
                attractions = [f'{destination} City Center', f'{destination} Market', f'{destination} Heritage Sites']
        
        return attractions[:9]  # Limit to 9 attractions (3 per day for 3 days)
    
    def _create_enhanced_fallback_plans(self, destination, duration, budget, budget_type):
        """Create enhanced fallback plans with destination-specific content"""
        print(f"    🏗️ Creating enhanced fallback for {destination}, {budget_type}, ₹{budget}")
        daily_budget = budget / duration
        
        # Destination-specific templates
        templates = {
            'hyderabad': {
                'attractions': ['Charminar & Laad Bazaar', 'Golconda Fort', 'Hussain Sagar Lake', 'Ramoji Film City', 'Birla Mandir', 'Salar Jung Museum'],
                'foods': ['Hyderabadi Biryani', 'Haleem', 'Qubani ka Meetha', 'Irani Chai', 'Kebabs', 'Nihari'],
                'areas': ['Old City', 'Banjara Hills', 'Jubilee Hills', 'Secunderabad', 'Hitech City', 'Charminar Area'],
                'hotels': {
                    'Budget-Friendly': [
                        {'name': 'Hotel Sitara Grand', 'price': 1500, 'area': 'Banjara Hills', 'rating': '3-star'},
                        {'name': 'Treebo Trend Amber', 'price': 1800, 'area': 'Gachibowli', 'rating': '3-star'}
                    ],
                    'Standard': [
                        {'name': 'Novotel Hyderabad Airport', 'price': 3500, 'area': 'HITEC City', 'rating': '4-star'},
                        {'name': 'Marriott Hyderabad', 'price': 4000, 'area': 'Tank Bund Road', 'rating': '4-star'}
                    ],
                    'Premium': [
                        {'name': 'Park Hyatt Hyderabad', 'price': 8000, 'area': 'Banjara Hills', 'rating': '5-star'},
                        {'name': 'ITC Kohenur', 'price': 7500, 'area': 'HITEC City', 'rating': '5-star'}
                    ]
                },
                'transport': {
                    'Budget-Friendly': {'mode': 'Metro/Bus', 'daily_cost': 200},
                    'Standard': {'mode': 'Cab/Auto', 'daily_cost': 500},
                    'Premium': {'mode': 'Private Car', 'daily_cost': 1000}
                }
            },
            'goa': {
                'attractions': ['Baga Beach', 'Fort Aguada', 'Basilica of Bom Jesus', 'Anjuna Beach', 'Dudhsagar Falls', 'Palolem Beach'],
                'foods': ['Fish Curry Rice', 'Bebinca', 'Feni', 'Prawn Balchao', 'Goan Sausage', 'Sol Kadhi'],
                'areas': ['North Goa', 'South Goa', 'Panaji', 'Old Goa', 'Candolim', 'Calangute'],
                'hotels': {
                    'Budget-Friendly': [
                        {'name': 'OYO Beach Resort', 'price': 1800, 'area': 'Calangute', 'rating': '3-star'},
                        {'name': 'Zostel Goa', 'price': 1500, 'area': 'Anjuna', 'rating': '3-star'}
                    ],
                    'Standard': [
                        {'name': 'Lemon Tree Hotel', 'price': 4000, 'area': 'Candolim', 'rating': '4-star'},
                        {'name': 'Novotel Goa Resort', 'price': 4500, 'area': 'Dona Paula', 'rating': '4-star'}
                    ],
                    'Premium': [
                        {'name': 'Taj Exotica Resort', 'price': 12000, 'area': 'Benaulim', 'rating': '5-star'},
                        {'name': 'Grand Hyatt Goa', 'price': 10000, 'area': 'Bambolim', 'rating': '5-star'}
                    ]
                },
                'transport': {
                    'Budget-Friendly': {'mode': 'Local Bus/Bike Rental', 'daily_cost': 300},
                    'Standard': {'mode': 'Taxi/Scooter Rental', 'daily_cost': 600},
                    'Premium': {'mode': 'Private Car with Driver', 'daily_cost': 1200}
                }
            }
        }
        
        template = templates.get(destination.lower(), {
            'attractions': [f'{destination} Main Attractions', f'{destination} Heritage Sites', f'{destination} Local Markets'],
            'foods': ['Local Cuisine', 'Street Food', 'Traditional Dishes'],
            'areas': [f'{destination} City Center', f'{destination} Old Town', f'{destination} Modern Area'],
            'hotels': {
                'Budget-Friendly': [{'name': f'Budget Hotel {destination}', 'price': 1200, 'area': f'{destination} Center', 'rating': '3-star'}],
                'Standard': [{'name': f'Standard Hotel {destination}', 'price': 2500, 'area': f'{destination} Center', 'rating': '4-star'}],
                'Premium': [{'name': f'Luxury Hotel {destination}', 'price': 5000, 'area': f'{destination} Center', 'rating': '5-star'}]
            },
            'transport': {
                'Budget-Friendly': {'mode': 'Local Bus/Metro', 'daily_cost': 150},
                'Standard': {'mode': 'Taxi/Auto', 'daily_cost': 400},
                'Premium': {'mode': 'Private Car', 'daily_cost': 800}
            }
        })
        
        print(f"    📋 Using template for {destination.lower()}: {len(template.get('hotels', {}))} hotel categories")
        
        daily_plans = []
        
        # Get hotels and transport for this budget type
        hotels = template.get('hotels', {}).get(budget_type, [])
        transport = template.get('transport', {}).get(budget_type, {'mode': 'Local Transport', 'daily_cost': 300})
        selected_hotel = hotels[0] if hotels else {'name': f'{budget_type} Hotel', 'price': int(daily_budget * 0.3), 'area': destination, 'rating': '3-star'}
        
        print(f"    🏨 Selected hotel: {selected_hotel['name']} (₹{selected_hotel['price']})")
        print(f"    🚗 Selected transport: {transport['mode']} (₹{transport['daily_cost']}/day)")
        
        for day in range(1, duration + 1):
            activities = []
            
            # Get attractions for this day
            day_attractions = template['attractions'][(day-1)*2:(day-1)*2+3]
            day_foods = template['foods'][(day-1)*2:(day-1)*2+2] if 'foods' in template else ['Local Cuisine']
            
            # Transportation (start of day)
            if day == 1:
                activities.append({
                    'time': '8:00 AM',
                    'activity': f'Transportation - {transport["mode"]}',
                    'duration': '1 hour',
                    'cost': transport['daily_cost'],
                    'place': f'{destination} Transport Hub',
                    'details': f'Daily transportation using {transport["mode"]} for convenient city travel and sightseeing.',
                    'transport_recommendation': True
                })
            
            # Morning
            morning_attraction = day_attractions[0] if day_attractions else f'{destination} Sightseeing'
            morning_activity = {
                'time': '9:00 AM',
                'activity': f'Visit {morning_attraction}',
                'duration': '3 hours',
                'cost': int(daily_budget * 0.2),
                'place': morning_attraction,
                'details': f'Explore the historic and cultural significance of {morning_attraction}. Perfect for morning photography and learning about local heritage.',
                'influencer_recommended': False,
                'youtube_recommended': False,
                'hotel_recommendation': False,
                'transport_recommendation': False,
                'flight_recommendation': False
            }
            activities.append(morning_activity)
            
            # Afternoon
            afternoon_attraction = day_attractions[1] if len(day_attractions) > 1 else f'{destination} Local Experience'
            activities.append({
                'time': '1:00 PM',
                'activity': f'Explore {afternoon_attraction}',
                'duration': '4 hours',
                'cost': int(daily_budget * 0.25),
                'place': afternoon_attraction,
                'details': f'Afternoon exploration of {afternoon_attraction} including local shopping and cultural experiences.',
                'influencer_recommended': False,
                'youtube_recommended': False,
                'hotel_recommendation': False,
                'transport_recommendation': False,
                'flight_recommendation': False
            })
            
            # Evening
            evening_food = day_foods[0] if day_foods else 'Local Cuisine'
            activities.append({
                'time': '6:00 PM',
                'activity': f'Dinner & {evening_food} Experience',
                'duration': '3 hours',
                'cost': int(daily_budget * 0.2),
                'place': f'{destination} Restaurant District',
                'details': f'Enjoy authentic {evening_food} at local restaurants with evening entertainment and cultural shows.',
                'influencer_recommended': False,
                'youtube_recommended': False,
                'hotel_recommendation': False,
                'transport_recommendation': False,
                'flight_recommendation': False
            })
            
            # Night accommodation
            activities.append({
                'time': '10:00 PM',
                'activity': f'Stay at {selected_hotel["name"]}',
                'duration': '10 hours',
                'cost': selected_hotel['price'],
                'place': f'{selected_hotel["area"]}, {destination}',
                'details': f'{selected_hotel["rating"]} {budget_type.lower()} accommodation with modern amenities, comfortable rooms, and excellent service. Located in {selected_hotel["area"]}.',
                'hotel_recommendation': True
            })
            
            daily_plans.append({
                'day': day,
                'activities': activities
            })
        
        # Add flight recommendations for the itinerary
        flight_cost = int(budget * 0.15) if budget_type == 'Budget-Friendly' else int(budget * 0.2)
        daily_plans[0]['activities'].insert(0, {
            'time': '6:00 AM',
            'activity': f'Flight to {destination}',
            'duration': '2-3 hours',
            'cost': flight_cost,
            'place': f'{destination} Airport',
            'details': f'{budget_type} flight booking to {destination}. Includes airport transfers and comfortable seating.',
            'flight_recommendation': True
        })
        
        print(f"    ✈️ Added flight: ₹{flight_cost}")
        print(f"    📊 Total activities per day: {[len(day['activities']) for day in daily_plans]}")
        
        return daily_plans
    
    def _get_influencer_recommendations(self, destination):
        """Get influencer recommendations from BigQuery"""
        if not self.bq_client:
            return []
            
        query = f"""
        SELECT platform, influencer_name, place_name, recommendation, category, budget_range, best_time
        FROM `{self.project_id}.travel_data.influencer_recommendations`
        WHERE LOWER(destination) = LOWER(@destination)
        LIMIT 10
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("destination", "STRING", destination)]
        )
        
        try:
            results = self.bq_client.query(query, job_config=job_config).result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error fetching influencer data: {str(e)}")
            return []
    
    def _get_youtube_content(self, destination):
        """Get YouTube travel content"""
        try:
            youtube_service = YouTubeService()
            return youtube_service.get_travel_content(destination)
        except Exception as e:
            print(f"Error getting YouTube content: {str(e)}")
            return []
    
    def _check_influencer_match(self, activity_text, influencer_recs):
        """Check if activity matches influencer recommendations"""
        for rec in influencer_recs:
            if rec['place_name'].lower() in activity_text.lower():
                return True
        return False
    
    def _check_youtube_match(self, activity, youtube_content):
        """Check if activity matches YouTube content"""
        if not youtube_content:
            return False
        
        activity_lower = activity.lower()
        for video in youtube_content:
            if any(location.lower() in activity_lower for location in video.get('locations', [])):
                return True
        return False
    
    def _get_youtube_title(self, activity, youtube_content):
        """Get YouTube video title for matching activity"""
        if not youtube_content:
            return "Travel Video"
        
        activity_lower = activity.lower()
        for video in youtube_content:
            if any(location.lower() in activity_lower for location in video.get('locations', [])):
                return video.get('title', 'Travel Video')
        return "Travel Video"
    
    def _get_youtube_video_id(self, activity, youtube_content):
        """Get YouTube video ID for matching activity"""
        if not youtube_content:
            return None
        
        activity_lower = activity.lower()
        for video in youtube_content:
            if any(location.lower() in activity_lower for location in video.get('locations', [])):
                return video.get('video_id')
        return None
    
    def _select_best_option(self, options, target_budget):
        """Select best itinerary option based on budget"""
        if not options:
            return None
        
        # Prefer options within budget
        within_budget = [opt for opt in options if opt.get('total_cost', 0) <= target_budget * 1.1]
        
        if within_budget:
            # Return the one closest to target budget
            return min(within_budget, key=lambda x: abs(x.get('total_cost', 0) - target_budget))
        else:
            # Return cheapest option if all exceed budget
            return min(options, key=lambda x: x.get('total_cost', float('inf')))
    
    def _create_fallback_options(self, destination, duration, budget, themes, influencer_recs, youtube_content):
        """Create fallback options when AI generation fails"""
        options = []
        
        budget_variations = [
            {"budget": int(budget * 0.8), "type": "Budget-Friendly"},
            {"budget": budget, "type": "Standard"},
            {"budget": int(budget * 1.2), "type": "Premium"}
        ]
        
        for budget_option in budget_variations:
            itinerary = self._create_fallback_itinerary(
                destination, duration, budget_option['budget'], budget_option['type']
            )
            options.append(itinerary)
        
        return options
    
    def _create_fallback_itinerary(self, destination, duration, budget, budget_type):
        """Create basic fallback itinerary"""
        daily_budget = budget / duration
        daily_plans = []
        
        for day in range(1, duration + 1):
            activities = [
                {
                    'time': '9:00 AM',
                    'activity': f'Morning exploration in {destination}',
                    'duration': '3 hours',
                    'cost': int(daily_budget * 0.3),
                    'details': f'Discover the morning charm of {destination} with local sightseeing'
                },
                {
                    'time': '2:00 PM',
                    'activity': f'Afternoon activities in {destination}',
                    'duration': '4 hours',
                    'cost': int(daily_budget * 0.4),
                    'details': f'Enjoy afternoon attractions and local experiences in {destination}'
                },
                {
                    'time': '7:00 PM',
                    'activity': f'Evening entertainment in {destination}',
                    'duration': '3 hours',
                    'cost': int(daily_budget * 0.3),
                    'details': f'Experience the nightlife and evening culture of {destination}'
                }
            ]
            
            daily_plans.append({
                'day': day,
                'activities': activities
            })
        
        total_cost = sum(sum(activity['cost'] for activity in day['activities']) for day in daily_plans)
        
        return {
            'destination': destination,
            'duration': duration,
            'budget': budget,
            'budget_type': budget_type,
            'total_cost': total_cost,
            'daily_plans': daily_plans,
            'ai_generated': False,
            'data_sources': {
                'template_based': True,
                'ai_powered': False
            }
        }
    
    def _create_basic_daily_plans(self, destination, duration, budget):
        """Create basic daily plans structure"""
        return self._create_fallback_itinerary(destination, duration, budget, "Standard")['daily_plans']
    
    def _create_basic_activities(self, day_content):
        """Create basic activities from day content"""
        return [
            {
                'time': '9:00 AM',
                'activity': 'Morning Activity',
                'duration': '3 hours',
                'cost': 500,
                'details': day_content[:100] + '...' if len(day_content) > 100 else day_content
            }
        ]
    
    def _itinerary_to_text(self, itinerary):
        """Convert itinerary to text format for modification prompts"""
        text = f"Destination: {itinerary['destination']}\n"
        text += f"Duration: {itinerary['duration']} days\n"
        text += f"Budget: ₹{itinerary['budget']}\n\n"
        
        for day_plan in itinerary['daily_plans']:
            text += f"Day {day_plan['day']}:\n"
            for activity in day_plan['activities']:
                text += f"  {activity['time']}: {activity['activity']} (₹{activity.get('cost', 0)})\n"
            text += "\n"
        
        return text
