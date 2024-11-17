import json
import boto3
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
import os
import psycopg2
from datetime import datetime

def weatherMetricExtractor(event):
    # Get the bucket name and object key from the event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    object_key = event['Records'][0]['s3']['object']['key']

    # Initialize S3 client
    try:
        s3_client = boto3.client('s3')
    except Exception as e:
        print(f"Error connecting to AWS S3 Service: {str(e)}")
        return []
    
    # Get the object from S3
    try:
        response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    except Exception as e:
        print(f"Error getting S3 json object: {str(e)}")
        return []

    content = response['Body'].read().decode('utf-8')
    
    # Parse JSON content
    data = json.loads(content)
    
    # Extract required values
    extracted_data = []
    for item in data:
        extracted_info = {
            'event_datetime': datetime.now(),
            'WeatherText': item['WeatherText'],
            'CloudCover': item['CloudCover'],
            'Precip1hrMetricValue': item['Precip1hr']['Metric']['Value'],
            'Precip1hrMetricUnit': item['Precip1hr']['Metric']['Unit'],
            'TemperatureMetricValue': item['Temperature']['Metric']['Value'],
            'TemperatureMetricUnit': item['Temperature']['Metric']['Unit'],
            'RelativeHumidity': item['RelativeHumidity'],
            'UVIndex': item['UVIndex'],
            'VisibilityMetricValue': item['Visibility']['Metric']['Value'],
            'VisibilityMetricUnit': item['Visibility']['Metric']['Unit'],
            'WindDirection': item['Wind']['Direction']['Localized'],
            'WindSpeedMetricValue': item['Wind']['Speed']['Metric']['Value'],
            'WindSpeedMetricUnit': item['Wind']['Speed']['Metric']['Unit']
        }
        extracted_data.append(extracted_info)
    
    # Return extracted data
    return extracted_data

def create_schema_and_table(engine):
    try:
        with engine.connect() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS weather_data"))
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS weather_data.weather_extracts (
                    event_datetime TIMESTAMP NOT NULL,
                    WeatherText VARCHAR(20),
                    CloudCover NUMERIC(4, 2),
                    Precip1hrMetricValue NUMERIC(7, 3),
                    Precip1hrMetricUnit VARCHAR(5),
                    TemperatureMetricValue NUMERIC(4, 2),
                    TemperatureMetricUnit VARCHAR(2),
                    RelativeHumidity NUMERIC(4, 2),
                    UVIndex NUMERIC(4, 2),
                    VisibilityMetricValue NUMERIC(5, 2),
                    VisibilityMetricUnit VARCHAR(2),
                    WindDirection VARCHAR(3),
                    WindSpeedMetricValue NUMERIC(5, 2),
                    WindSpeedMetricUnit VARCHAR(4)
                )
            """))
            connection.commit()
    except SQLAlchemyError as e:
        print(f"Error while creating schema/table: {str(e)}")

def write_to_rds(extracted_data):
    # Database credentials
    db_user = os.environ['db_user']
    db_password = os.environ['db_password']
    db_host = os.environ['db_host']
    db_port = os.environ['db_port']
    db_name = os.environ['db_name']

    # Convert list of dictionaries to list of tuples
    result = [tuple(item.values()) for item in extracted_data]

    # Create a database connection using SQLAlchemy
    try:
        engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}')
    except Exception as e:
        print(f"Error while connecting to RDS: {str(e)}")
        return
    
    # Create schema and table if they don't exist
    create_schema_and_table(engine)
    
    try:
        raw_connection = engine.raw_connection()

        try:
            cursor = raw_connection.cursor()                   
            # Insert data into PostgreSQL table
            insert_query = """
                INSERT INTO weather_data.weather_extracts (
                    event_datetime, WeatherText, CloudCover, Precip1hrMetricValue, Precip1hrMetricUnit, TemperatureMetricValue,
                    TemperatureMetricUnit, RelativeHumidity, UVIndex, VisibilityMetricValue, VisibilityMetricUnit, WindDirection,
                    WindSpeedMetricValue, WindSpeedMetricUnit ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.executemany(insert_query, result)
            raw_connection.commit()
            cursor.close()
        finally:
            raw_connection.close()
    
    except SQLAlchemyError as e:
        print(f"Error while writing to RDS: {str(e)}")
        return
    
    return "success"

def lambda_handler(event, context):
    # Extract weather metrics
    record = weatherMetricExtractor(event)

    # Write the DataFrame to RDS
    write_to_rds(record)
    
    return {
        'statusCode': 200,
        'body': json.dumps('Data processed and written to RDS successfully!')
    }

# Test the lambda_handler function locally
if __name__ == "__main__":
    # Example event structure for testing
    event = {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": "aw-weather-data"
                    },
                    "object": {
                        "key": "weather_data_20241117175538.json"
                    }
                }
            }
        ]
    }
    context = {}
    lambda_handler(event, context)