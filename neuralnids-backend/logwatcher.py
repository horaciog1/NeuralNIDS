import os
import time
import json
EVE_LOG = "/var/log/suricata/eve.json"

def watcher(socket):
    with open(EVE_LOG, "r") as f:
        # Read the last line of the file
        f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if not line:
                # If no new line, wait a bit and check again
                time.sleep(0.5)
                continue
            # Process the line
            data = json.loads(line)
            if data.get("event_type") == "alert":
                # send the alert data through the websocket
                socket.emit("alert", data)