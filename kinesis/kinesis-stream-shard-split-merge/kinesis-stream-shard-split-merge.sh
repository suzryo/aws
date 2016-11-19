
# Kinesis Stream シャード増減スクリプト
# (kinesis-stream-shard-split-merge-function.sh)


# 実行例
# . ./kinesis-stream-shard-split-merge-function.sh
# STREAM_NAME='stream-1'
#
# 有効シャード確認
# get-json-active-shards ${STREAM_NAME} | jq .
# 
# シャード倍増
# split-shards ${STREAM_NAME}
#
# シャード半減
# merge-shards ${STREAM_NAME}


## シャード倍増(x2)

function split-shards () {
   STREAM_NAME=$1
   JSON_DESC_STREAM=`get-json-active-shards ${STREAM_NAME}`

   echo ${JSON_DESC_STREAM} | jq .
   echo ${JSON_DESC_STREAM}| jq -r  "[.ShardId, .HashKeyRange.StartingHashKey, .HashKeyRange.EndingHashKey]|@csv" | sed 's/"//g' | while read -r TMP1; do

      IFS=","
      set -- $TMP1
      SHARD_ID=$1
      STARTING_HASH=$2
      ENDING_HASH=$3

      IFS=$' \t\n'

      # 分割地点となるハッシュ値計算
      NEW_STARTING_HASH=`expr \( ${ENDING_HASH} - ${STARTING_HASH} \) / 2 + ${STARTING_HASH} + 1`

      echo "STREAM_NAME: ${STREAM_NAME}"
      echo "SHARD_ID: ${SHARD_ID}"
      echo "NEW_STARTING_HASH: ${NEW_STARTING_HASH}"

      kinesis-split-shard ${STREAM_NAME} ${SHARD_ID} ${NEW_STARTING_HASH}

   done

   get-json-active-shards ${STREAM_NAME} | jq .

}



## シャード半減(1/2)

function merge-shards () {
   STREAM_NAME=$1
   i=0

   JSON_DESC_STREAM=`get-json-active-shards ${STREAM_NAME}`
   echo ${JSON_DESC_STREAM} | jq .

   echo ${JSON_DESC_STREAM} | jq -r '[.ShardId]|@csv'| sed 's/"//g' | sort |  while read -r TMP1; do

      if [ ${i} -eq 0 ] ; then
         echo "$TMP1"
         SHARD_TO_MERGE="${TMP1}"
         i=1
      else
         ADJACENT_SHARD="${TMP1}"
         echo "STREAM_NAME: $STREAM_NAME"
         echo "SHARD_TO_MERGE: $SHARD_TO_MERGE"
         kinesis-merge-shard ${STREAM_NAME} ${SHARD_TO_MERGE} ${ADJACENT_SHARD}
         i=0
      fi  
   done

   get-json-active-shards ${STREAM_NAME}| jq .

}


## シャード分割

function kinesis-split-shard () {
   STREAM_NAME=$1
   SHARD_ID=$2
   NEW_STARTING_HASH=$3

   aws kinesis split-shard --stream-name ${STREAM_NAME} \
     --shard-to-split ${SHARD_ID}  \
     --new-starting-hash-key ${NEW_STARTING_HASH}

   check-stream-active ${STREAM_NAME}

}

## シャード統合
function kinesis-merge-shard () {
   STREAM_NAME=$1
   SHARD_TO_MERGE=$2
   ADJACENT_SHARD=$3

   aws kinesis merge-shards --stream-name ${STREAM_NAME} \
     --shard-to-merge ${SHARD_TO_MERGE}  \
     --adjacent-shard-to-merge ${ADJACENT_SHARD}

   check-stream-active ${STREAM_NAME}

}

## シャードステータス確認
# split-shard, merge-shard の 完了検知)
function check-stream-active () {
   STREAM_NAME=$1

   while :
   do
     sleep 1
     r="`aws kinesis describe-stream --stream-name ${STREAM_NAME} | jq -r .StreamDescription.StreamStatus`"
     if [ ${r} = "ACTIVE" ]; then
       break
     fi
   done
}


## 有効シャードのみ取得

function get-json-active-shards () {
   STREAM_NAME=$1

   aws kinesis describe-stream --stream-name ${STREAM_NAME} \
   | jq '.StreamDescription.Shards[]' \
   | jq 'select(.SequenceNumberRange.EndingSequenceNumber == null)' \
   | jq -c .

}



