import os
import sys
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from concurrent.futures import ProcessPoolExecutor, as_completed

RESULT_FOLDER = "profile_results"
IMG_FOLDER = "profile_results_img"
WEB_LIST = "web_list.txt"
WEB_LIST_OTHER = "web_list_other.txt"
ITER_NUM = 300

def url_to_filename(url: str) -> str:
    if url.startswith("http://"):
        url = url[len("http://"):]
    elif url.startswith("https://"):
        url = url[len("https://"):]
    return url.replace(".", "_").replace("/", "_")

def spike_filter(x, spike_thresh = 85000, neighbor_thresh = 85000):
    y = x.copy()
    n = len(x)
    if n < 3:
        return y

    for i, latency in enumerate(x):
        if i == 0 or i == n - 1:
            continue

        if latency < spike_thresh:
            continue

        prev_latency = x[i-1]
        next_latency = x[i+1]
        
        y[i] = 0.5 * (prev_latency+next_latency)

    return y

def average(x, interval = 100):
    data_list = list(x)

    if interval <= 0:
        raise ValueError("interval should be >0")

    downsampled_data = []
    for i in range(0, len(data_list), interval):
        end_index = i + interval
        chunk = data_list[i:end_index]
        
        if chunk is not []:
            downsampled_data.append(np.mean(chunk))
            
    return downsampled_data

def plot_one(args):
    result_path, plot_path, web = args
    try:
        data = np.fromfile(result_path, dtype=np.uint32)
        if data.size == 0:
            return plot_path, f"empty data: {result_path}"

        fig = plt.figure(figsize=(12, 8))

        ax = fig.add_subplot(111)
        ax.plot(average(spike_filter(data)))

        fig.tight_layout()
        fig.savefig(plot_path)
        plt.close(fig)
        return plot_path, None
    except FileNotFoundError:
        return plot_path, f"missing file: {result_path}"
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return plot_path, f"{type(e).__name__}: {e}"


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

    os.makedirs(IMG_FOLDER, exist_ok=True)

    tasks = []
    for web in websites:
        if web in websites_other:
            iter_num = 1
            folder_name = "other"
        else:
            iter_num = ITER_NUM
            folder_name = url_to_filename(web)

        for i in range(iter_num):
            if web in websites_other:
                idx = websites_other.index(web)
            else:
                idx = i
            result_path = os.path.join(RESULT_FOLDER, str(i) + "_" + url_to_filename(web))
            os.makedirs(os.path.join(IMG_FOLDER, folder_name), exist_ok=True)
            plot_path = os.path.join(IMG_FOLDER, folder_name, str(idx) + ".png")
            tasks.append((result_path, plot_path, web))

    total = len(tasks)
    if total == 0:
        print("No tasks found.")
        return

    max_workers = min(32, os.cpu_count() or 4)
    print(f"[INFO] Tasks={total}, workers={max_workers}")

    done_cnt = 0
    errors = 0
    try:
        with ProcessPoolExecutor(max_workers=max_workers) as ex:
            futures = [ex.submit(plot_one, t) for t in tasks]
            for fut in as_completed(futures):
                plot_path, err = fut.result()
                done_cnt += 1
                if err:
                    errors += 1
                    print(f"[ERR] {plot_path}: {err}")
                else:
                    if done_cnt % 50 == 0 or done_cnt == total:
                        print(f"[OK] {done_cnt}/{total}: {plot_path}")
    except KeyboardInterrupt:
        print("\nInterrupted by user. Shutting down workers…", file=sys.stderr)

    print(f"[DONE] {done_cnt}/{total} finished, errors={errors}")


if __name__ == "__main__":
    main()
