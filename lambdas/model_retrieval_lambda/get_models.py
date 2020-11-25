import sys
import json
import logging
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
