#include <stdio.h>
#include <string.h>
#include <stdint.h>
#include "common.h"
#include <linux/idxd.h>

int main(int argc, char *argv[]) {
  struct dsa_hw_desc *desc_buf;
  struct dsa_completion_record *comp_buf;
  uint64_t *(data_buf[2][BUF_SIZE]);
  struct wq_info wq_info;

  int found_xfer = 0, found_buf = 0, found_dsa = 0, found_wq = 0;
  int xfer_size = 0, buf_size = 0, dsa_num = 0, wq_num = 0;
  int payload_length;
  int payload_length_byte;
  uint64_t interval_cycle = 1000000;
  const char* bitstream;

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
    } else if (strncmp(argv[i], "--interval_cycle=", 17) == 0) {
      interval_cycle = atoi(argv[i] + 17);
    } else if (strncmp(argv[i], "--bitstream=", 12) == 0) {
      bitstream = argv[i] + 12;
      payload_length = strlen(bitstream);
      payload_length_byte = payload_length/8;
    } else {
      printf("Unknown option: %s\n", argv[i]);
    }
  }

  if (!(found_xfer && found_buf && found_dsa && found_wq)) {
    printf("Usage: ./source --xfer_size=SIZE --buf_size=COUNT --dsa=DSA_NUM --wq=WQ_NUM\n");
    return 0;
  }

  desc_buf = (struct dsa_hw_desc*)aligned_alloc(64, buf_size * sizeof(struct dsa_hw_desc));
  comp_buf = (struct dsa_completion_record*)aligned_alloc(32, buf_size * sizeof(struct dsa_completion_record));
  for (int i = 0; i < 2; i++) {
    for (int j = 0; j < buf_size; j++)
      data_buf[i][j] = (uint64_t *)malloc(xfer_size);
  }

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

  char *payload = malloc(payload_length_byte);
  if (payload == NULL) {
      perror("malloc");
      return 1;
  }

  for (int i = 0; i < payload_length_byte; i++) {
      char byte_str[9] = {0};
      strncpy(byte_str, &bitstream[i * 8], 8);
      payload[i] = (unsigned char)strtol(byte_str, NULL, 2);
  }

  send(data_buf, desc_buf, comp_buf, wq_info.wq_fd, xfer_size, buf_size, payload, payload_length_byte, interval_cycle);

  for (int i = 0; i < 1; i++)
    for (int j = 0; j < buf_size; j++)
      free(data_buf[i][j]);
  free(desc_buf);
  free(comp_buf);
  free(payload);

  return 0;
}
