# -*- coding: utf-8 -*-

# get-timelag-lambda-consumer.py
# lambda-consumer でPutするKinesisをトリガとして実行
# Getしたレコード、lamda-consumerの起動時刻(producers_unixtime_ms)との時間差を、CloudwatchLogsに出力

from __future__ import print_function

import base64
import json
import time
import commands

# print('Loading function')

def lambda_handler(event, context):
    #print("Received event: " + json.dumps(event, indent=2))

    client_hostname_ip = commands.getoutput("hostname -i")
    client_ifconfig_ip = commands.getoutput("/sbin/ifconfig|grep 'Bcast:0.0.0.0  Mask:255.255.255.0'| cut -f 2 -d ':' | cut -f 1 -d ' ' " )
    client_unixtime_ms = int(time.time()*1000)

    for record in event['Records']:
        # Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record['kinesis']['data'])
        #print("Decoded payload: " + payload)
        
        data = json.loads(payload)
        producers_unixtime_ms = int(data["producers_unixtime_ms"]) 
        producers_hostname_ip = str(data["producers_hostname_ip"]) 
        producers_ifconfig_ip = str(data["producers_ifconfig_ip"]) 

        client_timelag = client_unixtime_ms - producers_unixtime_ms

        list = {"timelag": client_timelag, "client_unixtime_ms": client_unixtime_ms, "client_hostname_ip": client_hostname_ip,"client_ifconfig_ip": client_ifconfig_ip, "producers_hostname_ip": producers_hostname_ip,"producers_ifconfig_ip": producers_ifconfig_ip,"producers_unixtime_ms": producers_unixtime_ms}

        s = json.dumps(list)
        print(s)


    return 'Successfully processed {} records.'.format(len(event['Records']))
