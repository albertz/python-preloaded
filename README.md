# Python Preloaded

Very simple idea:
Use some checkpointing tool ([CRIU](https://criu.org/)) to store the state of CPython
right after we imported some slow-to-import module like TensorFlow or PyTorch.
(In case of slow file systems, I have seen startup times including such import
of 10-20 seconds.)
Then later we can load this checkpoint (very fast) and run any random Python script
(we can use [runpy](https://docs.python.org/3/library/runpy.html)).

CRIU currently needs root access for dump/restore.
However, there is ongoing work to support a non-root option in https://github.com/checkpoint-restore/criu/pull/1930.

Or maybe [DMTCP](https://github.com/dmtcp/dmtcp/) is a better alternative to CRIU?
