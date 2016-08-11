#!/bin/bash

set -x

# Virtual framebuffer settings
#-----------------------------
VFB_DISPLAY_SIZE='1280x1024'
VFB_COLOR_DEPTH=16
VFB_DISPLAY_NUM=22
#-----------------------------

export SSH_OPTS='-o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no'
export FUEL_PASSWD='r00tme'

SNAPSHOT_NAME=$(dos.py snapshot-list "$ENV_NAME" | tail -1 | awk '{print $1}')

dos.py revert-resume "$ENV_NAME" "$SNAPSHOT_NAME"


ADMIN_NODE_IP=$(dos.py net-list $ENV_NAME | tail -1 | awk '{print $2}' | sed 's|/.*||g' | sed 's|.$|2|g')

echo "LOG: fuel-master ip=$ADMIN_NODE_IP"

sudo apt-get install --yes sshpass

#####This variable should be set for pagination test running#####
sed -i 's#MURANO_REPO_URL =.*#MURANO_REPO_URL = '\''http://localhost:8099'\''#g' "$WORKSPACE/muranodashboard/local/local_settings.d/_50_murano.py"

CONTROLLER_ID=`echo 'fuel node | \
                     grep controller | \
                     awk '\''{print $1}'\'' | \
                     head -1' | \
                     sshpass -p "$FUEL_PASSWD" \
              ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"`

echo "LOG: controller_id=$CONTROLLER_ID"

##### Upload the murano-dashboard repo on controller node in home #####
EXEC_CMD="echo 'apt-get install --yes git && git clone https://github.com/openstack/murano-dashboard.git' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##### Installing Firefox version 46.0 #####
FIREFOX_CMD="echo 'apt-get install --yes firefox && \
             apt-get remove --yes firefox && \
             wget https://ftp.mozilla.org/pub/firefox/releases/46.0/linux-x86_64/en-US/firefox-46.0.tar.bz2 && \
             tar -xjf firefox-46.0.tar.bz2 && \
             rm -rf /opt/firefox && \
             mv firefox /opt/firefox46 && \
             ln -s /opt/firefox46/firefox /usr/bin/firefox'"
EXEC_CMD="$FIREFOX_CMD | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##### Installing Prerequisites on controller#####
EXEC_CMD="echo 'apt-get install --yes python-pip xvfb xfonts-100dpi xfonts-75dpi xfonts-cyrillic xorg dbus-x11 && \
          pip install --upgrade pip && \
          pip install -U selenium nose' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##### Copying script to master node, then to controller #####
sshpass -p "$FUEL_PASSWD" scp ${SSH_OPTS} "$WORKSPACE/utils/jenkins/parser.py" "root@${ADMIN_NODE_IP}:/root/parser.py"
echo "scp /root/parser.py/ node-${CONTROLLER_ID}:murano-dashboard/muranodashboard/tests/functional/config/" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##### Run python script for preparing config.conf for tests#####
EXEC_CMD="echo '. /root/openrc && cd murano-dashboard/muranodashboard/tests/functional/config/ && chmod +x parser.py && ./parser.py -i /root/openrc' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

fonts_path="/usr/share/fonts/X11/misc/"

##### Running Xvfb #####
XVFB_SESSION="echo 'Xvfb -fp \"${fonts_path}\" :${VFB_DISPLAY_NUM} -screen 0 \"${VFB_DISPLAY_SIZE}x${VFB_COLOR_DEPTH}\" &'"
EXEC_CMD="$XVFB_SESSION | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##### Configuring VNC. Port forwarding example ssh -L 127.0.0.1:8000:controller_ip:5900  user@server #####
EXEC_CMD="echo 'apt-get install --yes x11vnc && x11vnc -bg -forever -nopw -display :${VFB_DISPLAY_NUM} -ncache 10 && iptables -I INPUT 1 -p tcp --dport 5900 -j ACCEPT' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##### Run tests #####
RUN_TESTS="echo 'export DISPLAY=:${VFB_DISPLAY_NUM} && nosetests -sv murano-dashboard/muranodashboard/tests/functional/sanity_check.py --with-xunit --xunit-file /root/test_report.xml' | ssh -T node-$CONTROLLER_ID"
echo "$RUN_TESTS" | sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"

##########################################################
##### Copying results from controller to admin node: #####
##### and then to host in workspace folder           #####
##########################################################
GET_REP_CMD="scp node-$CONTROLLER_ID:/root/test_report.xml /root/test_report.xml"
echo "$GET_REP_CMD" |  sshpass -p "$FUEL_PASSWD" ssh ${SSH_OPTS} -T root@"$ADMIN_NODE_IP"
sshpass -p "$FUEL_PASSWD" scp ${SSH_OPTS} root@"$ADMIN_NODE_IP":/root/test_report.xml "$WORKSPACE/logs/"

exit 0
