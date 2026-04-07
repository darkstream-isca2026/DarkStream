#!/bin/bash
export DTO_USESTDC_CALLS=0
export DTO_COLLECT_STATS=1
export DTO_WAIT_METHOD=yield
export DTO_MIN_BYTES=8192
export DTO_CPU_SIZE_FRACTION=0.33
export DTO_AUTO_ADJUST_KNOBS=1
export DTO_WQ_LIST="wq0.0"
export DTO_DSA_CC=1

export LD_PRELOAD=./DTO/libdto.so.1.0
# Assume Chromium is installed at the default Playwright cache path
~/.cache/ms-playwright/chromium-1181/chrome-linux/chrome --headless=new --no-sandbox --enable-logging=stderr --log-level=3 2>/dev/null --dump-dom $1
