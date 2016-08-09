#!/usr/bin/env bash

SSH_OPTS='-o UserKnownHostsFile=/dev/null \
          -o StrictHostKeyChecking=no'

SNAPSHOT_NAME=$(dos.py snapshot-list "$ENV_NAME" | tail -1 | awk '{print $1}')

dos.py revert-resume "$ENV_NAME" "$SNAPSHOT_NAME"

ADMIN_NODE_IP=$(dos.py net-list $ENV_NAME | tail -1 | awk '{print $2}' | sed 's|/.*||g' | sed 's|.$|2|g')

echo $ADMIN_NODE_IP

CONTROLLER_ID=`echo 'fuel node | \
                     grep controller | \
                     awk '\''{print $1}'\'' | \
                     head -1' | \
                     sshpass -p 'r00tme' \
              ssh -o UserKnownHostsFile=/dev/null \
                  -o StrictHostKeyChecking=no \
                  -T root@"$MASTER_NODE_IP"`

sudo apt-get install docker -y

##### Generating docker file and copying it to admin node,#####
##### and then to controller node                         #####
sudo docker build -t rally-tempest "$WORKSPACE/utils/jenkins/rally-tempest/latest"
sudo docker save -o ./dimage rally-tempest
sshpass -p 'r00tme' scp -o UserKnownHostsFile=/dev/null \
                        -o StrictHostKeyChecking=no dimage root@"$ADMIN_NODE_IP":/root/rally
echo "scp /root/rally node-$CONTROLLER_ID:/root/rally" | \
      sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null \
                              -o StrictHostKeyChecking=no \
                              -T root@"$ADMIN_NODE_IP"

echo 'wget -qO- https://get.docker.com/ | sh' > ssh_scr.sh

cat $WORKSPACE/utils/jenkins/prepare_controller.sh >> ssh_scr.sh
echo '' >> ssh_scr.sh

echo 'docker load -i /root/rally' >> ssh_scr.sh


echo 'docker images | grep rally > temp.txt' >> ssh_scr.sh
echo 'awk '\''{print $3}'\'' temp.txt > ans' >> ssh_scr.sh
echo 'ID=`cat ans`' >> ssh_scr.sh
echo 'echo $ID' >> ssh_scr.sh

echo 'docker run -tid -v /var/lib/rally-tempest-container-home-dir:/home/rally --net host "$ID" > dock.id' >> ssh_scr.sh
echo 'DOCK_ID=`cat dock.id`' >> ssh_scr.sh
echo 'sed -i "s|:5000|:5000/v2.0|g" /var/lib/rally-tempest-container-home-dir/openrc' >> ssh_scr.sh
echo 'docker exec -u root "$DOCK_ID" sed -i "s|\#swift_operator_role = Member|swift_operator_role=SwiftOperator|g" /etc/rally/rally.conf' >> ssh_scr.sh
echo 'docker exec "$DOCK_ID" setup-tempest' >> ssh_scr.sh

echo 'file=`find / -name tempest.conf`' >> ssh_scr.sh

echo 'sed -i "79i max_template_size = 5440000" $file ' >> ssh_scr.sh
echo 'sed -i "80i max_resources_per_stack = 20000" $file ' >> ssh_scr.sh
echo 'sed -i "81i max_json_body_size = 10880000" $file ' >> ssh_scr.sh
echo 'sed -i "24i volume_device_name = vdc" $file ' >> ssh_scr.sh
echo 'sed -i "/[service_available]/a murano = True" $file' >> ssh_scr.sh
echo 'sed -i "/[service_available]/a glare = True" $file' >> ssh_scr.sh

echo 'echo "[application_catalog]" >> $file' >> ssh_scr.sh
echo 'echo "glare_backend = True" >> $file' >> ssh_scr.sh

echo 'deployment=$(docker exec "$DOCK_ID" bash -c "rally deployment list" | awk '\''/tempest/{print $2}'\'')' >> ssh_scr.sh

echo 'docker exec "$DOCK_ID" bash -c "source /home/rally/openrc && rally verify start --regex application_catalog --concurrency 1 --system-wide"' >> ssh_scr.sh

echo 'docker exec "$DOCK_ID" bash -c "rally verify results --json --output-file output.json" ' >> ssh_scr.sh
echo 'docker exec "$DOCK_ID" bash -c "rm -rf rally_json2junit && git clone https://github.com/greatehop/rally_json2junit && python rally_json2junit/rally_json2junit/results_parser.py output.json" ' >> ssh_scr.sh
chmod +x ssh_scr.sh

##### Copying script to master node, then to controller #####
sshpass -p 'r00tme' scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no ssh_scr.sh root@"$MASTER_NODE_IP":/root/ssh_scr.sh
echo "scp /root/ssh_scr.sh node-$CONTROLLER_ID:/root/ssh_scr.sh" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$MASTER_NODE_IP"

##### Executing script from admin node on controller node: #####
EXEC_CMD="echo 'chmod +x /root/ssh_scr.sh && /bin/bash -xe /root/ssh_scr.sh > /root/log.log' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$MASTER_NODE_IP"

##########################################################
##### Copying results from controller to admin node: #####
##### and then to host in workspace folder           #####
##########################################################
GET_RES_CMD="scp node-$CONTROLLER_ID:/var/lib/rally-tempest-container-home-dir/verification.xml /root/verification.xml"
echo "$GET_RES_CMD" |  sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$MASTER_NODE_IP"
sshpass -p 'r00tme' scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@"$MASTER_NODE_IP":/root/verification.xml "$WORKSPACE/logs/"

GET_LOG_CMD="scp node-$CONTROLLER_ID:/root/log.log /root/log.log"
echo "$GET_LOG_CMD" |  sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$MASTER_NODE_IP"
sshpass -p 'r00tme' scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no root@"$MASTER_NODE_IP":/root/log.log "$WORKSPACE/logs/"
