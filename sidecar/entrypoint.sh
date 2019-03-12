#!/bin/sh
set -e -o xtrace

# USER_ID=${LOCAL_USER_ID:-9001}
# GROUP_ID=${LOCAL_GROUP_ID:-9001}

# echo "Starting with UID : $USER_ID and GID : $GROUP_ID"
# usermod -u $USER_ID nobody
# groupmod -g $GROUP_ID nobody

# /usr/bin/supervisord -c /etc/supervisor/supervisord.conf

python /autopilot.py start --service ${REG_SERVICE_NAME} --consul-host http://consul:8500

REG_SERVICE_ID=`cat /usr/app/service.id`
REG_PROXY_ID=`cat /usr/app/proxy.id`

python /watch.py start --service ${REG_SERVICE_NAME} --consul-host http://consul:8500 &
/usr/app/http &
/usr/local/bin/envoy --config-path /usr/app/envoy-bootstrap.yaml  -l debug --service-cluster ${REG_PROXY_ID} --service-node ${REG_PROXY_ID}
exec "$@"