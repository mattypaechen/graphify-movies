import os
import boto3
import json
from main import create_app # Import your factory

def get_neo4j_creds():
    secret_name = os.environ.get("NEO4J_SECRET_ARN")
    region_name = os.environ.get("AWS_REGION", "us-east-1")
    
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
    return ""

creds = get_neo4j_creds()

app_config = {
    "SCHEME": creds.get("NEO4J_SCHEME", "neo4j+s"),
    "HOST_NAME": creds.get("NEO4J_HOST"),
    "PORT": creds.get("NEO4J_PORT", "7687"),
    "USER": creds.get("NEO4J_USER"),
    "PASSWORD": creds.get("NEO4J_PASS"),
    "DATABASE": creds.get("NEO4J_DATABASE", "neo4j")
}

app = create_app(app_config)
