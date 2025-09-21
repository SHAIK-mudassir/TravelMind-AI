import googlemaps
from datetime import datetime
import os

class MapsService:
    def __init__(self, maps_client):
        self.gmaps = maps_client
    
    def get_place_details(self, location):
        """Get tourist attractions near a location"""
        try:
            # First, geocode the location
            geocode_result = self.gmaps.geocode(location)
            if not geocode_result:
                return None
            
            location_coords = (
                geocode_result[0]['geometry']['location']['lat'],
                geocode_result[0]['geometry']['location']['lng']
            )
            
            # Get nearby places
            places = self.gmaps.places_nearby(
                location=location_coords,
                radius=5000,
                type='tourist_attraction'
            )
            
            return places.get('results', [])
        except Exception as e:
            print(f"Error getting place details: {str(e)}")
            return None

    def get_route_info(self, origin, destination):
        """Get route information between two points"""
        try:
            route = self.gmaps.directions(
                origin,
                destination,
                mode="driving",
                departure_time=datetime.now()
            )
            return route[0] if route else None
        except Exception as e:
            print(f"Error getting route info: {str(e)}")
            return None

    def get_place_photos(self, place_id):
        """Get photos for a specific place"""
        try:
            place = self.gmaps.place(place_id, fields=['photos'])
            if 'photos' in place['result']:
                return [
                    self.gmaps.places_photo(photo['photo_reference'])
                    for photo in place['result']['photos'][:3]  # Limit to 3 photos
                ]
            return []
        except Exception as e:
            print(f"Error getting place photos: {str(e)}")
            return []
