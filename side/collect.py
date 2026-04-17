import subprocess
import os
import sys
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

WEB_ACCESS_SCRIPT = "./web_access_dsa.sh"
RESULT_FOLDER = "profile_results"
WEB_LIST = "web_list.txt"
WEB_LIST_OTHER = "web_list_other.txt"

### Configurations
# Number of traces per website
ITER_NUM = 300

# Transfer and buffer size for making contentions
XFER_SIZE_SINK = 1048576
BUF_SIZE_SINK = 64

# DSA Device and WQ number
DSA_NUM_SINK = 0
WQ_NUM_SINK = 1

# Monitoring time per trace
PROBE_TIME_SEC=7

# CPU affinity settings
CORE_WEB = 1
CORE_SINK = 2

def url_to_filename(url: str) -> str:
    if url.startswith("http://"):
        url = url[len("http://"):]
    elif url.startswith("https://"):
        url = url[len("https://"):]
    return url.replace(".", "_").replace("/", "_")

def main():
    websites = []
    with open(WEB_LIST, "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip()
            if domain:
                websites.append(f"https://{domain}")

    websites_other = []
    with open(WEB_LIST_OTHER, "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip()
            if domain:
                websites_other.append(f"https://{domain}")

    websites += websites_other

    os.makedirs(RESULT_FOLDER, exist_ok=True)

    for web in websites:
        if web in websites_other:
            iter_num = 1
        else:
            iter_num = ITER_NUM

        for i in range(iter_num):
            web_access_cmd = [
                "taskset", "-c", str(CORE_WEB),
                WEB_ACCESS_SCRIPT,
                web
            ]

            result_path = os.path.join(RESULT_FOLDER, str(i) + "_" + url_to_filename(web))

            sink_cmd = [
                "taskset", "-c", str(CORE_SINK),
                "./sink",
                f"--xfer_size={XFER_SIZE_SINK}",
                f"--buf_size={BUF_SIZE_SINK}",
                f"--dsa={DSA_NUM_SINK}",
                f"--wq={WQ_NUM_SINK}",
                f"--probe_time_sec={PROBE_TIME_SEC}",
                f"--path={result_path}"
            ]

            current_probe = web + " (" + str(i + 1) + "/" + str(ITER_NUM) + ")"
            sys.stdout.write('\r\033[K' + current_probe.rstrip() + '\n')
            sys.stdout.flush()
            sink_proc = subprocess.Popen(
                sink_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            time.sleep(0.5)
            web_proc = subprocess.Popen(
                web_access_cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            sink_proc.wait()
            web_proc.wait()
            time.sleep(0.5)

if __name__ == "__main__":
    main()
