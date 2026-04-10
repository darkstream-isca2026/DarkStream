#!/bin/bash
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script with sudo or as root."
  exit 1
fi

for GOVERNOR in /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor; do
    if [ -f "$GOVERNOR" ]; then
        CORE=$(echo "$GOVERNOR" | cut -d'/' -f6)
        
        echo "performance" > "$GOVERNOR"
        
        RESULT=$(cat "$GOVERNOR")
        echo "$CORE: $RESULT"
    fi
done

for CPU_DIR in /sys/devices/system/cpu/cpu[0-9]*; do
    CORE=$(basename "$CPU_DIR")
    for STATE_DIR in "$CPU_DIR"/cpuidle/state[0-9]*; do
        if [ -d "$STATE_DIR" ]; then
            STATE_NAME=$(cat "$STATE_DIR/name")
            DISABLE_FILE="$STATE_DIR/disable"
            
            if [ -f "$DISABLE_FILE" ]; then
                echo 1 > "$DISABLE_FILE"
                
                RESULT=$(cat "$DISABLE_FILE")
                echo "$CORE - $STATE_NAME: $([ "$RESULT" -eq 1 ] && echo "Disabled" || echo "Failed")"
            fi
        fi
    done
done

TARGET_USER=$1

if [ -z "$TARGET_USER" ]; then
    read -p "Enter the username to grant device ownership: " TARGET_USER
fi

if [ -z "$TARGET_USER" ]; then
    echo "Error: No username provided. Exiting."
    exit 1
fi

echo "Disabling device dsa0..."
accel-config disable-device dsa0

echo "Configuring work queues..."
accel-config config-wq --group-id=0 --mode=shared --wq-size=64 --threshold=64 --type=user --priority=10 --name="app0" --driver-name="user" dsa0/wq0.0
accel-config config-wq --group-id=1 --mode=dedicated --wq-size=64 --type=user --priority=10 --name="app1" --driver-name="user" dsa0/wq0.1

echo "Configuring engines..."
accel-config config-engine dsa0/engine0.0 --group-id=0
accel-config config-engine dsa0/engine0.1 --group-id=1

echo "Enabling device and work queues..."
accel-config enable-device dsa0
accel-config enable-wq dsa0/wq0.0
accel-config enable-wq dsa0/wq0.1

echo "Changing ownership of wqs..."
chown "$TARGET_USER" /dev/dsa/wq0.0
chown "$TARGET_USER" /dev/dsa/wq0.1
