## Side-channel

### 1. **Install Playwright and Chromium.**
Execute the following command to install Playwright (v1.54.0) and the corresponding Chromium browser:

```bash
npx playwright@1.54.0 install chromium
```
Upon successful installation, the Chromium binary should be located at the following path:
`~/.cache/ms-playwright/chromium-1181/chrome-linux/chrome`

### 2. **Building the Intel® DSA Transparent Offload (DTO) Library**
The [Intel® DSA Transparent Offload (DTO)](https://github.com/intel/DTO) library is designed to offload memory operations from existing software to the DSA hardware.

Ensure the DTO repository is correctly initialized within the project:
```bash
git submodule update --init --recursive
```

Navigate to the DTO directory and compile the library:
```bash
cd DTO
make libdto
cd ..
```

### 3. **Configure the DSA device.**
To ensure consistent and stable experimental results, this script locks the CPU frequency to its maximum level and activates work queues (WQs) 0 and 1, along with the engines on DSA device 0. Additionally, it assigns access permissions for these work queues to the user specified as a command-line argument.

```bash
sudo ./config_side.sh username
```

### 4. **Website Trace Collection**
Execute the following script to begin collecting side-channel traces from website accesses:
```bash
make
python3 collect.py
```

#### How it works:
**DSA-Offloaded Chromium Execution:** The script invokes `web_access_dsa.sh`, which utilizes the DTO library to offload Chromium's memory operations to the DSA.

**Side-Channel Monitoring:** Simultaneously, the script launches a `sink` program to monitor and record the latency of memory operations caused by the target website's activities.

#### Experimental Scope:
The collection process covers two sets of data to ensure both depth and breadth:

**Target Sites:** 43 websites (listed in `web_list.txt`) are visited 300 times each.

**Other Sites (for open-world setting):** 4,000 websites (listed in `web_list_other.txt`) are visited once each.

#### Output:
The latency traces observed by the sink during each execution are automatically saved in the `profile_results` directory.

### 5. **Trace Visualization**
Execute the following script to convert the raw latency traces stored in `profile_results` into visual images for analysis. The generated visualizations will be saved in the `profile_results_img` directory.
```bash
python3 results_to_image.py
```

### 6. **Training and Classification**
Execute the following script to train the image classifier and evaluate its performance on the collected website traces:
```bash
python3 classify_img.py
```
#### How it works:
**Dataset Partitioning:** The script automatically splits the visualized traces into three distinct datasets: `data/train`, `data/val`, and `data/eval`.

**Model Training:** It trains a ResNet-18 image classifier over 10 epochs using the training and validation sets.

**Evaluation & Output:** After training, the script evaluates the model's classification accuracy using the evaluation dataset.
It generates a confusion matrix to visualize the model's performance, which is saved as `confusion_matrix.png`.
