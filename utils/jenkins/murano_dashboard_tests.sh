#!/bin/bash

set -x

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

# Functions
#-------------------------------------------------------------------------------
function start_xvfb_session() {

    export DISPLAY=:${VFB_DISPLAY_NUM}

    fonts_path="/usr/share/fonts/X11/misc/"
    if [ "$DISTRO_BASED_ON" == "redhat" ]; then
        fonts_path="/usr/share/X11/fonts/misc/"
    fi

    # Start XVFB session
    sudo Xvfb -fp "${fonts_path}" "${DISPLAY}" -screen 0 "${VFB_DISPLAY_SIZE}x${VFB_COLOR_DEPTH}" &

    # Start VNC server
    sudo apt-get install --yes x11vnc
    x11vnc -bg -forever -nopw -display "${DISPLAY}" -ncache 10
    sudo iptables -I INPUT 1 -p tcp --dport 5900 -j ACCEPT

    cat << EOF
********************************************************************************
*
*   Floating IP: ${FLOATING_IP_ADDRESS}
*   VNC connection string: vncviewer ${FLOATING_IP_ADDRESS}::5900
*
********************************************************************************
EOF

    # Launch window manager
    sudo apt-get install --yes openbox
    exec openbox &
}

function run_nosetests() {
    local tests=$*
    local retval=0

    $NOSETESTS_CMD -s -v \
        --with-xunit \
        --xunit-file="${WORKSPACE}/artifacts/report/test_report.xml" \
        $tests || retval=$?

    return $retval
}

function run_tests() {
    local retval=0

    pushd "${PROJECT_TESTS_DIR}"

    mkdir -p "${WORKSPACE}/artifacts/report"

    TESTS_STARTED_AT=($(date +'%Y-%m-%d %H:%M:%S'))
    case "${PROJECT_NAME}" in

        'murano-dashboard'|'python-muranoclient')
            if [[ -n "${EXECUTE_TESTS_BY_TAG}" ]]; then
                echo "Custom test configuration found. Executing..."
                run_nosetests -a "${EXECUTE_TESTS_BY_TAG}" || retval=$?
            else
                run_nosetests sanity_check || retval=$?
            fi
        ;;
    esac

    TESTS_FINISHED_AT=($(date +'%Y-%m-%d %H:%M:%S'))

    if [ $retval -ne 0 ]; then
        cat << EOF
List of murano processes:
********************************************************************************
$(pgrep -l -f -a murano)
********************************************************************************
EOF
    fi

    popd

    ensure_no_heat_stacks_left || retval=$?

    return $retval
}

#-------------------------------------------------------------------------------
BUILD_STATUS_ON_EXIT='TESTS_FAILED'

start_xvfb_session

run_tests

BUILD_STATUS_ON_EXIT='TESTS_SUCCESS'

exit 0