import json
import requests
import boto3
import os
from datetime import datetime

def lambda_handler(event, context):
    # OpenWeatherMap API key and endpoint
    #owm_api_key = os.environ['OPENWEATHERMAP_API_KEY']
    aw_api_key = os.environ['AccuWeather_API_Key']
    #owm_city_id = '993800'  # Edenvale, Gauteng, South Africa
    aw_city_id = '1148699'  # Edenvale, Gauteng, South Africa
    #url = f'http://api.openweathermap.org/data/2.5/weather?id={owm_city_id}&appid={owm_api_key}'
    url = f'http://dataservice.accuweather.com/currentconditions/v1/{aw_city_id}?apikey={aw_api_key}&details=true'

    # Fetch the weather data
    try:
        response = requests.get(url)
        weather_data = response.json()
    
        # Log weather data
        print("Weather data:", weather_data)
    except Exception as e:
        error_message = f'Failed to fetch weather data: {str(e)}'
        print("Error fetching weather data:", error_message)
    
    # Upload to S3
    try:
        s3 = boto3.client('s3')
    except Exception as e:
        error_message = f'Failed to connect to AWS S3 Service: {str(e)}'
        print("Error connecting to AWS S3 Service:", error_message)
    
    try: 
        bucket_name = 'aw-weather-data'
        file_name = f'weather_data_{datetime.now().strftime("%Y%m%d%H%M%S")}.json'
        
        s3.put_object(Bucket=bucket_name, Key=file_name, Body=json.dumps(weather_data))
        print("Weather data written to S3:", file_name)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Weather data stored in S3 Bucket successfully!')
        }
    except Exception as e:
        error_message = f'Failed to store weather data to AWS S3 Bucket: {str(e)}'
        print("Error storing weather data to AWS S3 Bucket:", error_message)

if __name__ == "__main__":
    lambda_handler(0, 0)