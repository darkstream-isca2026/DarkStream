CC=gcc
CFLAGS=-I.
LDFLAGS = -laccel-config
DEPS = common.h
SRCS_SOURCE = source.c send.c
SRCS_SINK = sink.c receive.c
OBJS_SOURCE = $(SRCS_SOURCE:.c=.o)
OBJS_SINK = $(SRCS_SINK:.c=.o)
EX_SOURCE = source
EX_SINK = sink

all: $(EX_SOURCE) $(EX_SINK)
	@rm -f *.o

.PHONY: clean

%.o: %.c $(DEPS)
	$(CC) -c -o $@ $< $(CFLAGS) $(LDFLAGS)

$(EX_SOURCE): $(OBJS_SOURCE)
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

$(EX_SINK): $(OBJS_SINK)
	$(CC) -o $@ $^ $(CFLAGS) $(LDFLAGS)

clean:
	rm -f $(EX_SOURCE) $(OBJS_SOURCE)
	rm -f $(EX_SINK) $(OBJS_SINK)
