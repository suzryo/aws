# -*- coding: utf-8 -*-

# kinesis-lambda-stream-to-firehose.py
# AWS Lambda Console (Edit code inline)

from __future__ import print_function

import json
import base64
import boto3

# Configure firehose 
FirehoseConfig = {
  "region": "us-west-2",
  "DeliveryStreamname": "firehose-streamname"
}

firehose = boto3.client('firehose', region_name=FirehoseConfig['region'])
streamname = FirehoseConfig['DeliveryStreamname']


def lambda_handler(event, context):
    # Describe Check
    # DescribeFirehose(streamname)

    # GetData Stream
    s = []
    
    for u in event['Records']:
        # Kinesis data is base64 encoded so decode here
        t = base64.b64decode(u['kinesis']['data']) + "\n"

        if len(t) > 1 :
            p={ 'Data': str(t)  }
            s.insert(len(s),p)

    if len(s) > 1 :
        PutRecordBatchFirehose(streamname, s)


def PutRecordBatchFirehose(streamname, s):
    r = firehose.put_record_batch(
        DeliveryStreamName = streamname,
        Records = s
    )
    #print(str(r["ResponseMetadata"]["HTTPHeaders"]))
    #print(str(s))


def DescribeFirehose(d):
    r = firehose.describe_delivery_stream(
        DeliveryStreamName = d
    )
    print(str(r["ResponseMetadata"]["HTTPHeaders"]))


