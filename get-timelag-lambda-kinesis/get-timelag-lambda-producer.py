# -*- coding: utf-8 -*-

# get-timelag-lambda-producer.py

# 起動時刻(producers_unixtime_ms)
# Lambda実行環境のIP(producers_hostname_ip, producers_ifconfig_ip) をKinesisStreamにPut
# イベントトリガ(1min毎)で実行
# Putしたレコード、lamda-consumer で Getし、起動時間を比較する事でLambdaのタイムラグを計測

from __future__ import print_function

import json
import commands
import time
import boto3

client = boto3.client('kinesis')

#print('Loading function')

def lambda_handler(event, context):
    
    hostname_ip = commands.getoutput("hostname -i")
    ifconfig_ip = commands.getoutput("/sbin/ifconfig|grep 'Bcast:0.0.0.0  Mask:255.255.255.0'| cut -f 2 -d ':' | cut -f 1 -d ' ' " )
    unixtime_ms = int(time.time()*1000)
    
    list = {"producers_unixtime_ms": unixtime_ms, "producers_hostname_ip": hostname_ip, "producers_ifconfig_ip": ifconfig_ip}
    s = json.dumps(list)
    #print(s)

    put_record_kinesis(s,hostname_ip)

def put_record_kinesis(s,pk):
    
    r = client.put_record(
        StreamName='stream01',
        Data=s,
        PartitionKey=pk
    )
    
    #print(r)