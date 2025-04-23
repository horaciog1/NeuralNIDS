import os
import time
import json
EVE_LOG = "/var/log/suricata/eve.json"

def watcher(socket):
    alert_batch = []
    last_emission = time.time()
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
                # add the alert to the batch
                alert_batch.append(data)
            
            now = time.time()
            # If we have enough lines or it's been a while, emit them
            if len(alert_batch) >= 5 or (now - last_emission) > 10:
                socket.emit("alert_batch", json.dumps(alert_batch))
                alert_batch = []
                last_emission = now
            