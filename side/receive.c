#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include "common.h"
#include <linux/idxd.h>
#include <time.h>

#define MAX_INDEX 200000000
int latency_arr[MAX_INDEX];
struct timespec timestamp[MAX_INDEX];

void timespec_diff(struct timespec *start, struct timespec *end, struct timespec *diff) {
    if ((end->tv_nsec - start->tv_nsec) < 0) {
        diff->tv_sec  = end->tv_sec - start->tv_sec - 1;
        diff->tv_nsec = 1000000000 + end->tv_nsec - start->tv_nsec;
    } else {
        diff->tv_sec  = end->tv_sec - start->tv_sec;
        diff->tv_nsec = end->tv_nsec - start->tv_nsec;
    }
}

int receive(uint64_t *(data_buf[][BUF_SIZE]), struct dsa_hw_desc *desc_buf,
                                             struct dsa_completion_record *comp_buf,
                                             int wq_fd, int xfer_size, int buf_size, int probe_time_sec, char* path_name) {
  int status = 0;
  uint64_t start, delay;
  int rc, retry;
  int i;
  int copy_latency;
  struct timespec start_time, target_time, current_time, delta;
  struct timespec probe_time;
  probe_time.tv_sec = probe_time_sec;
  probe_time.tv_nsec = 0;

  for (i = 0; i < buf_size; i++) {
    comp_buf[i].status          = 0;
    desc_buf[i].opcode          = DSA_OPCODE_MEMMOVE;
    desc_buf[i].flags           = IDXD_OP_FLAG_RCR | IDXD_OP_FLAG_CRAV;
    desc_buf[i].xfer_size       = xfer_size;
    desc_buf[i].src_addr        = (uintptr_t)data_buf[0][i];
    desc_buf[i].dst_addr        = (uintptr_t)data_buf[1][i];
    desc_buf[i].completion_addr = (uintptr_t)&(comp_buf[i]);
  }

  char *temp;
  clock_gettime(CLOCK_MONOTONIC_RAW, &start_time);
  target_time.tv_sec = start_time.tv_sec + probe_time.tv_sec;
  target_time.tv_nsec = start_time.tv_nsec + probe_time.tv_nsec;
  if (target_time.tv_nsec >= 1000000000L) {
            target_time.tv_sec += 1;
            target_time.tv_nsec -= 1000000000L;
  }
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
    clock_gettime(CLOCK_MONOTONIC_RAW, &current_time);
    while (comp_buf[i].status == 0 && retry++ < MAX_COMP_RETRY) {
      umonitor(&(comp_buf[i]));
      if (comp_buf[i].status == 0) {
        uint64_t delay = __rdtsc() + UMWAIT_DELAY;
        umwait(UMWAIT_STATE_C0_1, delay);
      }
    }
    comp_buf[i].status = 0;
    copy_latency = rdtsc() - start;
    latency_arr[latency_idx] = copy_latency;
    clock_gettime(CLOCK_MONOTONIC_RAW, &current_time);
    timestamp[latency_idx] = current_time;
    if(current_time.tv_sec > target_time.tv_sec || (current_time.tv_sec == target_time.tv_sec && current_time.tv_nsec > target_time.tv_nsec)){
      timespec_diff(&start_time, &current_time, &delta);
      break;
    }
    else if(i<buf_size-1)
      i++;
    else
      i = 0;
    latency_idx++;
  }

  FILE *fp = fopen(path_name, "wb");
  if (fp == NULL) {
      perror("file open error");
      return -1;
  }

  uint32_t count = (uint32_t)(latency_idx + 1);
  for (uint32_t i = 0; i < count; i++) {
      int v = latency_arr[i];
      if (v < 0) v = 0;
      uint32_t s = (uint32_t) v;
      if (fwrite(&s, sizeof(s), 1, fp) != 1) {
          perror("file write error");
          fclose(fp);
          return -1;
      }
  }
  fclose(fp);

  return status;
}
