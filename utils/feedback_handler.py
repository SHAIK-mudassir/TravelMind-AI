from google.cloud import bigquery
import datetime

class FeedbackHandler:
    def __init__(self, bq_client):
        self.bq_client = bq_client
        self.dataset_id = "travel_data"
        self.feedback_table = "user_feedback"

    def store_feedback(self, itinerary_id, destination, feedback_data):
        """Store user feedback for improving recommendations"""
        table_id = f"{self.bq_client.project}.{self.dataset_id}.{self.feedback_table}"
        
        rows_to_insert = [{
            'itinerary_id': itinerary_id,
            'destination': destination,
            'rating': feedback_data.get('rating'),
            'comments': feedback_data.get('comments'),
            'liked_places': feedback_data.get('liked_places', []),
            'disliked_places': feedback_data.get('disliked_places', []),
            'budget_accuracy': feedback_data.get('budget_accuracy'),
            'timestamp': datetime.datetime.now()
        }]

        errors = self.bq_client.insert_rows_json(table_id, rows_to_insert)
        return not errors  # Returns True if no errors

    def get_destination_insights(self, destination):
        """Get aggregated insights for a destination"""
        query = f"""
        SELECT 
            liked_places,
            COUNT(*) as recommendation_count,
            AVG(rating) as avg_rating,
            AVG(budget_accuracy) as budget_accuracy_score
        FROM `{self.bq_client.project}.{self.dataset_id}.{self.feedback_table}`
        WHERE destination = @destination
        GROUP BY liked_places
        ORDER BY recommendation_count DESC
        LIMIT 10
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("destination", "STRING", destination)
            ]
        )
        
        query_job = self.bq_client.query(query, job_config=job_config)
        return query_job.result()
