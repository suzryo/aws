import boto3
import json
import os
import urllib.parse
import csv

import gzip
from datetime import datetime
import base64

s3 = boto3.client('s3')
firehose = boto3.client('firehose')

def lambda_handler(event, context):
  bucket_name = event['Records'][0]['s3']['bucket']['name']
  key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
  print ('bucket_name: ' + key)

  response =s3.get_object(Bucket=bucket_name, Key=key)
  
  body = gzip.decompress(response['Body'].read()).decode('utf-8').splitlines()

  e = []
  for line in body:
    f = parse_log(line)
    e.append({'Data': f})




  PutRecordBatchFirehose(e)


def parse_log(line):

  z = {}
  a = line.split('"')
  b = a[0].split(' ')

  # Check ALB Log
  if len(b) == 13:
    if b[2].split('/')[0] == 'app':
      z["type"] = b[0]
      z["timestamp"] = b[1]
      z["elb"] = b[2]
      z["client_port"] = b[3].split(':')[1]
      z["target_port"] = b[4].split(':')[1]
      z["request_processing_time"] = float(b[5])
      z["target_processing_time"] = float(b[6])
      z["response_processing_time"] = float(b[7])
      z["elb_status_code"] = int(b[8])
      z["target_status_code"] = int(b[9])
      z["received_bytes"] = float(b[10])
      z["sent_bytes"] = float(b[11])

      z["request"] = a[1]
      z["user_agent"] = a[3]

      c = a[4].split(' ')
      if len(c) == 5:
        z["ssl_cipher"] = c[1]
        z["ssl_protocol"] = c[2]
        z["target_group_arn"] = c[3]

      z["trace_id"] = a[5]
      z["domain_name"] = a[7]
      z["chosen_cert_arn"] = a[9]
      z["matched_rule_priority"] = a[10]

      if len(a) > 10:
        d = a[10].split(' ')
        if len(d) > 1:
          z["matched_rule_priority"] = d[1]

      # fluent-plugin-elb-access-log compatible
      z["client"] = b[3].split(':')[0]
      z["target"] = b[4].split(':')[0]

      z["request.method"] = z["request"].split(' ')[0]
      z["request.uri"] = z["request"].split(' ')[1]
      z["request.http_version"] = z["request"].split(' ')[2]

      e = urllib.parse.urlparse(z["request.uri"])
      z["request.uri.scheme"] = e.scheme
      z["request.uri.user"] = e.username
      z["request.uri.host"] = e.hostname
      z["request.uri.port"] = e.port
      z["request.uri.path"] = e.path
      z["request.uri.query"] = e.query
      z["request.uri.fragment"] = e.fragment

  #print(z)
  return json.dumps(z) + "\n"


def PutRecordBatchFirehose(s):

  s = firehose.put_record_batch(
        DeliveryStreamName = 'firehose-0422',
        Records = s
  )
  print(str(r["ResponseMetadata"]["HTTPHeaders"]))


