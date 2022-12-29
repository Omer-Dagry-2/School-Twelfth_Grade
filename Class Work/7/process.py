import os
import sys
import time
import types
import pickle
import marshal
import win32api
import win32event
import win32process

from typing import *
from base64 import b64encode, b64decode


class Process:
    def __init__(self, target: Callable, args: Union[tuple, Any] = None, kwargs: Union[dict[str, Any], None] = None,
                 name: Union[str, None] = None, process_security_attributes=None, thread_security_attributes=None,
                 inherit_handles: int = 0, flags: Union[int, None] = None, environment: Union[Dict, None] = None,
                 current_directory: Union[str, None] = None):
        """
        Create A New Process
        :param target: The target function to call.
        :param args: The arguments to pass to the target function.
        :param kwargs: The keyword arguments to pass to the target function.
        :param name: The name of the process.
        """
        kwargs = {} if kwargs is None else kwargs
        args = () if args is None else args
        assert isinstance(kwargs, dict)
        assert isinstance(args, tuple)
        self.__target = target
        self.__args = args
        self.__kwargs = kwargs
        self.__name = name
        script_name = ".".join(__file__.split('\\')[-1].split('.')[:-1])
        #
        # if the target function is a builtin function it has no attribute '__code__' because the
        # implementation is in c, but it can be pickled, so builtin function are getting pickled
        # and other functions that are not builtin have '__code__' attribute and the code needs to be "marshalled"
        if isinstance(self.__target, types.BuiltinFunctionType):
            func = b64encode(pickle.dumps(self.__target)).decode()
            func_serialized_by = "pickle"
        else:
            try:
                func = b64encode(marshal.dumps(self.__target.__code__)).decode()
            except:
                raise RuntimeError("The target function can't be serialized.")
            func_serialized_by = "marshal"
        # pickle the args and kwargs
        pickled_data = (self.__args, self.__kwargs) if self.__args != () or self.__kwargs != {} else None
        pickled_data = b64encode(pickle.dumps(pickled_data)).decode()
        # create the command that the main thread of the process will run
        self.__command_line = f'"{sys.executable}" -c "import {script_name}; {script_name}.Process.run('
        self.__command_line += f"'{pickled_data}', '{func}', '{func_serialized_by}')" + '"'
        # parameters to start process using Windows api
        self.__process_security_attributes = process_security_attributes
        self.__thread_security_attributes = thread_security_attributes
        self.__inherit_handles = inherit_handles
        flags = win32process.CREATE_SUSPENDED if flags is None else flags | win32process.CREATE_SUSPENDED
        self.__flags = flags
        self.__environment = environment
        self.__current_directory = os.path.dirname(__file__) if current_directory is None else current_directory
        self.__startup_info = win32process.STARTUPINFO()
        self.__startup_info.hStdInput = win32api.GetStdHandle(win32api.STD_INPUT_HANDLE)
        self.__startup_info.hStdOutput = win32api.GetStdHandle(win32api.STD_OUTPUT_HANDLE)
        self.__startup_info.hStdError = win32api.GetStdHandle(win32api.STD_ERROR_HANDLE)
        # class parameters
        self.__started = False
        self.__suspended = True
        self.__killed = False
        # create the process
        self.__process, self.__main_thread, self.__process_id, self.__main_thread_id = win32process.CreateProcess(
            self.__name, self.__command_line, self.__process_security_attributes, self.__thread_security_attributes,
            self.__inherit_handles, self.__flags, self.__environment, self.__current_directory, self.__startup_info
        )

    @staticmethod
    def run(pickled_data: str, func: str, func_serialized_by: str):
        """ This func unpickles the args & kwargs and then calls the target func """
        # if the function was serialized by pickle - un-pickle the function
        # if it was serialized by marshal - un-marshal the function and reconstruct it
        if func_serialized_by == "marshal":
            code = marshal.loads(b64decode(func.encode()))
            func = types.FunctionType(code, {})
        elif func_serialized_by == "pickle":
            func = pickle.loads(b64decode(func.encode()))
        else:
            raise ValueError(f"Unknown value for 'func_serialized_by': '{func_serialized_by}'")
        pickled_data = pickle.loads(b64decode(pickled_data.encode()))
        if pickled_data is not None:
            args = pickled_data[0]
            kwargs = pickled_data[1]
            func(*args, **kwargs)
        else:
            func()

    def start(self):
        """ Start The Process Main Thread"""
        if self.__started:
            raise RuntimeError("process can only be started once")
        suspend_count = self.resume_main_thread()
        self.__started = True
        return suspend_count

    def resume_main_thread(self):
        """ Resume Main Thread """
        if self.__suspended:
            self.__suspended = False
            return win32process.ResumeThread(self.__main_thread)
        raise RuntimeError("Can't resume a thread that isn't suspend.")

    def suspend_main_thread(self):
        """ Suspend Main Thread """
        if not self.__suspended:
            self.__suspended = True
            return win32process.SuspendThread(self.__main_thread)
        raise RuntimeError("Can't suspend a thread that isn't running.")

    def join(self, timeout=win32event.INFINITE) -> int:
        """
            Join This Process And All It's Threads
            (waits until the process exits by itself or until timing out)
            :param timeout: time-out interval in milliseconds
        """
        if self.__main_thread is not None and self.__started:
            return win32event.WaitForSingleObject(self.__process, timeout)
        raise RuntimeError("Can't join a process that hasn't started yet.'")

    def terminate(self):
        """ Terminates The Process ( same as .kill() )"""
        if self.__started and self.__process is not None:
            if self.is_alive():
                self.__killed = True
                win32process.TerminateProcess(self.__process, -1)
            return
        raise RuntimeError("Can't terminate a process that hasn't started yet.")

    def kill(self):
        """ Kills The Process ( same as .terminate() )"""
        if self.__started and self.__process is not None:
            if self.is_alive():
                self.__killed = True
                win32process.TerminateProcess(self.__process, -1)
            return
        raise RuntimeError("Can't kill a process that hasn't started yet.")

    @staticmethod
    def exit_process(exit_code: int):
        """
            Closes The Current Process,
            Not Necessarily The Process Of A Specific Instance Of This Class.
            This Will Close The Process That The Call To This Function Was Made From.
        """
        win32process.ExitProcess(exit_code)

    def is_alive(self):
        """ Check If The Process Is Still Alive """
        if self.__process is not None and self.__started:
            return win32process.GetExitCodeProcess(self.__process) == 259
        raise RuntimeError("Can't check if process is alive, the process hasn't started yet.'")

    def get_exit_code(self):
        """ Get The Process Exit Code """
        if self.__process is not None and self.__started:
            if self.__killed:
                return None  # if the process was killed/terminated there is no exit code
            if self.is_alive():
                return None  # if process is still running there is no exit code yet
            return win32process.GetExitCodeProcess(self.__process)
        raise Exception("Can't check the process's exit code, the process hasn't started yet.'")

    def get_process_id(self):
        """ returns: the process id """
        return self.__process_id

    def get_main_thread_id(self):
        """ returns: the main thread id """
        return self.__main_thread_id

    def get_name(self):
        """ returns: the process name """
        return self.__name

    def __del__(self):
        # free the resources
        try:
            win32process.TerminateProcess(self.__process, -1)
            win32api.CloseHandle(self.__process)
        except:
            pass
        del self

    def __enter__(self):  # allows: "with Process(...) as p:"
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):  # allows: "with Process(...) as p:"
        if self.__started:
            # wait for process to finish, only then exit
            while self.is_alive():
                time.sleep(0.1)
        self.__del__()
