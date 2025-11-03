#!/bin/bash

# Borrowed from https://github.com/voidtrance/voron-klipper-kinematicss

# Force script to exit if an error occurs
set -e

KLIPPER_PATH="${HOME}/klipper"
SYSTEMDDIR="/etc/systemd/system"
KINEMATICS_LIST="ratos_hybrid_corexy"
SRCDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )"/ && pwd )"

# Step 1:  Verify Klipper has been installed
function check_klipper() {
    if [ "$(sudo systemctl list-units --full -all -t service --no-legend | grep -F "klipper.service")" ]; then
        echo "Klipper service found!"
    else
        echo "Klipper service not found, please install Klipper first"
        exit -1
    fi
}

# Step 2: Check if the kinematicss are already present.
# This is a way to check if this is the initial installation.
function check_existing() {
    for kinematics in ${KINEMATICS_LIST}; do
        [ -L "${KLIPPER_PATH}/klippy/kinematics/${kinematics}.py" ] || return 1
    done
    return 0
}

# Step 3: Link kinematics to Klipper
function link_kinematicss() {
    echo "Linking kinematicss to Klipper..."
    for kinematics in ${KINEMATICS_LIST}; do
        ln -sf "${SRCDIR}/kinematics/${kinematics}/${kinematics}.py" "${KLIPPER_PATH}/klippy/kinematics/${kinematics}.py"
    done
}

function unlink_kinematicss() {
    echo "Unlinking kinematicss from Klipper..."
    for kinematics in ${KINEMATICS_LIST}; do
        rm -f "${KLIPPER_PATH}/klippy/kinematics/${kinematics}.py"
    done
}

# Step 4: Restart Klipper
function restart_klipper() {
    echo "Restarting Klipper..."
    sudo systemctl restart klipper
}

function verify_ready() {
    if [ "$(id -u)" -eq 0 ]; then
        echo "This script must not run as root"
        exit -1
    fi
}

do_uninstall=0

while getopts "k:u" arg; do
    case ${arg} in
        k) KLIPPER_PATH=${OPTARG} ;;
        u) do_uninstall=1 ;;
    esac
done

verify_ready
if ! check_existing; then
    link_kinematicss
else
    if [ ${do_uninstall} -eq 1 ]; then
        unlink_kinematicss
    fi
fi
restart_klipper
exit 0
