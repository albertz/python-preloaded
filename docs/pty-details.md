I must admit, I don't know all the details of how the PTY works.
I tried to read through [reptyr](https://github.com/nelhage/reptyr)
and [its blog post](https://blog.nelhage.com/2011/02/changing-ctty/)
but there are many details I don't fully understand.
These things are however probably relevant for this project,
so here I will collect some summary.

Specifically, what I don't understand:

- What is a [pseudoterminal (PTY)](https://en.wikipedia.org/wiki/Pseudoterminal)?
  How does it work?
- What is a "controlling terminal", or the "current controlling terminal (CTTY)"?
- What are "sessions groups" and "process groups"?
- What is a "session leader" or "process group leader"?
- What do [setsid](https://linux.die.net/man/2/setsid), [setpgid](https://linux.die.net/man/2/setpgid), etc do?

Some resources:

- [Pseudoterminal (PTY) Wikipedia](https://en.wikipedia.org/wiki/Pseudoterminal)
- [reptyr repo](https://github.com/nelhage/reptyr)
- [reptyr: Changing a process's controlling terminal, Nelson Elhage, 2011](https://blog.nelhage.com/2011/02/changing-ctty/)
- [reptyr: Attach a running process to a new terminal, Nelson Elhage, 2011](https://blog.nelhage.com/2011/01/reptyr-attach-a-running-process-to-a-new-terminal/)
- [A Brief Introduction to termios: Signaling and Job Control, Nelson Elhage, 2010](https://blog.nelhage.com/2010/01/a-brief-introduction-to-termios-signaling-and-job-control/)
- [Moving a process to another terminal, Thomas Habets, 2009](https://blog.habets.se/2009/03/Moving-a-process-to-another-terminal.html)
- [Termios Linux man page](https://linux.die.net/man/3/termios)
- [The TTY demystified, Linus Åkesson, 2008](http://www.linusakesson.net/programming/tty/index.php)