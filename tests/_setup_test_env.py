"""
Setups the environment for tests.
Import this module to have the side effect
that the project root dir will be added to ``sys.path``,
i.e. ``import preloaded`` works afterwards.
In the test code, you would have this::

    import _setup_test_env  # noqa

The ``# noqa`` is to ignore the warning that this module is not used.
See :func:`setup` below for details.
"""


def setup():
    """
    Calls necessary setups.
    """
    import logging
    import os
    import sys

    my_dir = os.path.dirname(os.path.realpath(os.path.abspath(__file__)))
    root_dir = os.path.dirname(my_dir)
    sys.path.insert(0, root_dir)

    # Enable all logging, up to debug level.
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')

    try:
        # noinspection PyUnresolvedReferences
        import better_exchook
        better_exchook.install()
        better_exchook.replace_traceback_format_tb()
    except ImportError:
        print("no better_exchook")

    import preloaded
    assert preloaded.__file__.startswith(root_dir)

    try:
        # noinspection PyUnresolvedReferences
        import faulthandler
        # Enable after libSigSegfault, so that we have both,
        # because faulthandler will also call the original sig handler.
        faulthandler.enable()
    except ImportError:
        print("no faulthandler")

    _try_hook_into_tests()


def _try_hook_into_tests():
    """
    Hook into nosetests or other unittest based frameworks.

    The hook will throw exceptions such that a debugger like PyCharm can inspect them easily.
    This will only be done if there is just a single test case.

    This code might be a bit experimental.
    It should work though. But if it does not, we can also skip this.
    Currently any exception here would be fatal though, as we expect this to work.

    Also see: https://youtrack.jetbrains.com/issue/PY-9848
    """
    import sys
    get_trace = getattr(sys, "gettrace", None)
    in_debugger = False
    if get_trace and get_trace() is not None:
        in_debugger = True

    # get TestProgram instance from stack...
    from unittest import TestProgram
    # noinspection PyProtectedMember,PyUnresolvedReferences
    top_frame = sys._getframe(1)
    if not top_frame:
        # This will not always work. Just silently accept this. This should be rare.
        return

    test_program = None
    frame = top_frame
    while frame:
        local_self = frame.f_locals.get("self")
        if isinstance(local_self, TestProgram):
            test_program = local_self
            break
        frame = frame.f_back

    test_names = None
    if test_program:  # nosetest, unittest
        test_names = getattr(test_program, "testNames")

    test_session = None
    try:
        # noinspection PyPackageRequirements,PyUnresolvedReferences
        import pytest
    except ImportError:
        pass
    else:
        frame = top_frame
        while frame:
            local_self = frame.f_locals.get("self")
            if isinstance(local_self, pytest.Session):
                test_session = local_self
                break
            frame = frame.f_back
        if test_session and not test_names:
            test_names = test_session.config.args

    if not test_names:
        # Unexpected, but just silently ignore.
        return
    if len(test_names) >= 2 or ":" not in test_names[0]:
        # Multiple tests are being run. Do not hook into this.
        # We only want to install the hook if there is only a single test case.
        return

    # Skip this if we are not in a debugger.
    if test_program and in_debugger:  # nosetest, unittest

        # Ok, try to install our plugin.
        class _ReraiseExceptionTestHookPlugin:
            @staticmethod
            def _reraise_exception(test, err):
                exc_class, exc, tb = err
                print("Test %s, exception %s %s, reraise now." % (test, exc_class.__name__, exc))
                raise exc

            handleFailure = _reraise_exception
            handleError = _reraise_exception

        config = getattr(test_program, "config")
        config.plugins.addPlugin(_ReraiseExceptionTestHookPlugin())


setup()
