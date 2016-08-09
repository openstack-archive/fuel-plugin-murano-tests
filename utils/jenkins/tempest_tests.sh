#!/usr/bin/env bash
set -x

export SSH_OPTS='-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
export FUEL_PASSWD='r00tme'

SNAPSHOT_NAME=$(dos.py snapshot-list "$ENV_NAME" | tail -1 | awk '{print $1}')

dos.py revert-resume "$ENV_NAME" "$SNAPSHOT_NAME"

ADMIN_NODE_IP=$(dos.py net-list $ENV_NAME | tail -1 | awk '{print $2}' | sed 's|/.*||g' | sed 's|.$|2|g')

echo "LOG: fuel-master ip=$ADMIN_NODE_IP"

CONTROLLER_ID=`echo 'fuel node | \
                     grep controller | \
                     awk '\''{print $1}'\'' | \
                     head -1' | \
                     sshpass -p "$FUEL_PASSWD" \
              ssh "$SSH_OPTS" -T root@"$ADMIN_NODE_IP"`

wget -qO- https://get.docker.com/ | sh

##### Generating docker file and copying it to admin node,#####
##### and then to controller node                         #####
sudo -H docker build -t rally-tempest "$WORKSPACE/utils/jenkins/rally-tempest/latest"
sudo -H docker save -o ./dimage rally-tempest
sudo chown "${USER}:${USER}" ./dimage
sshpass -p "$FUEL_PASSWD" scp "$SSH_OPTS" dimage root@"$ADMIN_NODE_IP":/root/rally

echo "scp /root/rally node-$CONTROLLER_ID:/root/rally" | sshpass -p "$FUEL_PASSWD" ssh "$SSH_OPTS" -T root@"$ADMIN_NODE_IP"

echo 'wget -qO- https://get.docker.com/ | sh' > ssh_scr.sh

cat "$WORKSPACE/utils/jenkins/prepare_controller.sh" >> ssh_scr.sh

cat >> ssh_scr.sh <<'EOF'
docker load -i /root/rally
ID=$(docker images | awk '/rally/ {print $3}')
echo "LOG: INFO rally image id=$ID"

export DOCK_ID=$(docker run -tid -v /var/lib/rally-tempest-container-home-dir:/home/rally --net host "$ID")

sed -i "s|:5000|:5000/v2.0|g" /var/lib/rally-tempest-container-home-dir/openrc

docker exec -u root "$DOCK_ID" sed -i "s|\#swift_operator_role = Member|swift_operator_role=SwiftOperator|g" /etc/rally/rally.conf
docker exec "$DOCK_ID" setup-tempest

tempest_file=$(find / -name tempest.conf)

sed -i "79i max_template_size = 5440000" $tempest_file
sed -i "80i max_resources_per_stack = 20000" $tempest_file
sed -i "81i max_json_body_size = 10880000" $tempest_file
sed -i "24i volume_device_name = vdc" $tempest_file
sed -i "/[service_available]/a murano = True" $tempest_file
sed -i "/[service_available]/a glare = True" $tempest_file

echo "[application_catalog]" >> $tempest_file
echo "glare_backend = True" >> $tempest_file

deployment=$(docker exec "$DOCK_ID" bash -c "rally deployment list | awk '/tempest/ {print \$2}'")

docker exec "$DOCK_ID" bash -c "source /home/rally/openrc && rally verify start --regex application_catalog --concurrency 2"

docker exec "$DOCK_ID" bash -c "rally verify results --json --output-file output.json"
docker exec "$DOCK_ID" bash -c "rm -rvf rally_json2junit && git clone https://github.com/greatehop/rally_json2junit && python rally_json2junit/rally_json2junit/results_parser.py output.json"
EOF

chmod +x ssh_scr.sh

##### Copying script to master node, then to controller #####
sshpass -p "$FUEL_PASSWD" scp "$SSH_OPTS" ssh_scr.sh root@"$ADMIN_NODE_IP":/root/ssh_scr.sh
echo "scp /root/ssh_scr.sh node-$CONTROLLER_ID:/root/ssh_scr.sh" | sshpass -p "$FUEL_PASSWD" ssh "$SSH_OPTS" -T root@"$ADMIN_NODE_IP"

##### Executing script from admin node on controller node: #####
EXEC_CMD="echo 'chmod +x /root/ssh_scr.sh && /bin/bash -xe /root/ssh_scr.sh > /root/log.log' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh $"SSH_OPTS" -T root@"$ADMIN_NODE_IP"

##########################################################
##### Copying results from controller to admin node: #####
##### and then to host in workspace folder           #####
##########################################################
GET_RES_CMD="scp node-$CONTROLLER_ID:/var/lib/rally-tempest-container-home-dir/verification.xml /root/verification.xml"
echo "$GET_RES_CMD" |  sshpass -p "$FUEL_PASSWD" ssh "$SSH_OPTS" -T root@"$ADMIN_NODE_IP"
sshpass -p "$FUEL_PASSWD" scp "$SSH_OPTS" root@"$ADMIN_NODE_IP":/root/verification.xml "$WORKSPACE/logs/"

GET_LOG_CMD="scp node-$CONTROLLER_ID:/root/log.log /root/log.log"
echo "$GET_LOG_CMD" |  sshpass -p "$FUEL_PASSWD" ssh "$SSH_OPTS" -T root@"$ADMIN_NODE_IP"
sshpass -p "$FUEL_PASSWD" scp "$SSH_OPTS" root@"$ADMIN_NODE_IP":/root/log.log "$WORKSPACE/logs/"

sudo rm -vf dimage
sudo rm -vf ssh_scr.sh

set +x
