import json
import os
import shlex
import subprocess
from datetime import date

import boto3
import requests
import syft as sy
import torch as th
import websockets
import torch as th
from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify, request
from syft.execution.placeholder import PlaceHolder
from syft.execution.state import State
from syft.execution.translation import TranslationTarget
from syft.frameworks.torch.hook import hook
from syft.grid.clients.model_centric_fl_client import ModelCentricFLClient
from syft.serde import protobuf
from torch import nn

import jsonpickle
from jsonpickle.ext import numpy as jsonpickle_numpy
from orchestration_helper import AppFactory
from post_deploy_actions import get_outputs
from syft_proto.execution.v1.plan_pb2 import Plan as PlanPB
from syft_proto.execution.v1.state_pb2 import State as StatePB
from websocket import create_connection


jsonpickle_numpy.register_handlers()

sy.make_hook(globals())
hook.local_worker.framework = None  # force protobuf serialization for tensors
th.random.manual_seed(1)

app = Flask(__name__)
region_name = "us-east-1"

try:
    ecs_client = boto3.client('ecs')

except BaseException as exe:
    print(exe)

dynamodb = boto3.resource('dynamodb', region_name=region_name)


# check api status, ping to test
@app.route("/")
def status():
    return "Running"


# spin up a new node for an app developer
@app.route("/create", methods=["POST"])
def create_node():
    # grab model id, query model_table to check if a node has already been spun up for model
    model_table = dynamodb.Table('model_table')
    model_id = request.json.get('model_id')
    model_id = model_id.lower()
    print(model_id)
    try:
        model_response = model_table.query(KeyConditionExpression=Key('model_id').eq(model_id))
    except:
        return jsonify({'error': 'failed to query dynamodb'}), 500
    print(model_response)

    if model_response['Items'] is None:
        return jsonify({'error': 'model id not found'}), 400

    # if model hasNode, check if node is fully deployed
    if model_response['Items'][0]['hasNode'] is True:
        output_dict = get_outputs(stack_name=model_id)
        if output_dict is None:
            return jsonify({'status': 'node is deploying, please try later'})
        nodeURL = output_dict['PyGridNodeLoadBalancerDNS']
        # put nodeAddress into DB
        model_response['Items'][0]['node_URL'] = nodeURL
        model_table.put_item(Item=model_response['Items'][0])
        return jsonify({'status': 'ready'})

    # if node hasn't been loaded yet, first validate the user has access to data
    owner = model_response['Items'][0]['owner_name']
    # if validate_user(model_id, owner) is False:
    #     return jsonify({'error': 'user has not purchased requested dataset'}), 600

    # deploy resources
    app_factory = AppFactory()
    app_factory.make_standard_stack(model_id)
    app_factory.generate_stack()
    app_factory.launch_stack()
    print("Deploying")

    # set hasNode to true
    model_response['Items'][0]['hasNode'] = True
    model_table.put_item(Item=model_response['Items'][0])
    return jsonify({'status': 'node is starting to deploy. This may take a few minutes'})


# delete node of an app developer
@app.route("/delete", methods=["POST"])
def delete_node():
    return None


@app.route("/model_progress", methods=["POST"])
def model_progress():
    """ Updates the percent complete attribute of a model, and retrieves the model if it is done training """

    # Get the new model complete metric from PyGrid
    model_id = request.json.get('model_id')
    percent_complete = request.json.get('percent_complete')
    model_table = dynamodb.Table('model_table')

    # Debugging
    print('Got model', model_id, 'from PyGrid, which is', percent_complete, 'percent complete')

    # Update the DynamoDB entry for 'percent_complete'
    try:
        model = model_table.query(KeyConditionExpression=Key('model_id').eq(model_id))['Items'][0]
    except:
        return jsonify({'error': 'failed to query dynamodb'}), 500

    model['percent_complete'] = percent_complete
    model_table.put_item(Item=model)

    # If the model is done training, retrieve it so that the user can download it
    if percent_complete == 100:
        # Do model retrieval
        retrieve(user=model['owner_name'], model_id=model_id, version=model['version'], node_url=model['node_URL'])

        # If all models left in the node are done, spin it down

    return jsonify({'status': 'model completion was updated successfully'})


@app.route("/send", methods=["POST"])
def send_model():
    # model_table = dynamodb.Table('model_table')
    # model_pkl = request.json.get('model')
    # x_pkl = request.json.get('x')
    # y_pkl = request.json.get('y')
    # training_plan_pkl = request.json.get('training_plan_func')
    # optim_func_pkl = request.json.get('optim')
    # loss_func_pkl = request.json.get('loss')
    # model = jsonpickle.encode(model_pkl)
    # x = jsonpickle.decode(x_pkl)
    # y = jsonpickle.decode(y_pkl)
    # training_plan = jsonpickle.decode(training_plan_pkl)
    # optim_func = jsonpickle.decode(optim_func_pkl)
    # loss_func = jsonpickle.decode(loss_func_pkl)

    # model_params, training_plan = syftfunctions.def_training_plan(model, x, y, None)
    # avg_plan = syftfunctions.def_avg_plan(model_params, None)
    # grid = syftfunctions.artificien_connect()
    # syftfunctions.send_model("perceptron", "0.1.1", "5", "0.5", "10", model_params, grid, training_plan, avg_plan)
    return None


def validate_user(model_id, owner):
    user_table = dynamodb.Table('user_table')
    try:
        user_response = user_table.query(KeyConditionExpression=Key('user_id').eq(owner))
    except:
        return jsonify({'error': 'failed to query dynamodb'}), 500

    if user_response['Items'][0] is None:
        return jsonify({'error': 'user not found'}), 400
    training_set = request.json.get('training_set')
    purchases = user_response['Items'][0]['datasets_purchased']
    if model_id in purchases:
        return True
    return False


def retrieve(user, model_id, version, node_url):

    # 1. get pygrid model
    payload = {
        "name": model_id,
        "version": version,
        "checkpoint": "latest"
    }

    url = node_url + "/model-centric/retrieve-model"
    r = requests.get(url, params=payload)
    th.save(r.content, '/tmp/model.pkl')  # only the /tmp directory in lambda is writable

    # 2. Put model in s3 bucket
    s3 = boto3.client('s3')
    region = region_name
    s3_bucket_name = "artificien-retrieved-models-storage"
    file_name = user + model_id + version + '/tmp/model.pkl'
    s3.upload_file('/tmp/model.pkl', s3_bucket_name, file_name)
    print('done!')

    bucket_url = 'https://s3.console.aws.amazon.com/s3/object/' + s3_bucket_name + '?region=' + region + '&prefix=' + file_name

    # 3. flip is_active boolean on model in dynamo
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    table = dynamodb.Table('model_table')

    update_response_1 = table.update_item(
        Key={'model_id': model_id},
        UpdateExpression="set active_status = :r",
        ExpressionAttributeValues={
            ':r': 0,
        },
    )

    # 4. Add bucket URL to model in Dynamo
    update_response_2 = table.update_item(
        Key={'model_id': model_id},
        UpdateExpression="set download_link = :r",
        ExpressionAttributeValues={
            ':r': bucket_url,
        },
    )

    if update_response_1 and update_response_2:
        print("UPDATE success")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)