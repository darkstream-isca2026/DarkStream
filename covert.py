import subprocess
import time
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import random
import math
import argparse
import os
import re
import statistics

LATENCY_RESULT_FILE_NAME = "latency_result"
EVALUATION_FILE_PATH = "covert_result"

### Configurations
# Transfer and buffer size for making contentions
XFER_SIZE_SOURCE = 4
XFER_SIZE_SINK =1
BUF_SIZE_SOURCE = 64
BUF_SIZE_SINK = 64

# DSA Device and WQ number
DSA_NUM_SOURCE = 0
DSA_NUM_SINK = DSA_NUM_SOURCE
WQ_NUM_SOURCE = 0
WQ_NUM_SINK = 1

# CPU core
CORE_SOURCE = 1
CORE_SINK = 2

LATENCY_THRESHOLD = 1700
OUTLIER_THRESHOLD = 10000
BIT_LENGTH = 128
HEADER_PATTERN = ["high", "low", "high", "low", "high", "low", "high", "low"]

INTERVAL_LIST = [50000, 40000, 35000, 30000, 25000, 20000, 15000, 14000, 13000, 12500, 10000, 9000, 8000]

def sleep_us(microseconds):
    target = time.perf_counter_ns() + microseconds * 1000
    while time.perf_counter_ns() < target:
        pass

def classify_signal(lat):
    if lat >= LATENCY_THRESHOLD:
        return "high"
    else:
        return "low"

def bit_restore(interval, df, merged_segment_info, payload):
    found = False
    payload_start_ts = -1
    payload_length = len(payload)

    for seg in merged_segment_info:
        if seg.iloc[0]["signal"] == "high":
            header_pattern_candidate = []
            header_start_ts_candidate = int(seg.iloc[0]["timestamp"])
            current_ts = header_start_ts_candidate
            for i in range(len(HEADER_PATTERN)):
                subset = df[(df["timestamp"] >= current_ts) & (df["timestamp"] <= current_ts + interval)]
                latency_list = subset["latency"].tolist()

                if latency_list == []:
                    continue
                median_value = statistics.median(latency_list)

                if median_value > LATENCY_THRESHOLD:
                    header_pattern_candidate.append("high")
                else:
                    header_pattern_candidate.append("low")

                current_ts += interval

            if header_pattern_candidate == HEADER_PATTERN:
                payload_start_ts = current_ts
                found = True
        if found:
            break

    if not found:
        return False, False

    bitstream = ""
    current_ts = payload_start_ts

    for i in range(BIT_LENGTH):
        subset = df[(df["timestamp"] >= current_ts) & (df["timestamp"] <= current_ts + interval)]
        latency_list = subset["latency"].tolist()

        if latency_list != []:
            median_value = statistics.median(latency_list)
            if median_value > LATENCY_THRESHOLD:
                bit = "1"
            else:
                bit = "0"
        elif bitstream != "":
            bit = bitstream[-1]
        else:
            bit = "0"

        bitstream += bit
        current_ts += interval

    correct = 0
    zero_to_one_errors = 0
    one_to_zero_errors = 0

    if len(bitstream) != len(payload):
        return False, False
    total = min(len(payload), len(bitstream))
    for i in range(total):
        if payload[i] == bitstream[i]:
            correct += 1
        elif payload[i] == "0":
            zero_to_one_errors += 1
        else:
            one_to_zero_errors += 1

    e = 1 - correct / payload_length

    num_zeros = payload.count("0")
    num_ones = payload.count("1")

    zero_to_one_error_rate = zero_to_one_errors / num_zeros if num_zeros > 0 else 0
    one_to_zero_error_rate = one_to_zero_errors / num_ones if num_ones > 0 else 0

    def H(e):
        if e == 0 or e == 1:
            return 0
        return -e * math.log2(e) - (1 - e) * math.log2(1 - e)

    def calc_capacity(one_to_zero, zero_to_one):
        e0, e1 = min(one_to_zero, zero_to_one), max(one_to_zero, zero_to_one)

        Hb_e0 = 0 if e0 in (0, 1) else -e0 * math.log2(e0) - (1-e0) * math.log2(1-e0)
        Hb_e1 = 0 if e1 in (0, 1) else -e1 * math.log2(e1) - (1-e1) * math.log2(1-e1)

        denominator = 1 - e0 - e1
        
        if denominator == 0:
            return 0.0

        capa = (e0 / denominator) * Hb_e1 - ((1 - e1) / denominator) * Hb_e0 + math.log2(1 + pow(2, (Hb_e0 - Hb_e1) / denominator))
        return capa

    capa = calc_capacity(one_to_zero_error_rate, zero_to_one_error_rate)

    return capa, e

def filter():
    file_path = LATENCY_RESULT_FILE_NAME

    timestamp = []
    latency_result = []
    with open(file_path, "r") as f:
        for line in f:
            timestamp.append(float(line.split(", ")[0]))
            latency_result.append(int(line.split(", ")[1].strip()))

    from pykalman import KalmanFilter

    kf = KalmanFilter(initial_state_mean=1400, n_dim_obs=1)
    smoothed_state_means, _ = kf.smooth(latency_result)

    filtered_latencies = []
    filtered_timestamps = []

    for lat, ts in zip(smoothed_state_means, timestamp):
        if lat < LATENCY_THRESHOLD - 100 or lat > LATENCY_THRESHOLD + 100:
            filtered_latencies.append(lat)
            filtered_timestamps.append(ts)

    delete_indices = []
    for i in range(1, len(filtered_latencies) - 1):
        prev_type = classify_signal(filtered_latencies[i - 1])
        next_type = classify_signal(filtered_latencies[i + 1])
        current_type = classify_signal(filtered_latencies[i])
        if prev_type == next_type and current_type != prev_type:
            delete_indices.append(i)

    for idx in reversed(delete_indices):
        del filtered_latencies[idx]
        del filtered_timestamps[idx]

    df = pd.DataFrame({
        "timestamp": filtered_timestamps,
        "latency": filtered_latencies
    })

    df["signal"] = df["latency"].apply(lambda x: "outlier" if x >= OUTLIER_THRESHOLD else ("high" if x >= LATENCY_THRESHOLD else "low"))

    segments = []
    segment_start_idx = 0

    for i in range(1, len(df)):
        prev_signal = df.iloc[i - 1]["signal"]
        curr_signal = df.iloc[i]["signal"]
        
        if prev_signal != curr_signal:
            segment = df.iloc[segment_start_idx:i].copy()
            segments.append(segment)
            segment_start_idx = i

    if segment_start_idx < len(df):
        segments.append(df.iloc[segment_start_idx:].copy())

    return df, segments

def covert(interval):
    payload = "".join(random.choice(["0", "1"]) for _ in range(BIT_LENGTH))

    source_cmd = [
        "taskset", "-c", str(CORE_SOURCE),
        "./source",
        f"--xfer_size={XFER_SIZE_SOURCE}",
        f"--buf_size={BUF_SIZE_SOURCE}",
        f"--dsa={DSA_NUM_SOURCE}",
        f"--wq={WQ_NUM_SOURCE}",
        f"--interval_cycle={interval}",
        f"--bitstream={payload}"
    ]

    sink_cmd = [
        "taskset", "-c", str(CORE_SINK),
        "./sink",
        f"--xfer_size={XFER_SIZE_SINK}",
        f"--buf_size={BUF_SIZE_SINK}",
        f"--dsa={DSA_NUM_SINK}",
        f"--wq={WQ_NUM_SINK}",
        f"--interval_cycle={interval}",
        f"--bit_legnth={BIT_LENGTH}"
    ]

    sink_proc = subprocess.Popen(sink_cmd)
    sleep_us(interval/100)
    source_proc = subprocess.Popen(source_cmd, stdout=subprocess.PIPE, text=True)

    stdout, _ = source_proc.communicate()
    output = stdout.strip()
    sink_proc.wait()

    df, segment_info = filter()
    capa, normal_error_rate = bit_restore(interval, df, segment_info, payload)

    if capa is False:
        return False, False, False, False

    match = re.search(r"(\d+)s\s+(\d+)ns", output)
    if match:
        seconds = int(match.group(1))
        nanoseconds = int(match.group(2))
        total_ns = seconds * 1_000_000_000 + nanoseconds

    interval_ns = total_ns / (len(HEADER_PATTERN) + BIT_LENGTH)

    freq = 1 / (interval_ns/1e9)
    bw = capa * freq

    return freq, capa, bw, normal_error_rate
    

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--interval_cycle', default=False)
    parser.add_argument('-n', '--num_iteration', default="100")
    parser.add_argument('-p', '--path', default=False)
    args = parser.parse_args()

    if args.interval_cycle is not False:
        interval_list = [int(args.interval_cycle)]
    else:
        interval_list = INTERVAL_LIST

    num_iter = int(args.num_iteration)

    if args.path is not False:
        os.makedirs(EVALUATION_FILE_PATH, exist_ok=True)
        eval_path = os.path.join(EVALUATION_FILE_PATH, args.path)
        if os.path.exists(eval_path):
            print("File", args.path, "exists.")
            return
        f = open(eval_path, "w")
    else:
        f = False

    for interval in interval_list:
        print("-----------------------")
        print("Interval:", interval, "cycles")
        success_count = 0
        capa_bw_list = []
        freq = -1
        while True:
            freq, capa, bw, normal_error_rate = covert(interval)
            if capa is False:
                continue

            capa_bw_list.append([freq, capa, bw, normal_error_rate])
            success_count += 1
            if success_count == num_iter:
                break

        avg_freq = np.average([x[0] for x in capa_bw_list])
        avg_capa = np.average([x[1] for x in capa_bw_list])
        avg_bw = np.average([x[2] for x in capa_bw_list])
        avg_ner = np.average([x[3] for x in capa_bw_list])
        result_list = [avg_freq, avg_capa, avg_bw, avg_ner]
        print("Frequency:", avg_freq/1024, "KHz")
        print("Capacity:", avg_capa)
        print("Bandwith:", avg_bw/1024, "Kbps")
        if f:
            f.write(" ".join(str(item) for item in result_list) + "\n")

if __name__ == "__main__":
    main()
