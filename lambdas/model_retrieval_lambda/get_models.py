import sys
sys.path.append('/mnt/python')  # import dependencies installed in EFS (can ONLY import packages AFTER this step)
from flask import jsonify
import logging

logging.getLogger().setLevel(logging.INFO)


# Functions to add
# 1. Given a particular username, return a list of all model names and versions associated with the user (DONE)
# 2. Given a model name and version, allow user to download model
#    - Check out artificien experimental for methods to download the model from PyGrid
#    - Look into converting the model into an H5
#    - Look into how to download/ send back the H5.
# 3. Given a model name and version, allow user to view model information/ params.


def default():
    logging.info('Successfully served GET/ method')
    return jsonify({'statusCode': 404,
                    'headers': {},
                    'body': {'message': 'ERROR: Method not found'}
                    })


def test():
    logging.info('Successfully served GET /test method')
    return jsonify({'statusCode': 200,
                    'headers': {},
                    'body': {'message': 'You\'ve successfully invoked the test method'}
                    })


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
            return jsonify({'statusCode': 400,
                            'headers': {},
                            'body': 'We only accept GET methods right now'})

    except KeyError:
        logging.warning('Not a proper REST call', exc_info=True)  # prints stack trace
        return jsonify({'statusCode': 400,
                        'headers': {},
                        'body': {'message': 'Not a proper REST call. No HTTP method or path found.'}
                        })

    except Exception:
        logging.error('Unexpected Error', exc_info=True)  # prints stack trace
        return jsonify({'statusCode': 500,
                        'headers': {},
                        'body': {'message': 'Unexpected error occurred.'}
                        })
