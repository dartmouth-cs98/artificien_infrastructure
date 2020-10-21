import boto3
import pprint
from boto3.dynamodb.conditions import Key
from aws_cdk import core
from artificien_infrastructure.dynamo_db_stack import DynamoDBStack


def get_sample_table_attributes():
    app = core.App()
    db = DynamoDBStack(app, "artificien-infrastructure", env={'region': 'us-east-1'})
    return db.enterprise_table_name, db.user_table_name, db.app_table_name, db.model_table_name,  db.dataset_table_name, db.region


def test_update_sample_table():
    """ Generate Sample Data for the Hello World Table"""

    # Get attributes
    enterprise_table_name, user_table_name, app_table_name, model_table_name, dataset_table_name, region_name = get_sample_table_attributes()

    # Test that the DynamoDB creation worked (using boto DynamoDB client):
    dynamodb = boto3.resource('dynamodb', region_name=region_name)

    # ---------------------------------------POPULATE DATABASES--------------------------------------------------

    # -------------------------------------------ENTERPRISE-------------------------------------------------

    
    table = dynamodb.Table(enterprise_table_name)

    # ----------Enterprise-------------
    # PK------[enterprise_id]:S
    # ---------------------------------
    # -----[num_models]:N
    # -----[enterprise_account_email]:S
    # -----[num_users]:N
    # -----[users]<<:M
    # ---------------------------------

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
        batch.put_item(Item={"enterprise": "healthInsuranceGuys",
                            'num_models': 1,
                            'enterprise_account_email': "healthInsuranceGuys@hotmail.com",
                            'num_users': 2,
                            'users': None
                       })

    # -------------------------------------------USER-------------------------------------------------


    usr_table = dynamodb.Table(user_table_name)
    
    # ----------User-------------
    # PK------[user_id]:S
    # ---------------------------------
    # -----[is_developer]:BOOL
    # -----[user_account_email]:S
    # -----[name]:S
    # -----[enterprise]:M
    # -----[models]<<:M
    # -----[bank_info]<<
    # ---------------------------------

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with usr_table.batch_writer() as batch:
        batch.put_item(Item={"user_id": "mSmith42",
                            'is_developer': False,
                            'user_account_email': 'michael_smith@gmail.com',
                            'name': "Michael Smith",
                            'enterprise': "healthInsuranceGuys",
                            'models': None,
                            'bank_info': {
                                'bank_number': 4321,
                                'bank': "Citibank" # no idea what this should look like tbh
                            }
                       })
        batch.put_item(Item={"user_id": "mKenney",
                            'is_developer': True,
                            'user_account_email': 'alexander.b.quill.21@dartmouth.edu',
                            'name': "Matt Kenney",
                            'enterprise': "healthInsuranceGuys",
                            'models': None,
                            'bank_info': {
                                'bank_number': 1001,
                                'bank': "Bank Of America"
                            }
                       })

    # --------------------------------------------APP-----------------------------------------------

    # ----------App-------------
    # PK------[app_id]
    # ---------------------------------
    # -----[dataset]:M
    # -----[grid]:M
    # ---------------------------------

    app_table = dynamodb.Table(app_table_name)


    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with app_table.batch_writer() as batch:
        batch.put_item(Item={"app_id": "Tinder",
                            'dataset': None,
                            'grid': None
                       })

    # --------------------------------------------MODEL-----------------------------------------------

    # ----------MODEL-------------
    # PK------[model_id]
    # ---------------------------------
    # -----[active_status]:BOOL
    # -----[owner]:M
    # -----[date_submitted]:S YYYYMMDD ISO _8601
    # ---------------------------------

    model_table = dynamodb.Table(model_table_name)


    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with model_table.batch_writer() as batch:
        batch.put_item(Item={"model_id": "testModelOne",
                            'active_status': True,
                            'owner': "mSmith42",
                            'date_submitted': '20201019'
                       })
        batch.put_item(Item={"model_id": "testModelTwo",
                            'active_status': False,
                            'owner': "mKenney",
                            'date_submitted': '20200621'
                       })

    # --------------------------------------------DATASET---------------------------------------------

    # ----------DATASET-------------
    # PK------[dataset_id]
    # ---------------------------------
    # -----[app]:M
    #------[name]:S
    # -----[logo_image_url]:S
    # -----[category]:S
    # -----[num_devices]:N
    # ---------------------------------

    model_table = dynamodb.Table(dataset_table_name)


    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with model_table.batch_writer() as batch:
        batch.put_item(Item={"dataset_id": "testDataSetOne",
                            'app': None,
                            'name': "tinderLocation",
                            'logo_image_url': 'https://i.pinimg.com/originals/c4/5e/1d/c45e1dcbf128ecf7ea3222a4c76829bb.jpg',
                            'category': 'location',
                            'num_devices': 42
                       })

def test_sample_table_queryable():
    """ Test that the DynamoDB creation worked (using boto DynamoDB client) """
    # Get attributes
    enterprise_table_name, user_table_name, app_table_name, model_table_name, dataset_table_name, region_name = get_sample_table_attributes()

    # Attempt GET
    dynamodb = boto3.resource('dynamodb', region_name=region_name)

    target_table_hits = 5
    hits = 0
    table_misses = []
    pp = pprint.PrettyPrinter(indent=2)

    table_names = [enterprise_table_name, user_table_name, app_table_name, model_table_name, dataset_table_name]

    for table_name in table_names:
        table = dynamodb.Table(table_name)
        response = None

        if table_name == enterprise_table_name:
            response = table.get_item(Key={"enterprise": "healthInsuranceGuys"})

        elif table_name == user_table_name:
            response = table.get_item(Key={"user_id": "mKenney"})

        elif table_name == app_table_name:
            response = table.get_item(Key={"app_id": "Tinder"})

        elif table_name == model_table_name:
            response = table.get_item(Key={"model_id": "testModelOne"})

        elif table_name == dataset_table_name:
            response = table.get_item(Key={"dataset_id": "testDataSetOne"})
        
        if response: 
            hits+=1
            print("\n------------SUCCESS: {}------------\nRESPONSE:".format(hits))
            pp.pprint(response)
        else: table_misses.append(table_name)

    if target_table_hits == hits:
        print("\n------------SUCCESS ALL------------\n")

    else:
        print("FAIL ON: {}".format(table_misses))


def populate_and_query():
    test_update_sample_table()
    test_sample_table_queryable()

populate_and_query()
