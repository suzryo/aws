import boto3
import json
import os
import urllib.parse
import gzip
from datetime import datetime
import base64
import re
from itertools import groupby
from operator import itemgetter

s3 = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')

def lambda_handler(event, context):
  z = parse_s3_event(event)
  bucket_name = z['bucket_name']
  key = z['key']

  print ('bucket_name: ' + bucket_name)
  print ('key: ' + key)
  response =s3.get_object(Bucket=bucket_name, Key=key)
  body = gzip.decompress(response['Body'].read()).decode('utf-8').splitlines()

  a = sort_log(body) 
  b = aggregate_log_by_group(a)
  if len(b) > 0:
    r = put_cloudwatch(b)
  
def parse_s3_event(event):
  a = json.loads(event['Records'][0]['Sns']['Message'])
  z = {}
  z['bucket_name'] = a['Records'][0]['s3']['bucket']['name']
  z['key'] = urllib.parse.unquote_plus(a['Records'][0]['s3']['object']['key'], encoding='utf-8')
  return z

def sort_log(data):

  d = []
  for a in data:
    b = json.loads(a)
    c = {}
    if 'request_uri_host' in b.keys():
      if 'timestamp' in b.keys():

        for e in get_aggregation_url():
          if (b['request_uri_scheme'] + '://' + b['request_uri_host'] + b["request_uri_path"]).startswith(e):

            c["request_uri_host"] = b['request_uri_host']
            c["timestamp_min"] = datetime.strptime(b['timestamp'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(second=0, microsecond=0)
            c["timestamp"] = b['timestamp']
            c["received_bytes"] = b['received_bytes']
            c["sent_bytes"] = b['sent_bytes']
            c["aggregation_url"] = e
          
            d.append(c)

  e = sorted(d, key=itemgetter('request_uri_host','aggregation_url','timestamp_min','timestamp'))
  return e

def aggregate_log_by_group(data):

  a = data
  j = []

  for b in groupby(a, key=itemgetter('request_uri_host','aggregation_url','timestamp_min')):

    d = []
    e = []
    h = {}

    for c in b[1]:
      d.append(c['received_bytes'])
      e.append(c['sent_bytes'])
      f = c['timestamp']
      h['request_uri_host'] = c['request_uri_host']
      h['aggregation_url'] = c['aggregation_url']

    h['received_bytes_sum'] = sum(d)
    h['received_bytes_min'] = min(d)
    h['received_bytes_max'] = max(d)
    h['sent_bytes_sum'] = sum(e)
    h['sent_bytes_min'] = min(e)
    h['sent_bytes_max'] = max(e)
    h['timestamp'] = datetime.strptime(f, '%Y-%m-%dT%H:%M:%S.%fZ').replace(microsecond=0)
    h['logcount'] = len(d)

    i = gen_metricdata_list(h)
    j.extend(i)

  return j

def gen_metricdata_list(a):

  CfnStackName = os.environ['CfnStackName']

  b = {
        'MetricName': 'sent_bytes',
        'Dimensions':  [{'Name': 'request_uri_host','Value': a['request_uri_host']}, {'Name': 'aggregation_url','Value': a['aggregation_url']}, {'Name': 'StackName','Value': CfnStackName}],
        'Timestamp': a['timestamp'],
        'StatisticValues': {
          'SampleCount': a['logcount'],
          'Sum': a['sent_bytes_sum'],
          'Minimum': a['sent_bytes_min'],
          'Maximum': a['sent_bytes_max'],
        },
        'Unit': "Bytes"
  }

  c = {
        'MetricName': 'received_bytes',
        'Dimensions':  [{'Name': 'request_uri_host','Value': a['request_uri_host']}, {'Name': 'aggregation_url','Value': a['aggregation_url']}, {'Name': 'StackName','Value': CfnStackName}],
        'Timestamp': a['timestamp'],
        'StatisticValues': {
          'SampleCount': a['logcount'],
          'Sum': a['received_bytes_sum'],
          'Minimum': a['received_bytes_min'],
          'Maximum': a['received_bytes_max'],
        },
        'Unit': "Bytes"
  }

  return [b,c]

def put_cloudwatch(data):
  b = []
  for a in data:
    b.append(a)
    if len(b) > 10:
      c = put_cloudwatch_batch(b)
      b = []
  if len(b) > 0:
    c = put_cloudwatch_batch(b)
  return c

def put_cloudwatch_batch(data):
  #print(str(data))

  r = cloudwatch.put_metric_data(
    Namespace = 'alb_log' ,
    MetricData = data
  )
  return r

def get_aggregation_url():
  a = os.environ['AggregationUrls'].split(',')
  if len(a) > 0:
    return a
