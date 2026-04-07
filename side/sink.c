#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include <limits.h>
#include "common.h"
#include <linux/idxd.h>

int main(int argc, char *argv[]) {
  void *wq_portal;
  uint64_t start;
  struct dsa_hw_desc *desc_buf;
  struct dsa_completion_record *comp_buf;
  uint64_t *(data_buf[2][BUF_SIZE]);
  int status;
  struct wq_info wq_info;

  int found_xfer = 0, found_buf = 0, found_dsa = 0, found_wq = 0;
  int xfer_size = 0, buf_size = 0, dsa_num = 0, wq_num = 0;
  char path_name[PATH_MAX] = "";
  int probe_time_sec = 7;

  for (int i = 1; i < argc; i++) {
    if (strncmp(argv[i], "--xfer_size=", 12) == 0) {
      xfer_size = atoi(argv[i] + 12);
      found_xfer = 1;
    } else if (strncmp(argv[i], "--buf_size=", 11) == 0) {
      buf_size = atoi(argv[i] + 11);
      found_buf = 1;
    } else if (strncmp(argv[i], "--dsa=", 6) == 0) {
      dsa_num = atoi(argv[i] + 6);
      found_dsa = 1;
    } else if (strncmp(argv[i], "--wq=", 5) == 0) {
      wq_num = atoi(argv[i] + 5);
      found_wq = 1;
    } else if (strncmp(argv[i], "--probe_time_sec=", 17) == 0) {
      probe_time_sec = atoi(argv[i] + 17);
    } else if (strncmp(argv[i], "--path=", 7) == 0) {
      snprintf(path_name, sizeof(path_name), "%s", argv[i] + 7);
    } else {
      printf("Unknown option: %s\n", argv[i]);
    }
  }

  if (!(found_xfer && found_buf && found_dsa && found_wq)) {
    printf("Usage: ./sink --xfer_size=SIZE --buf_size=COUNT --dsa=DSA_NUM --wq=WQ_NUM\n");
    return 0;
  }

  desc_buf = (struct dsa_hw_desc*)aligned_alloc(64, buf_size * sizeof(struct dsa_hw_desc));
  comp_buf = (struct dsa_completion_record*)aligned_alloc(32, buf_size * sizeof(struct dsa_completion_record));
  for (int i = 0; i < 2; i++) {
    for (int j = 0; j < buf_size; j++)
      data_buf[i][j] = (uint64_t *)malloc(xfer_size);
  }

  start = rdtsc();

  int rc_wq = map_wq(&wq_info, dsa_num, wq_num);
  if (rc_wq == -1){
    printf("wq map failed\n");
    return 1;
  }

  for (int j = 0; j < buf_size; j++) {
    for (int i = 0; i < 2; i++){
      for (size_t k = 0; k < xfer_size / sizeof(uint64_t); k += 512)
        data_buf[i][j][k] = UINT64_MAX;
    }
    cflush((char*)data_buf[0][j], xfer_size);
    cflush((char*)data_buf[1][j], xfer_size);
  }
  
  status = receive(data_buf, desc_buf, comp_buf, wq_info.wq_fd, xfer_size, buf_size, probe_time_sec, path_name);

  if (status == -1){
    printf("file open/write error\n");
    return 1;
  }

  for (int i = 0; i < 1; i++)
    for (int j = 0; j < buf_size; j++)
      free(data_buf[i][j]);
  free(desc_buf);
  free(comp_buf);

  return 0;
}
