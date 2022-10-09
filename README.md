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


## Method 2: Fork server

Start CPython and import the libraries.
The keep the process running as a fork server.
Whenever a new instance it needed, we make a fork (`os.fork`),
and apply a similar logic as [reptyr](https://github.com/nelhage/reptyr).

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
TF: 2.7.0

________________________________________________________
Executed in    1.47 secs    fish           external
   usr time    1.68 secs    0.07 millis    1.68 secs
   sys time    1.60 secs    1.20 millis    1.60 secs
```

The starter script was not run yet, so the first start is just as slow:
```
$ time ./python-tf.bin demo-import-tensorflow.py
Existing socket but can not connect: [Errno 61] Connection refused
Import module: tensorflow
TF: 2.7.0

________________________________________________________
Executed in    1.54 secs    fish           external
   usr time    1.81 secs    0.07 millis    1.81 secs
   sys time    1.56 secs    1.32 millis    1.56 secs
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
TF: 2.7.0

________________________________________________________
Executed in  246.09 millis    fish           external
   usr time   60.38 millis    0.08 millis   60.30 millis
   sys time   25.17 millis    1.66 millis   23.52 millis
```
As you see, the startup time is now very fast.
This demo is on a fast filesystem.
On a slow filesystem, the difference can be much larger.


## Method 2: Process pool

We always keep some pool (e.g. N=10 instances)
of CPython + preloaded libraries alive in the background,
and once we need a new instance, we just pick one from the pool.

(Currently not implemented)


## Method 3: Program checkpoint on disk

Use some checkpointing tool ([CRIU](https://criu.org/)) to store the state of CPython
right after we imported the libraries.
Then later we can load this checkpoint (very fast).

CRIU currently needs root access for dump/restore.
However, there is ongoing work to support a non-root option in https://github.com/checkpoint-restore/criu/pull/1930.

Or maybe [DMTCP](https://github.com/dmtcp/dmtcp/) is a better alternative to CRIU?

(Currently incomplete)


