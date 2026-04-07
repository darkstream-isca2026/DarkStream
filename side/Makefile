CC=gcc
CFLAGS=-I.
LDFLAGS = -laccel-config
DEPS = common.h
SRCS_SINK = sink.c receive.c
OBJS_SINK = $(SRCS_SINK:.c=.o)
EX_SINK = sink

all: $(EX_SINK)
	@rm -f *.o

.PHONY: clean

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS) $(LDFLAGS)

$(EX_SINK): $(OBJS_SINK)
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

clean:
	rm -f $(EX_SINK) $(OBJS_SINK)
