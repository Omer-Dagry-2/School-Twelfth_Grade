import win32event
import win32process

from typing import *


class Thread:
    def __init__(self, target: Callable, args: Union[tuple, Any] = None, kwargs: Union[Mapping[str, Any], None] = None,
                 name: Union[str, None] = None, security_attributes=None, stack_size: int = 0):
        kwargs = {} if kwargs is None else kwargs
        args = () if args is None else args
        assert isinstance(kwargs, dict)
        assert isinstance(args, tuple)
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__name = name
        self.__security_attributes = security_attributes
        self.__stack_size = stack_size
        self.__flags = win32process.CREATE_SUSPENDED
        self.__thread, self.__thread_id = win32process.beginthreadex(
            self.__security_attributes, self.__stack_size, self.__run, (self.__args, self.__kwargs), self.__flags)
        self.__started = False
        self.__suspended = True

    def __run(self, *args):
        """ Call __target, this allows to pass key word arguments """
        kwargs = args[1]
        args = args[0]
        self.__target(*args, **kwargs)

    def start(self):
        """ Start The Process Main Thread"""
        if self.__started:
            raise RuntimeError("threads can only be started once")
        suspend_count = self.resume()
        self.__started = True
        return suspend_count

    def resume(self):
        """ Resume Thread """
        if self.__suspended:
            self.__suspended = False
            return win32process.ResumeThread(self.__thread)
        raise RuntimeError("Can't resume a thread that isn't suspend.")

    def suspend(self):
        """ Suspend Thread """
        if not self.__suspended:
            self.__suspended = True
            return win32process.SuspendThread(self.__thread)
        raise RuntimeError("Can't suspend a thread that isn't running.")

    def join(self, timeout=win32event.INFINITE) -> int:
        """
            Join This Thread
            (waits until the thread exits by itself or until timing out)
            :param timeout: time-out interval in milliseconds
        """
        if self.__thread is not None and self.__started:
            return win32event.WaitForSingleObject(self.__thread, timeout)
        raise RuntimeError("Can't join a thread that hasn't started yet.'")

    def is_alive(self):
        """ Check If The Process Is Still Alive """
        if self.__thread is not None and self.__started:
            return win32process.GetExitCodeThread(self.__thread) == 259
        raise RuntimeError("Can't check if thread is alive, the thread hasn't started yet.'")

    def get_exit_code(self):
        """ Get The Process Exit Code """
        if self.__thread is not None and self.__started:
            return win32process.GetExitCodeThread(self.__thread)
        raise Exception("Can't check the thread's exit code, the thread hasn't started yet.'")

    def get_name(self):
        """ returns: the thread name"""
        return self.__name
