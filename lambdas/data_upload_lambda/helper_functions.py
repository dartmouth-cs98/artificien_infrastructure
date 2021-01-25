# Importing relevant packages
import os
import csv
import random
import boto3

# setting up connection with dynamoDB
region_name = os.environ["AWS_REGION"]
dynamodb = boto3.resource('dynamodb', region_name=region_name)
s3 = boto3.client('s3')

# Will only ever make a fake dataset from dataset table, so may as well declare it!
table = dynamodb.Table(os.environ['DYNAMO_TABLE'])
s3_bucket_name = os.environ['S3_BUCKET']


def get_random_words():
    f = open('words.txt', 'r')
    content = f.read()
    word_list = str.split(content)
    return word_list


def preprocess_dynamo_row(column_header, input):
    print("PK: {} Value: {}".format(column_header, input))
    response = table.get_item(Key={column_header: input})
    return response['Item']


# this function will grab the relevant rows (column header, min, max, num_rows)
def grab_relevant_info(column_header, input):
    # this grabs the dictionary of the row of data we want!
    dict = preprocess_dynamo_row(column_header, input)

    columns = []
    schema = []
    num_rows = 0
    ranges = []
    # correlation = []

    # grab the column headers; we assume that this is the right length of columns the data should be.
    columns = dict['attributes']

    # grab the data schema, we assume that this is per row (i.e. if 3 columns of data, this is the same length)
    schema = dict['attributeTypes']

    # grab the number of rows (fake data)
    num_rows = int(dict['num_devices'])  # this avoids any problem with that it is a Decimal value

    # to create ranges we need to make sure our data is not all string and/or binary
    num = 0  # we assume it IS all string/binary, the schema must prove us wrong
    for i in range(len(schema)):
        if schema[i] == "N":
            num = 1

    # this makes sure there is one number, i.e. there has to be a range!
    # if the bool is false there is no 'attributerange...' hence we need to instantiate a list somehow
    if (num == 1):
        mins = dict['attributeRangeMins']
        maxs = dict['attributeRangeMaxes']
    else:
        mins = []
        maxs = []

    # corresponding min and max of column; if string, make [0, 0]
    min_max_counter = 0  # this tracks the smaller array

    # go through each column and figure out if its range exists OR we must add a value suppose schema = [S, N, S],
    # then range only equals [[3, 10]], must append [0, 0] for index 0 and 2 so we can iterate cleanly in other
    # functions
    for i in range(len(columns)):
        if schema[i] == 'S':
            ranges.append([0, 0])
        elif schema[i] == 'B':
            ranges.append([0, 1])
        else:
            ranges.append([])
            ranges[i].append(float(mins[min_max_counter]))
            ranges[i].append(float(maxs[min_max_counter]))
            min_max_counter += 1

    # find correlation; this will be later. this supposes that we have another column of length n where 0 = no
    # correlation with anyone else a non-zero means that this column is a function of another column (so each
    # non-zero must occur at least twice!) a function of the other column goes both ways which enables flexibility in
    # terms of how we write the code (refer to my last PR in correlated_fake_data in our experimental repo)
    # correlation = list(dict['Correlation'])

    print("grab relevant info done")
    return columns, schema, num_rows, ranges  # ,correlation


# inputs: columns, discrete/continuous, ranges for each column, correlation, number of rows this has every column
# besides the first column be a function of the first column correlation: index of length n, 0 means no correlation
# with anything else, any non-zero int needs to have a pair (should be validated, will not be yet) assume earlier
# index is the one the later one is based on... doesn't really matter
def schematic_fake_data(columns, schema, ranges, num_rows):
    word_list = get_random_words()

    # input validation
    if len(columns) != len(ranges):
        return "incorrect lengths of columns in one of the first three inputs"
    elif num_rows <= 0:
        return "incorrect number of rows"

    # # this is a dictionary on that tracks the counts of each value in array
    # correlation_counter_dict = {}
    # validation_counter = 0

    # while validation_counter < len(correlation):
    #     if correlation[validation_counter] in correlation_counter_dict.keys():
    #         correlation_counter_dict[correlation[validation_counter]] += 1
    #     else:
    #         correlation_counter_dict[correlation[validation_counter]] = 1

    #     validation_counter += 1
    # val_list = (list(correlation_counter_dict.values()))
    # key_list = (list(correlation_counter_dict.keys()))
    # for i in val_list:
    #     if i < 2:
    #         if key_list[val_list.index(i)] != 0:
    #             return ("error: need a corresponding value with this correlation value")

    output_data = [columns]

    col_iterator = 0
    row_of_data = 1  # topline is the headers
    # write an array where each item is a row of fake data

    while row_of_data <= num_rows:

        output_data.append([])

        while len(columns) > col_iterator:

            # # if this is a "correlated column", need to find other column and make it a function of another
            # if (correlation[col_iterator] != 0):
            #
            #     # this finds if this current column is later
            #     temp = 0
            #     while temp < col_iterator:
            #
            #         # this means that this column is later
            #         if correlation[temp] == correlation[col_iterator]:
            #             output_data[row_of_data].append(output_data[row_of_data][temp] * 3 + random.random() * 5)
            #             temp = col_iterator + 2 # to cut out of the loop
            #             col_iterator += 1
            #         else:
            #             temp +=1
            #
            #     # if this column index is earlier, make it random
            #     if schema[col_iterator] == "int":
            #         output_data[row_of_data].append(random.randint(range[col_iterator][0], range[col_iterator][1]))
            #         col_iterator += 1
            #     else:
            #         output_data[row_of_data].append(range[col_iterator][0] + random.random() *
            #                                         (range[col_iterator][1] - range[col_iterator][0]))
            #         col_iterator += 1
            #
            # else:
            # if an integer or binary, which means they have an ACTUAL range, we select integer between the two!
            if schema[col_iterator] == "N" or schema[col_iterator] == "B":
                print(ranges)
                print(col_iterator)
                output_data[row_of_data].append(random.randint(ranges[col_iterator][0], ranges[col_iterator][1]))
                col_iterator += 1

            # if it a string, we just add a random word from our list of 1k words
            elif schema[col_iterator] == "S":
                rand_word = (word_list[random.randint(0, len(word_list) - 1)])
                output_data[row_of_data].append(rand_word)
                col_iterator += 1

            # if not an int, a double, so we get a random double from min to max (i.e. min + (random decimal from 0
            # --> 1)(max-min))
            else:
                output_data[row_of_data].append(
                    ranges[col_iterator][0] + random.random() * (ranges[col_iterator][1] - ranges[col_iterator][0]))
                col_iterator += 1

        col_iterator = 0
        row_of_data += 1

    print("schematic fake data done")
    return output_data


def convert_to_csv(columns, schema, ranges, num_rows, file_name):
    output = schematic_fake_data(columns, schema, ranges, num_rows)
    print(columns)
    print(schema)
    print(ranges)

    with open(file_name, 'w', newline='') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter=',',
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)

        x = 0
        while x < len(output):
            spamwriter.writerow(output[x])
            print(output[x])
            x += 1

    s3.upload_file(file_name, s3_bucket_name, file_name)


def query_to_csv(column_header, input):
    # first, get the dictionary
    right_info = grab_relevant_info(column_header, input)

    # parse the right info into the four values we need
    test_columns = right_info[0]
    test_schema = right_info[1]
    test_num_rows = right_info[2]
    test_ranges = right_info[3]

    # write the csv
    filename = ("/" + input + '.csv')
    convert_to_csv(test_columns, test_schema, test_ranges, test_num_rows, filename)
    print("convert to csv done")


def import_test():
    print('henlo')


def combine_ranges(mins, maxes):
    final_list = []
    for i in range(len(mins)):
        print(mins[i])
        print(maxes[i])
        pair_list = (mins[i], maxes[i])
        final_list.append(pair_list)
    return final_list
