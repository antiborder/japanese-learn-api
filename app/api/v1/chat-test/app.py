import json

def lambda_handler(event, context):
    """
    Minimal test lambda handler for container image testing
    """
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from Lambda Container!',
            'event': event
        }),
        'headers': {
            'Content-Type': 'application/json'
        }
    }

