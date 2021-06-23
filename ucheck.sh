#!/bin/sh

UP_FILE=/tmp/UPDATE
SERVER_FILE=/root/rfcomm-server.py
OLD_SERVER_FILE=/root/old.py

if [ -f "$UP_FILE" ]; then
    echo "$UP_FILE exists."

    tdiff=$(( `date +%s` - `stat -c %Y $UP_FILE` ))
    echo "Current time: $tdiff"
    if [ $tdiff -ge 300 ] ; then
        echo "Update corrupted!!! Restoring old update..."
        cp "$OLD_SERVER_FILE" "$SERVER_FILE"
        screen -XS rfcomm quit
        screen -dm -S rfcomm bash -c "python3 $SERVER_FILE"
        rm -f "$UP_FILE"
    fi
fi