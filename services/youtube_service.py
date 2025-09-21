from googleapiclient.discovery import build
from google.cloud import bigquery
import json
import os
from datetime import datetime

class YouTubeService:
    def __init__(self):
        self.api_key = os.getenv('YOUTUBE_API_KEY')
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.bq_client = bigquery.Client()

    def get_travel_content(self, location):
        """Get travel content for a specific location"""
        try:
            # First check BigQuery cache
            cached_content = self._get_cached_content(location)
            if cached_content:
                return cached_content

            # If no cache, fetch from YouTube
            search_response = self.youtube.search().list(
                q=f"travel vlog {location} places to visit",
                part='snippet',
                maxResults=5,
                type='video',
                videoDefinition='high',
                relevanceLanguage='en',
                videoDuration='medium'  # Filter for medium length videos
            ).execute()

            processed_content = []
            for item in search_response['items']:
                try:
                    video_id = item['id']['videoId']
                    video_info = self._get_video_details(video_id)
                    
                    if video_info:
                        # Extract locations and recommendations from video
                        locations = self._extract_video_content(video_id)
                        
                        content = {
                            'video_id': video_id,
                            'title': item['snippet']['title'],
                            'channel': item['snippet']['channelTitle'],
                            'thumbnail': item['snippet']['thumbnails']['high']['url'],
                            'published_at': item['snippet']['publishedAt'],
                            'locations': locations,
                            'view_count': video_info.get('view_count', 0),
                            'like_count': video_info.get('like_count', 0)
                        }
                        
                        processed_content.append(content)
                        
                        # Cache the content in BigQuery
                        try:
                            self._cache_content(location, content)
                        except Exception as cache_error:
                            print(f"Failed to cache content: {str(cache_error)}")
                            
                except Exception as video_error:
                    print(f"Error processing video {item.get('id', {}).get('videoId', 'unknown')}: {str(video_error)}")
                    continue

            return processed_content

        except Exception as e:
            print(f"Error fetching travel content: {str(e)}")
            return []

    def _get_video_details(self, video_id):
        """Get detailed information about a specific video"""
        try:
            video_response = self.youtube.videos().list(
                part='statistics,contentDetails',
                id=video_id
            ).execute()

            if video_response['items']:
                stats = video_response['items'][0]['statistics']
                return {
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0))
                }
            return None

        except Exception as e:
            print(f"Error fetching video details: {str(e)}")
            return None

    def _extract_video_content(self, video_id):
        """Extract location mentions and recommendations from video"""
        try:
            # Get video details and description
            video_response = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()

            locations = []
            if 'items' in video_response:
                description = video_response['items'][0]['snippet']['description']
                # Extract locations from description
                # For hackathon MVP, we'll extract any text that looks like a location
                import re
                # Look for common location patterns
                location_patterns = [
                    r'visit(?:ing)?\s+([A-Z][a-zA-Z\s]+)',
                    r'at\s+([A-Z][a-zA-Z\s]+)',
                    r'in\s+([A-Z][a-zA-Z\s]+)',
                    r'location:\s*([A-Z][a-zA-Z\s]+)',
                    r'places?(?:\s+to\s+visit)?:\s*([A-Z][a-zA-Z\s]+)'
                ]
                
                for pattern in location_patterns:
                    matches = re.finditer(pattern, description)
                    for match in matches:
                        location = match.group(1).strip()
                        if location and len(location) > 3:  # Avoid too short matches
                            locations.append(location)
                
                # Remove duplicates
                locations = list(set(locations))

            return locations

        except Exception as e:
            print(f"Error extracting video content: {str(e)}")
            return []

    def _get_cached_content(self, location):
        """Get cached content from BigQuery"""
        query = f"""
        SELECT *
        FROM `{self.bq_client.project}.travel_data.youtube_content`
        WHERE location = @location
        AND created_at > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)
        ORDER BY view_count DESC
        LIMIT 5
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("location", "STRING", location)
            ]
        )
        
        try:
            results = self.bq_client.query(query, job_config=job_config).result()
            return [dict(row) for row in results]
        except Exception as e:
            print(f"Error fetching cached content: {str(e)}")
            return None

    def _cache_content(self, location, content):
        """Cache content in BigQuery"""
        query = f"""
        INSERT INTO `{self.bq_client.project}.travel_data.youtube_content`
        (location, video_id, title, channel, thumbnail_url, published_at, 
         view_count, like_count, locations, created_at)
        VALUES
        (@location, @video_id, @title, @channel, @thumbnail, @published_at,
         @views, @likes, @locations, CURRENT_TIMESTAMP())
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("location", "STRING", location),
                bigquery.ScalarQueryParameter("video_id", "STRING", content['video_id']),
                bigquery.ScalarQueryParameter("title", "STRING", content['title']),
                bigquery.ScalarQueryParameter("channel", "STRING", content['channel']),
                bigquery.ScalarQueryParameter("thumbnail", "STRING", content['thumbnail']),
                bigquery.ScalarQueryParameter("published_at", "TIMESTAMP", content['published_at']),
                bigquery.ScalarQueryParameter("views", "INTEGER", content['view_count']),
                bigquery.ScalarQueryParameter("likes", "INTEGER", content['like_count']),
                bigquery.ScalarQueryParameter("locations", "STRING", json.dumps(content['locations']))
            ]
        )
        
        try:
            self.bq_client.query(query, job_config=job_config).result()
        except Exception as e:
            print(f"Error caching content: {str(e)}")

    def _extract_locations_from_captions(self, caption_content):
        """Extract location mentions from video captions"""
        # This would be enhanced with NLP in production
        locations = []
        # Basic extraction logic
        return locations
