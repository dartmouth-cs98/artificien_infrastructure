import sys
import json
import logging
import requests
import boto3
efs_mount = '/mnt/python/'
sys.path.append(efs_mount)  # import dependencies installed in EFS (can ONLY import EFS packages AFTER this step)
# import syft as sy

logging.getLogger().setLevel(logging.INFO)

'''
Functions to add
1. Given a particular username, return a list of all model names and versions associated with the user (DONE)
2. Given a model name and version, allow user to download model
    - Check out artificien experimental for methods to download the model from PyGrid
    - Look into converting the model into an H5
    - Look into how to download/ send back the H5.
3. Given a model name and version, allow user to view model information/ params.

Requirements for the response:
1. 'body' property must be a 'JSON string' (i.e. use json.dumps on whatever dictionary you want to pass
    in the body)
2. headers is just a standard dictionary
3. The following fields are required:
    {
    "isBase64Encoded": true|false,
    "statusCode": httpStatusCode,
    "headers": { "headerName": "headerValue", ... },
    "body": "..."
    }
'''
logging.getLogger().setLevel(logging.INFO)


def default():
    logging.info('Successfully served GET/ method')
    return {
        'isBase64Encoded': False,
        'statusCode': 404,
        'headers': {},
        'body': json.dumps({'message': 'ERROR: Method not found'})
    }


def test():
    logging.info('Successfully served GET /test method')
    return {
        'isBase64Encoded': False,
        'statusCode': 200,
        'headers': {},
        'body': json.dumps({'message': "You've successfully invoked the test method"})
    }

def retrieve(event):
    
    # 1. parse out the event values
    query_string_parameters = event['queryStringParameters']

    user = query_string_parameters['ownerName']
    model_id = query_string_parameters['modelId']
    version = query_string_parameters['version']
    node_url = "http://pygri-pygri-frtwp3inl2zq-2ea21a767266378c.elb.us-east-1.amazonaws.com:5000"

    print(user, model_id, version, node_url)

    # 2. get pygrid model
    payload = {
        "name": model_id,
        "version": version,
        "checkpoint": "latest"
    }
    url = node_url + "/model-centric/retrieve-model"

    r = requests.get(url, params=payload)
    data = r.json()
    print(data)

    serialized_model = data['serialized_model']
    print(serialized_model)

    # 3. put model to s3 bucket

    # 4. flip is_active boolean on model in dynamo
    # dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    # table = dynamodb.Table('model_table')

    # update_response = table.update_item(
    #     Key = {'model_id' : model_id},
    #     UpdateExpression = "set active_status = :r",
    #     ExpressionAttributeValues={
    #     ':r': 0,
    #     },
    # )

    # if update_response:
    #     print("UPDATE success")
    #     print(user)
    #     print(version)

    # # 5. return response with url  
    # return {
    #     'statusCode': 200,
    #     'isBase64Encoded': False,
    #     'headers': {},
    #     'body': {'message': 'You\'ve successfully invoked the retrieve model method'},
    #     }


def lambda_handler(event, context):
    try:
        method = event['httpMethod']
        # body = event['body'] # JSON body passed to method
        # headers = event['headers'] # JSON headers

        if method == 'GET':
            if event['path'] == '/':
                return default()
            if event['path'] == '/test':
                return test()

        else:
            # We only accept GET for now
            return {
                'isBase64Encoded': False,
                'statusCode': 400,
                'headers': {},
                'body': json.dumps('We only accept GET methods right now')
            }

    except KeyError:
        logging.warning('Not a proper REST call', exc_info=True)  # prints stack trace
        return {
            'isBase64Encoded': False,
            'statusCode': 400,
            'headers': {},
            'body': json.dumps({'message': 'Not a proper REST call. No HTTP method or path found.'})
        }

    except Exception:
        logging.error('Unexpected Error', exc_info=True)  # prints stack trace
        return {
            'isBase64Encoded': False,
            'statusCode': 500,
            'headers': {},
            'body': json.dumps({'message': 'Unexpected error occurred.'})
        }
