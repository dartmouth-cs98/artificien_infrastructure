import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify, request
from pygrid_node_stack import PygridNodeStack
from aws_cdk import core
from post_deploy_actions import get_outputs
import os
import syft as sy
from syft.serde import protobuf
from syft_proto.execution.v1.plan_pb2 import Plan as PlanPB
from syft_proto.execution.v1.state_pb2 import State as StatePB
from syft.grid.clients.model_centric_fl_client import ModelCentricFLClient
from syft.execution.state import State
from syft.execution.placeholder import PlaceHolder
from syft.execution.translation import TranslationTarget
from orchestration_helper import AppFactory
import subprocess
import shlex


from datetime import date
import torch as th
from torch import nn

from websocket import create_connection
import websockets
import json
import requests

app = Flask(__name__)
region_name = "us-east-1"

try:
  ecs_client = boto3.client('ecs')

except BaseException as exe:
    print(exe)

dynamodb = boto3.resource('dynamodb', region_name=region_name)

#check api status, ping to test
@app.route("/")
def status():
    return "Running"

#spin up a new node for an app developer
@app.route("/apps", methods=["POST"])
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
        model_response['Items'][0]['nodeURL'] = nodeURL
        model_table.put_item(Item=model_response['Items'][0])
        return jsonify({'status': 'ready'})

    #if node hasn't been loaded yet, first validate the user has access to data
    owner = model_response['Items'][0]['owner_name']
    if validate_user(model_id, owner) is False:
        return jsonify({'error': 'user has not purchased requested dataset'}), 600

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

#delete node of an app developer
@app.route("/delete", methods=["POST"])
def delete_node():
    return None
@app.route("/send", methods=["POST"])
def send_model():
    nodeAddress=None
    name=None
    node = ModelCentricFLClient(id="test", address=nodeAddress, secure=False)
    node.connect()

    version = request.json.get('version')
    batch_size = request.json.get('batch_size')
    learning_rate = request.json.get('learning_rate')
    max_updates = request.json.get('max_updates')
    model_params = request.json.get('model_params')
    training_plan = request.json.get('training_plan')
    avg_plan = request.json.get('avg_plan')


    client_config = {
        "name": name,
        "version": version,
        "batch_size": batch_size,
        "lr": learning_rate,
        "max_updates": max_updates  # custom syft.js option that limits number of training loops per worker
    }

    server_config = {
        "min_workers": 5,
        "max_workers": 5,
        "pool_selection": "random",
        "do_not_reuse_workers_until_cycle": 6,
        "cycle_length": 28800,  # max cycle length in seconds
        "num_cycles": 5,  # max number of cycles
        "max_diffs": 1,  # number of diffs to collect before avg
        "minimum_upload_speed": 0,
        "minimum_download_speed": 0,
        "iterative_plan": True  # tells PyGrid that avg plan is executed per diff
    }

    model_params_state = State(
        state_placeholders=[
            PlaceHolder().instantiate(param)
            for param in model_params
        ]
    )

    response = node.host_federated_training(
        model=model_params_state,
        client_plans={'training_plan': training_plan},
        client_protocols={},
        server_averaging_plan=avg_plan,
        client_config=client_config,
        server_config=server_config
    )

def validate_user(model_id, owner):

    user_table = dynamodb.Table('user_table')
    try:
        user_response = user_table.get_item(Key={'user_id': owner})
    except:
        return jsonify({'error': 'failed to query dynamodb'}), 500

    if user_response['Items'] is None:
        return jsonify({'error': 'user not found'}), 400

    training_set = request.json.get('training_set')
    purchases = user_response['Items'][0]['datasets_purchased']
    if model_id in purchases:
        return True
    return False

if __name__ == '__main__':
    app.run()







