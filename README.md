# Python Preloaded

Problem:

The startup time of CPython including
loading big libraries like PyTorch or TensorFlow is too slow.
In case of slow file systems, I have seen startup times including such import
of 10-20 seconds.

Very simple idea:

Keep the state of CPython
right after we imported the big libraries
and make it available instantly when needed.
When loading the state,
we can continue to run any random Python script
(we can use [runpy](https://docs.python.org/3/library/runpy.html)).


## Method 1: Program checkpoint on disk

Use some checkpointing tool ([CRIU](https://criu.org/)) to store the state of CPython
right after we imported the libraries.
Then later we can load this checkpoint (very fast).

CRIU currently needs root access for dump/restore.
However, there is ongoing work to support a non-root option in https://github.com/checkpoint-restore/criu/pull/1930.

Or maybe [DMTCP](https://github.com/dmtcp/dmtcp/) is a better alternative to CRIU?


## Method 2: Fork server

Start CPython and import the libraries.
The keep the process running as a fork server.
Whenever a new instance it needed, we make a fork (`os.fork`),
reparent and [reptyr](https://github.com/nelhage/reptyr) it.


## Method 3: Process pool

We always keep some pool (e.g. N=10 instances)
of CPython + preloaded libraries alive in the background,
and once we need a new instance, we just pick one from the pool.
