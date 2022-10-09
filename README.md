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


## Method 1: Fork server

Start CPython and import the libraries.
Then keep the process running as a fork server.
Whenever a new instance it needed, we make a fork (`os.fork`),
and apply a similar logic as [reptyr](https://github.com/nelhage/reptyr).
Some technical details are [here](docs/pty-details.md).

This solution is very portable across Unix.
I tested it so far on Linux and MacOSX,
but it should run on most other Unixes as well.

### Example

Create the starter script `python-tf.bin`:
```
$ ./py-preloaded-bundle-fork-server.py tensorflow -o python-tf.bin
```
This starter script is supposed to be a dropin replacement to `python` itself.

For testing, there is `demo-import-tensorflow.py`, with only the following content:
```python
import tensorflow as tf
print("TF:", tf.__version__)
```

Now try to run it directly, and measure the time: 
```
$ time python3 demo-import-tensorflow.py
TF: 2.3.0

________________________________________________________
Executed in    8.31 secs    fish           external
   usr time    3.39 secs  278.00 micros    3.39 secs
   sys time    0.67 secs   83.00 micros    0.67 secs
```
This is on a slow filesystem, NFS specifically.
This is already after the files are cached (I just ran the same command immediately before).
Otherwise, the startup time is even over 14 seconds.

The starter script was not run yet, so the first start is just as slow:
```
$ time ./python-tf.bin demo-import-tensorflow.py
Existing socket but can not connect: [Errno 111] Connection refused
Import module: tensorflow
TF: 2.3.0

________________________________________________________
Executed in    8.35 secs    fish           external
   usr time    3.19 secs  768.00 micros    3.19 secs
   sys time    0.72 secs  228.00 micros    0.72 secs
```

Now it is running in the background.
It is in no way fixed to `demo-import-tensorflow.py`
but could also run any other script now.
However, we continue the demo with the same script:
```
$ time ./python-tf.bin demo-import-tensorflow.py
Existing socket, connected
Open new PTY
Send PTY fd to server
Wait for server to be ready
Entering PTY proxy loop
TF: 2.3.0

________________________________________________________
Executed in  261.56 millis    fish           external
   usr time   64.24 millis  542.00 micros   63.70 millis
   sys time   33.59 millis  163.00 micros   33.43 millis
```
As you see, the startup time is now very fast.
This is also just as fast when executed at a later time,
when the files are not cached anymore.

Interactively test the starter script environment:
```
$ ./python-tf.bin -m IPython
```


## Method 2: Process pool

We always keep some pool (e.g. N=10 instances)
of CPython + preloaded libraries alive in the background,
and once we need a new instance, we just pick one from the pool.

This shares a lot of logic with the fork server.
The main difference basically is that we use `subprocess.Popen` instead of `os.fork`.

(Currently not implemented)


## Method 3: Program checkpoint on disk

Use some checkpointing tool ([CRIU](https://criu.org/)) to store the state of CPython
right after we imported the libraries.
Then later we can load this checkpoint (very fast).

CRIU currently needs root access for dump/restore.
However, there is ongoing work to support a non-root option in https://github.com/checkpoint-restore/criu/pull/1930.

Or maybe [DMTCP](https://github.com/dmtcp/dmtcp/) is a better alternative to CRIU?

(Currently incomplete)


