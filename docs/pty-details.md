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
- Can you change the parent process?
- What does `disown` do? `nohup`? When do you get `SIGHUP`?
- What is `PR_SET_CHILD_SUBREAPER`? What is a "child subreaper" of a process?

Some resources:

- [Pseudoterminal (PTY) Wikipedia](https://en.wikipedia.org/wiki/Pseudoterminal)
- [reptyr repo](https://github.com/nelhage/reptyr)
- [reptyr: Changing a process's controlling terminal, Nelson Elhage, 2011](https://blog.nelhage.com/2011/02/changing-ctty/)
- [reptyr: Attach a running process to a new terminal, Nelson Elhage, 2011](https://blog.nelhage.com/2011/01/reptyr-attach-a-running-process-to-a-new-terminal/)
- [A Brief Introduction to termios: Signaling and Job Control, Nelson Elhage, 2010](https://blog.nelhage.com/2010/01/a-brief-introduction-to-termios-signaling-and-job-control/)
- [A Brief Introduction to termios, Nelson Elhage, 2009](https://blog.nelhage.com/2009/12/a-brief-introduction-to-termios/)
- [Moving a process to another terminal, Thomas Habets, 2009](https://blog.habets.se/2009/03/Moving-a-process-to-another-terminal.html)
- [injcode repo](https://github.com/ThomasHabets/injcode)
- [Termios Linux man page](https://linux.die.net/man/3/termios)
- [The TTY demystified, Linus Åkesson, 2008](http://www.linusakesson.net/programming/tty/index.php)
- [Is reparenting from the shell possible? 2014](https://unix.stackexchange.com/questions/152379/is-reparenting-from-the-shell-possible/)

Some comments, summary:

PTY has two endpoints:
- Master/server. This is the terminal emulator (e.g. xterm).
- Slave/client. E.g. a shell (e.g. bash).

Termios sits between the master/slave PTY endpoints.
Termios is implemented in the kernel. 
Termios controls all the logic of the PTY.

SIGHUP: controlling terminal closed.

Parent of a process is actually not really relevant?
When the parent dies (e.g. the shell),
the child process is reparented automatically (e.g. to `init`)
and continues to run (unless it now crashes due to SIGHUP or pipe destroyed).
So we maybe don't need to care about proper reparenting,
and simply need to care about proper PTY and stdin/stdout/stderr setup.

Session and process groups are good explained [here](https://blog.nelhage.com/2010/01/a-brief-introduction-to-termios-signaling-and-job-control/).
A session may have a controlling terminal. 
All processes within a single instance of the terminal emulator,
are within the same session, with the pty allocated by the terminal emulator.
Process groups are for signal generation by a terminal.
Process groups are a sub-division within sessions.

We probably want to copy the logic of reptyr or injcode,
but we don't need any of the ptrace logic,
as we have full control over the code anyway.
Specifically:

- in target proc:
  - `fork`, exit parent. now in child:
  - detach from current CTTY: `ioctl(fd, TIOCNOTTY)`
  - wait for startup proc. for each instance:
  - `fork`, now for the child:
  - new proc in the target session (pid: `new_pgid`), just `fork` or `subprocess`
    - make it a process group leader: `setpgid(0,0)`
  - change process group leader: `setpgid(0,new_pgid)` (needed for `sedsid`)
  - can kill/cleanup child proc `new_pgid` now
  - become session leader: `setsid`
  - set new PTY as CTTY: `ioctl(fd, TIOCSCTTY)`
- in startup proc:
  - create new PTY
  - use PTY proxy
