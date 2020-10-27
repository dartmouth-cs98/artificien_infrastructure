import boto3
import pprint
from boto3.dynamodb.conditions import Key
from aws_cdk import core
from artificien_infrastructure.dynamo_db_stack import DynamoDBStack

import datetime


# -------------------------------------------get_table_attributes-------------------------------------------------
# Gets table names from stack and assigns to variables. 

def get_table_attributes():
    app = core.App()
    db = DynamoDBStack(app, "artificien-infrastructure", env={'region': 'us-east-1'})
    return db.enterprise_table_name, db.user_table_name, db.app_table_name, db.model_table_name,  db.dataset_table_name, db.region


# -------------------------------------------update_enterprise_table-------------------------------------------------

# ----------Enterprise-------------
# PK------[enterprise_id]:S
# ---------------------------------
# -----[num_models]:N
# -----[enterprise_account_email]:S
# -----[num_users]:N
# -----[users]<<:M
# ---------------------------------

def update_enterprise_table(ID = "", num_models = 0, enterprise_account_email = "", num_users = 0, users = None):

    enterprise_table_name, _, _, _, _, region_name = get_table_attributes()
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(enterprise_table_name)

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
        batch.put_item(Item={"enterprise_id": str(ID),
                            'num_models': int(num_models),
                            'enterprise_account_email': str(enterprise_account_email),
                            'num_users': int(num_users),
                            'users': users
                       })

# -------------------------------------------USER-------------------------------------------------

  # ----------User-------------
    # PK------[user_id]:S
    # ---------------------------------
    # -----[is_developer]:BOOL
    # -----[user_account_email]:S
    # -----[name]:S
    # -----[enterprise]:M
    # -----[models]<<:M
    # -----[bank_info]<<{bank_number: N, bank: S}
    # ---------------------------------


def update_user_table(ID = "", is_developer = False, user_account_email = "", name = "", enterprise = "", bank_number = 0000, bank = ""):

    _, user_table_name, _, _, _, region_name = get_table_attributes()
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(user_table_name)

    with table.batch_writer() as batch:
        batch.put_item(Item={"user_id": str(ID),
                            'is_developer': is_developer,
                            'user_account_email': str(user_account_email),
                            'name': str(name),
                            'enterprise': str(enterprise),
                            'models': [], # not sure about this
                            'bank_info': {
                                'bank_number': int(bank_number),
                                'bank': str(bank) # no idea what this should look like tbh
                            }
                       })
    print("Done")
    
# --------------------------------------------APP-----------------------------------------------

    # ----------App-------------
    # PK------[app_id]:S
    # ---------------------------------
    # -----[dataset]:M
    # -----[grid]:M
    # -----[logo_image_url]:S
    # ---------------------------------

def update_app_table(ID = "", dataset = "", grid = None, logo_image_url = None):

    _, _, app_table_name, _, _, region_name = get_table_attributes()
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(app_table_name)

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
       batch.put_item(Item={"app_id": str(ID),
                            'dataset': str(dataset),
                            'grid': grid,
                            'logo_image_url': str(logo_image_url),
                       })

# --------------------------------------------MODEL-----------------------------------------------

    # ----------MODEL-------------
    # --------- P Index -------------
    # PK------[model_id]:S
    # --------- S Index -------------
    # PK ---[owner]:S
    # SK---[active_status]:N
    # ---------------------------------
    # -----[date_submitted]:S YYYYMMDD ISO _8601
    # ---------------------------------


def update_model_table(ID = "", active_status = 1, owner = None, date_submitted = datetime.datetime.today().strftime('%Y%m%d')):
    _, _, _, model_table_name, _, region_name = get_table_attributes()
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(model_table_name)

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
       batch.put_item(Item={"model_id": str(ID),
                            "active_status": active_status,
                            "owner": str(owner),
                            "date_submitted": date_submitted
                       })


# --------------------------------------------DATASET---------------------------------------------

    # ----------DATASET-------------
    # ------------P Index--------------
    # PK------[dataset_id]
    # ------------S Index--------------
    # PK------[category]:S
    # SK------[num_devices]:N
    # ---------------------------------
    # -----[app]:M
    #------[name]:S
    # -----[logo_image_url]:S

    # ---------------------------------


def update_dataset_table(ID = "", app = "", name = "", logo_image_url = "", category = "", num_devices = 0):
    _, _, _, _, dataset_table_name, region_name = get_table_attributes()
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(dataset_table_name)

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
        batch.put_item(Item={"dataset_id": str(ID),
                            'app': str(app),
                            'name': str(name),
                            'logo_image_url': str(logo_image_url),
                            'category': str(category),
                            'num_devices': int(num_devices)
                       })


# -------------------- test_queryable ------------------- #
# Test to make sure that you can query all five tables
# This function is just to test if each table is QUERYABLE. All test query PKs are pre-populated, fake data. 

def test_queryable(ent_pk = None, usr_pk = None, app_pk = None, mdl_pk = None, data_pk = None):
    """ Test that the DynamoDB creation worked (using boto DynamoDB client) """
    arguments = [ent_pk, usr_pk, app_pk, mdl_pk, data_pk]
    print(arguments)

    enterprise_table_name, user_table_name, app_table_name, model_table_name, dataset_table_name, region_name = get_table_attributes()

    # Attempt GET
    dynamodb = boto3.resource('dynamodb', region_name=region_name)

    table_misses = {}
    pp = pprint.PrettyPrinter(indent=2)

    table_names = [enterprise_table_name, user_table_name, app_table_name, model_table_name, dataset_table_name]

    for i in range(len(table_names)):
        table = dynamodb.Table(table_names[i])

        if arguments[i] is None: # we didn't pass an argument, we're not trying to query this table. 
            # print("ARG: {}".format(arguments[i]))
            continue

        response = None

        if table_names[i] == enterprise_table_name and ent_pk:
            response = table.get_item(Key={"enterprise_id": str(ent_pk)})

        elif table_names[i] == user_table_name and usr_pk:
            response = table.get_item(Key={"user_id": str(usr_pk)})

        elif table_names[i] == app_table_name and app_pk:
            response = table.get_item(Key={"app_id": str(app_pk)})

        elif table_names[i] == model_table_name and mdl_pk:
            response = table.get_item(Key={"model_id": str(mdl_pk[0]), "active_status": mdl_pk[1]})

        elif table_names[i] == dataset_table_name and data_pk:
            response = table.get_item(Key={"dataset_id": str(data_pk[0]), "num_devices": data_pk[1]})
        
        try:
            print(response)
            if response["Item"]: # we passed a PK AND that PK returns nonempty JSON
                print("\n------------SUCCESS------------\nRESPONSE:")
                pp.pprint(response)
                print("------------------------------------------------------------------------")
                continue

        except KeyError:
            table_misses[table_names[i]] = "KeyError: " + str(arguments[i])

    if len(table_misses) != 0:
        print("------------------------------------------------------------------------------------------------------------------------------------------------\nFAILS: {}".format(table_misses))

    else:
        print("\n------------SUCCESS ALL------------\n")


if __name__ == '__main__':
    update_enterprise_table(ID = "fakeEnt", num_models = 2, enterprise_account_email = "fakeEnt@gmail.com", num_users = 1, users = None)
    update_model_table(ID = "model1", active_status = 1, owner = "QUILL", date_submitted = datetime.datetime.today().strftime('%Y%m%d'))
    test_queryable("fakeEnt", "QUILL", "_", "modelOne")
    # update_user_table(ID = "Shreyas", is_developer = True, user_account_email = "shreyas.shreyas@gmail.com", name = "Shreyas", enterprise = "Bain", bank_number = 1492, bank = "Bank of New York")
