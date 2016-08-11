#!/bin/bash

set -x

# Virtual framebuffer settings
#-----------------------------
VFB_DISPLAY_SIZE='1280x1024'
VFB_COLOR_DEPTH=16
VFB_DISPLAY_NUM=22
#-----------------------------

SSH_OPTS='-o UserKnownHostsFile=/dev/null \
          -o StrictHostKeyChecking=no'

SNAPSHOT_NAME=$(dos.py snapshot-list "$ENV_NAME" | tail -1 | awk '{print $1}')

dos.py revert-resume "$ENV_NAME" "$SNAPSHOT_NAME"


ADMIN_NODE_IP=$(dos.py net-list $ENV_NAME | tail -1 | awk '{print $2}' | sed 's|/.*||g' | sed 's|.$|2|g')

echo $ADMIN_NODE_IP

sudo apt-get install --yes sshpass

CONTROLLER_ID=`echo 'fuel node | \
                     grep controller | \
                     awk '\''{print $1}'\'' | \
                     head -1' | \
                     sshpass -p 'r00tme' \
              ssh -o UserKnownHostsFile=/dev/null \
                  -o StrictHostKeyChecking=no \
                  -T root@"$ADMIN_NODE_IP"`

echo $CONTROLLER_ID

##### Upload the murano-dashboard repo on controller node in home #####
EXEC_CMD="echo 'apt-get install --yes git && git clone https://github.com/openstack/murano-dashboard.git' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

##### Installing Firefox version 46.0 #####
FIREFOX_CMD="echo 'apt-get install --yes firefox && \
             apt-get remove --yes firefox && \
             wget https://ftp.mozilla.org/pub/firefox/releases/46.0/linux-x86_64/en-US/firefox-46.0.tar.bz2 && \
             tar -xjf firefox-46.0.tar.bz2 && \
             rm -rf /opt/firefox && \
             mv firefox /opt/firefox46 && \
             ln -s /opt/firefox46/firefox /usr/bin/firefox'"
EXEC_CMD="$FIREFOX_CMD | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

##### Installing Prerequisites on controller#####
EXEC_CMD="echo 'apt-get install --yes python-pip xvfb && \
          pip install --upgrade pip && \
          pip install -U selenium nose' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

sshpass -p 'r00tme' scp -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no "/home/stack/fuel-plugin-murano-tests/utils/jenkins/parser.py" "root@$ADMIN_NODE_IP:/root/"

EXEC_CMD="yum install -y sshpass && scp /root/parser.py/ node-$CONTROLLER_ID:murano-dashboard/muranodashboard/tests/functional/config/"
echo "$EXEC_CMD" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

EXEC_CMD="echo 'cd murano-dashboard/muranodashboard/tests/functional/config/ && chmod +x parser.py && ./parser.py -i /root/openrc' | ssh -T node-$CONTROLLER_ID"
echo "$EXEC_CMD" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

export DISPLAY=:${VFB_DISPLAY_NUM}
fonts_path="/usr/share/fonts/X11/misc/"

XVFB_SESSION="echo 'apt-get install --yes xfonts-100dpi xfonts-75dpi xfonts-cyrillic xorg dbus-x11 && \
              Xvfb -fp "${fonts_path}" "${DISPLAY}" -screen 0 "${VFB_DISPLAY_SIZE}x${VFB_COLOR_DEPTH}"& && \
              apt-get install --yes x11vnc && x11vnc -bg -forever -nopw -display "${DISPLAY}" -ncache 10 && \
              sudo iptables -I INPUT 1 -p tcp --dport 5900 -j ACCEPT' | ssh -T node-$CONTROLLER_ID"
echo "$XVFB_SESSION" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

RUN_TESTS="echo 'export DISPLAY=:"${DISPLAY}" && nosetests -sv murano-dashboard/muranodashboard/tests/functional/sanity_check.py' | ssh -T node-$CONTROLLER_ID"
echo "$RUN_TESTS" | sshpass -p 'r00tme' ssh -o UserKnownHostsFile=/dev/null -o StrictHostKeyChecking=no -T root@"$ADMIN_NODE_IP"

exit 0
