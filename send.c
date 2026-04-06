#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include "common.h"
#include <linux/idxd.h>
#include <time.h>

void timespec_diff(struct timespec *start, struct timespec *end, struct timespec *diff) {
    if ((end->tv_nsec - start->tv_nsec) < 0) {
        diff->tv_sec  = end->tv_sec - start->tv_sec - 1;
        diff->tv_nsec = 1000000000 + end->tv_nsec - start->tv_nsec;
    } else {
        diff->tv_sec  = end->tv_sec - start->tv_sec;
        diff->tv_nsec = end->tv_nsec - start->tv_nsec;
    }
}

void send(uint64_t *(data_buf[][BUF_SIZE]), struct dsa_hw_desc *desc_buf,
                                             struct dsa_completion_record *comp_buf,
                                             int wq_fd, int xfer_size, int buf_size, char *payload, int payload_length_byte, int interval_cycle) {
  uint64_t delay;
  uint64_t start_tsc, target_tsc, current_tsc;
  int rc, retry;
  int i;
  struct timespec btime, etime, delta;
  uint64_t buffer = 250;
  uint64_t buffer_low = buffer;
  uint64_t buffer_high = buffer;

  for (i = 0; i < buf_size; i++) {
    comp_buf[i].status          = 1;
    desc_buf[i].opcode          = DSA_OPCODE_MEMMOVE;
    desc_buf[i].flags           = IDXD_OP_FLAG_RCR | IDXD_OP_FLAG_CRAV;
    desc_buf[i].xfer_size       = xfer_size;
    desc_buf[i].src_addr        = (uintptr_t)data_buf[0][i];
    desc_buf[i].dst_addr        = (uintptr_t)data_buf[1][i];
    desc_buf[i].completion_addr = (uintptr_t)&(comp_buf[i]);
  }

  char byte;
  int bit_index;

  clock_gettime(CLOCK_MONOTONIC_RAW, &btime);

  /* Header: 10101010: 170 */
  int header = 170;
	for (int bit_idx = 7; bit_idx >= 0; --bit_idx)
	{
		int bit = header >> bit_idx & 1;
		if (bit == 1){
        start_tsc = rdtsc();
        target_tsc = start_tsc + interval_cycle;
        i = 0;
        while(1){
          rc = 0;
          _mm_sfence();
          while(rc != sizeof(struct dsa_hw_desc)){
            rc = write(wq_fd, &desc_buf[i], sizeof(struct dsa_hw_desc));
          }
          retry = 0;
          current_tsc = rdtsc();
          if (current_tsc + buffer_high > target_tsc)
            break;
          else if(i<buf_size-1)
            i++;
          else
            i = 0;
        }
      }
      else{
        start_tsc = rdtsc();
        target_tsc = start_tsc + interval_cycle;
        while(1){
          delay = __rdtsc() + UMWAIT_DELAY;
          umwait(UMWAIT_STATE_C0_1, delay);
          current_tsc = rdtsc();
          if (current_tsc + buffer_low > target_tsc)
            break;
        }
      }
	}

  for (int byte_idx = 0; byte_idx < payload_length_byte; ++byte_idx){
    byte = payload[byte_idx];
    for (bit_index = 7; bit_index >= 0; --bit_index){
      int bit = (byte >> bit_index) & 1;
      if (bit == 1){
        start_tsc = rdtsc();
        target_tsc = start_tsc + interval_cycle;
        i = 0;
        while(1){
          rc = 0;
          _mm_sfence();
          while(rc != sizeof(struct dsa_hw_desc)){
            rc = write(wq_fd, &desc_buf[i], sizeof(struct dsa_hw_desc));
          }
          retry = 0;
          current_tsc = rdtsc();
          if (current_tsc + buffer_high > target_tsc)
            break;
          else if(i<buf_size-1)
            i++;
          else
            i = 0;
        }
      }
      else{
        start_tsc = rdtsc();
        target_tsc = start_tsc + interval_cycle;
        while(1){
          delay = __rdtsc() + UMWAIT_DELAY;
          umwait(UMWAIT_STATE_C0_1, delay);
          current_tsc = rdtsc();
          if (current_tsc + buffer_low > target_tsc)
            break;
        }
      }
    }
  }
  clock_gettime(CLOCK_MONOTONIC_RAW, &etime);
  timespec_diff(&btime, &etime, &delta);
  printf("%lds %09ldns\n", delta.tv_sec, delta.tv_nsec);
}
