## Covert channel

1. **Configure the DSA device.** To ensure consistent and stable experimental results, this script locks the CPU frequency to its maximum level and activates work queues (WQs) 0 and 1, along with the engines on DSA device 0. Additionally, it assigns access permissions for these work queues to the user specified as a command-line argument.

```bash
sudo ./config_covert.sh username
```

2. **Execute the Covert Channel.** After the build process, use the provided Python script to execute the covert channel.

```bash
make
python3 covert.py
```

The script supports the following arguments:

- `-i`, `--interval_cycle`: The time interval used to transmit a single bit.

- `-n`, `--num_iteration`: The number of iterations to perform (the script reports the average values across these runs).

- `-p`, `--path`: The name of the output file. Results are saved in the covert_result/ directory.

If no arguments are provided, the script automatically evaluates several different intervals, performing 100 iterations for each. Upon completion of each interval, the script outputs the results (frequency, capacity, and bandwidth) directly to the shell.


### Tuning

The classification of bit values (0 or 1) in the covert channel is determined by the **`LATENCY_THRESHOLD`** variable, located at **line 34 of `covert.py`**.

Because side-channel latencies are highly sensitive to the specific hardware environment and background noise, you may need to fine-tune this threshold to optimize channel stability.
