#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include "common.h"
#include <linux/idxd.h>
#include <time.h>
#define MAX_INDEX 10000000

int latency_arr[MAX_INDEX];
uint64_t timestamp[MAX_INDEX];

int receive(uint64_t *(data_buf[][BUF_SIZE]), struct dsa_hw_desc *desc_buf,
                                             struct dsa_completion_record *comp_buf,
                                             int wq_fd, int xfer_size, int buf_size, int interval_cycle, int payload_length) {
  uint64_t start, delay;
  uint64_t start_tsc, target_tsc, current_tsc, total_interval_cycles;
  int rc, retry;
  int i;
  int copy_latency;
  total_interval_cycles = interval_cycle * (payload_length*2);

  for (i = 0; i < buf_size; i++) {
    comp_buf[i].status          = 0;
    desc_buf[i].opcode          = DSA_OPCODE_MEMMOVE;
    desc_buf[i].flags           = IDXD_OP_FLAG_RCR | IDXD_OP_FLAG_CRAV;
    desc_buf[i].xfer_size       = xfer_size;
    desc_buf[i].src_addr        = (uintptr_t)data_buf[0][i];
    desc_buf[i].dst_addr        = (uintptr_t)data_buf[1][i];
    desc_buf[i].completion_addr = (uintptr_t)&(comp_buf[i]);
  }

  start_tsc = rdtsc();
  target_tsc = start_tsc + total_interval_cycles;
  int latency_idx = 0;
  i = 0;
  while(1){
    rc = 0;
    _mm_sfence();
    while(rc != sizeof(struct dsa_hw_desc)){
      rc = write(wq_fd, &desc_buf[i], sizeof(struct dsa_hw_desc));
    }
    start = rdtsc();
    retry = 0;
    while (comp_buf[i].status == 0 && retry++ < MAX_COMP_RETRY) {
      umonitor(&(comp_buf[i]));
      if (comp_buf[i].status == 0) {
        uint64_t delay = __rdtsc() + UMWAIT_DELAY;
        umwait(UMWAIT_STATE_C0_1, delay);
      }
    }
    current_tsc = rdtsc();
    comp_buf[i].status = 0;
    copy_latency = current_tsc - start;
    latency_arr[latency_idx] = copy_latency;
    timestamp[latency_idx] = current_tsc;

    if (current_tsc > target_tsc)
      break;
    else if(i<buf_size-1)
      i++;
    else
      i = 0;
    latency_idx++;
  }

  FILE *fp = fopen("latency_result", "w");
  if (fp == NULL) {
    perror("file open error");
    return -1;
  }

  for (int i = 0; i < latency_idx + 1; i++) {
    fprintf(fp, "%ld, %d\n", timestamp[i], latency_arr[i]);
  }

  fclose(fp);

  return 0;
}
