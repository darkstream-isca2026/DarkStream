<div align=center>

# DarkStream: Exploiting Internal Throughput Contention in Data Streaming Accelerator for Timing Attacks

</div>

This repository holds the artifact for the ISCA 2026 paper: "DarkStream: Exploiting Internal Throughput Contention in Data Streaming Accelerator for Timing Attacks".

This repository provides the source code to implement and evaluate two key scenarios:

1.  **Covert Channel:** Tools for establishing and measuring the performance (bandwidth and capacity) of a covert channel.
2.  **Website Fingerprinting (Side-Channel):** Scripts for side-channel trace collection, model training, and classification accuracy evaluation.

## Prerequisites

### 🖥 Hardware Requirements
* **Processor:** 4th Gen Intel® Xeon® Scalable Processor (Sapphire Rapids) or newer.
    * The CPU must have at least one Intel® Data Streaming Accelerator (DSA) device enabled.
* **GPU:** NVIDIA GPU (RTX A5000 or equivalent/better).
    * Required for model training and classification in the Website Fingerprinting experiments.
* **Storage:** At least 30 GB of free disk space.

### 🐧 Software Requirements
* **Operating System:** Ubuntu 22.04.5 LTS (Jammy Jellyfish).
* **Linux Kernel:** Version 6.13.1 or newer.
* **Compiler:** GCC 11.4.0.
* **Language Environment:** Python 3.10.12.
* **System Utilities:**  **`accel-config`:** Required for configuring Intel DSA devices (Work queues, Engines, and Groups). 
* **Privileges:** `root/sudo` access is necessary for system and DSA device configurations.

Before proceeding, please ensure that the Intel DSA is properly configured on your system by referring to Chapter 2 and 9 of the [Intel® Data Streaming Accelerator User Guide](https://www.intel.com/content/www/us/en/content-details/759709/intel-data-streaming-accelerator-user-guide.html).

To manage Intel DSA devices, you need the [`accel-config`](https://github.com/intel/idxd-config/) utility.

**Resolve dependencies**
```bash
apt install build-essential
apt install autoconf automake autotools-dev libtool pkgconf asciidoc xmlto
apt install uuid-dev libjson-c-dev libkeyutils-dev libz-dev libssl-dev
apt install debhelper devscripts debmake quilt fakeroot lintian asciidoctor
apt install file gnupg patch patchutils
```

**Build**
```bash
git clone https://github.com/intel/idxd-config
cd idxd-config
./autogen.sh
./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64
make
make check
sudo make install
```

**Verify installation**
```bash
accel-config --version
```

## Usage
For detailed instructions on how to set up and execute each experiment, please refer to the **`README.md`** file located within each respective directory.

## Disclaimer

This artifact is provided for educational and research purposes only. The techniques described (covert channel and side-channel analysis) are intended to demonstrate architectural vulnerabilities and should not be used for malicious activities. The authors are not responsible for any misuse of this software.
