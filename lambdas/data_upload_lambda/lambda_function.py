# Importing relevant packages
from helper_functions import *


def lambda_handler(event, context):
    import_test()

    for record in event["Records"]:
        if record["eventName"] == 'INSERT':
            new_image = record["dynamodb"]["NewImage"]
            pk = new_image["dataset_id"]["S"]  # dataset name
            query_to_csv('dataset_id', pk)
