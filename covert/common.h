#ifndef _COMMON_H__
#define __COMMON_H__

#include <stdlib.h>
#include <fcntl.h>
#include <linux/idxd.h>
#include <accel-config/libaccel_config.h>
#include <x86intrin.h>
#include <string.h>

#ifndef __GNUC__
#define __asm__ asm
#endif

#define PATH_MAX 4096
#define BUF_SIZE   1024 * 2
#define NOP_RETRY 100000000

struct wq_info {
    bool wq_mapped;
    int wq_fd;
};

static bool is_write_syscall_success(int fd) {
    struct dsa_hw_desc desc = { 0 };
    struct dsa_completion_record comp __attribute__((aligned(32)));
    int retry = 0;
    int rc;
    desc.opcode = DSA_OPCODE_NOOP;
    desc.flags = IDXD_OP_FLAG_CRAV | IDXD_OP_FLAG_RCR;
    comp.status = 0;
    desc.completion_addr = (unsigned long) & comp;
    rc = write(fd, & desc, sizeof(desc));
    if (rc == sizeof(desc)) {
        while (comp.status == 0 && retry++ < NOP_RETRY) _mm_pause();
        if (comp.status == DSA_COMP_SUCCESS) return true;
    }
    return false;
}

void send(uint64_t *(data_buf[2][BUF_SIZE]), struct dsa_hw_desc *desc_buf,
                                              struct dsa_completion_record *comp_buf,
                                              int wq_fd, int xfer_size, int buf_size, char *payload, int payload_length_byte, int interval_cycle);
int receive(uint64_t *(data_buf[2][BUF_SIZE]), struct dsa_hw_desc *desc_buf,
                                              struct dsa_completion_record *comp_buf,
                                              int wq_fd, int xfer_size, int buf_size, int interval_cycle, int payload_length);

static __always_inline uint64_t
rdtsc(void) {
  uint64_t tsc;
  unsigned int dummy;
  tsc = __rdtscp(&dummy);
  __builtin_ia32_lfence();
  return tsc;
}

#define UMWAIT_STATE_C0_1 1
#define MAX_COMP_RETRY 2000000000
#define UMWAIT_DELAY 100000

static inline unsigned char
umwait(unsigned int state, unsigned long long timeout) {
  uint8_t r;
  uint32_t timeout_low = (uint32_t)timeout;
  uint32_t timeout_high = (uint32_t)(timeout >> 32);
  asm volatile(".byte 0xf2, 0x48, 0x0f, 0xae, 0xf1\t\n"
    "setc %0\t\n" :
    "=r"(r) :
    "c"(state), "a"(timeout_low), "d"(timeout_high));
  return r;
}

static inline void
umonitor(void *addr) {
  asm volatile(".byte 0xf3, 0x48, 0x0f, 0xae, 0xf0" : : "a"(addr));
}

static int map_wq(struct wq_info * wq_info, int dsa_num, int wq_num) {
  char path[PATH_MAX] = "/dev/dsa/";
  int fd;

  snprintf(path + strlen(path), PATH_MAX - strlen(path), "wq%d.%d", dsa_num, wq_num);
  fd = open(path, O_RDWR);
  if (fd < 0)
    return -1;

  if (is_write_syscall_success(fd)) {
      wq_info -> wq_mapped = false;
      wq_info -> wq_fd = fd;
      return 0;
  }
  
  close(fd);
  return 0;
}

static inline
void clflushopt(volatile void *__p) {
  asm volatile("clflushopt %0" : "+m" (*(volatile char  *)__p));
}

static inline void
cflush(char *buf, uint64_t len) {
  char *b = buf;
  char *e = buf + len;
  for (; b < e; b += 64)
    clflushopt(b);
}

#endif
