from datetime import datetime, timedelta
from functools import wraps
import inspect, traceback, collections

def _safely(*funcs):
    ret = None
    for func in funcs:
        try:
            ret = func()
        except Exception as e:
            traceback.print_exc()
    return ret

def coroutine(func):
    def start(*args,**kwargs):
        cr = func(*args,**kwargs)
        next(cr)
        return cr
    return start


################################################################################################################################################################

class State(object):

    instances = []

    def __init__(self, timeout=None, lockout=None, lockout_oneway=True, hi_trig=None, lo_trig=None):
        """
        timeout: time in seconds after last activation, that state is deactivated
        lockout: time in seconds after last activation, during which state cannot be activated (or deactivated if lockout_oneway=False)
        lockout_oneway: if True, only lockout from activating again after activation; otherwise lockout from activating or deactivating (after activation)
        """
        self.timeout = timeout
        self.lockout = lockout
        self.lockout_oneway = lockout_oneway
        self.hi_trig = hi_trig    # only called when state is set/checked/polled!
        self.lo_trig = lo_trig    # only called when state is set/checked/polled!
        self._state = False
        self.timeout_time = None
        self.lockout_time = None
        State.instances.append(self)

    @property
    def state(self):
        if self.timeout_time and datetime.today() >= self.timeout_time:
            self.state = False
            self.timeout_time = None
        return self._state

    @state.setter
    def state(self, value):
        # State.state.fset(s, value)
        # State.state.__set__(s, value)
        if self.lockout_time and (not self.lockout_oneway or value):
            if datetime.today() < self.lockout_time:
                return
            else:
                self.lockout_time = None
        if bool(self._state) != bool(value):
            if value:
                if self.hi_trig: _safely(lambda: self.hi_trig())
            else:
                if self.lo_trig: _safely(lambda: self.lo_trig())
        self._state = value
        if value:
            if self.timeout:
                self.timeout_time = datetime.today() + timedelta(seconds=self.timeout)
            if self.lockout:
                self.lockout_time = datetime.today() + timedelta(seconds=self.lockout)
        else:
            self.timeout_time = None

    def __bool__(self):
        return bool(self.state)
        # value = self.state
        # return bool(value != False and value != None)
    __nonzero__ = __bool__  # PY2 compatibility

    def set(self, value=True):
        initial_value = self.state
        self.state = value
        return (initial_value != self.state)
    def activate(self, force=False):
        return self.set(True)
    def deactivate(self, force=False):
        return self.set(False)


################################################################################################################################################################

class MultiMode:

    instances = []
    current = None
    transition_func = None

    def __init__(self, levels={}, color='#555', pump=None, release=None, timeout=None,
            process=None, postprocess=None, rule=None, reset=None, thread_coro_init=None, sticky=None, exclusive=None, singleton=False):
        self.levels = levels
        self.color = color
        self.pump_func = pump
        self.release_func = release
        self.timeout = timeout
        self.process_func = process
        self.postprocess_func = postprocess
        self.rule = rule
        self.reset = reset
        self.thread_coro_init = thread_coro_init
        self.sticky = sticky
        self.exclusive = exclusive    # FIXME: not implemented

        self.level = 0
        self.active_time = None
        self.timeout_time = None
        self.thread_coro = None
        frame,filename,line_number,function_name,lines,index = inspect.getouterframes(inspect.currentframe())[2 if singleton else 1]
        self._str = "<mode.MultiMode instance from %s:%d>" % (filename, line_number)
        MultiMode.instances.append(self)

    def __str__(self):
        return self._str
    def __bool__(self):
        return bool(self.level)
    __nonzero__ = __bool__  # PY2 compatibility
    def __call__(self):
        return self.pump()

    def _active_level(self):
        active_levels = [level for level in self.levels.keys() if level <= self.level]
        return None if not active_levels else max(active_levels)

    def _active_fire_func(self):
        if self._active_level(): return self.levels[self._active_level()]
        return lambda: None

    def pump(self):
        self.heartbeat()
        if self.exclusive:
            self.release_all()
        MultiMode.current = self
        self.level += 1
        self.active_time = datetime.today()
        if self.timeout and (1 or self.level == 1):
            self.timeout_time = datetime.today() + timedelta(seconds=self.timeout)
        if self.thread_coro_init and not self.thread_coro:
            self.thread_coro = _safely(lambda: self.thread_coro_init())
        if self.process_func:
            _safely(lambda: self.process_func(self.level))
        if self.pump_func:
            _safely(lambda: self.pump_func())
        if self.rule:
            _safely(lambda: self.rule.enable())
        if self.levels and self._active_level():
            _safely(lambda: self._active_fire_func()())
            if self.reset:
                _safely(lambda: self.release())
        if self.postprocess_func:
            _safely(lambda: self.postprocess_func(self.level))
        if self.transition_func:
            _safely(lambda: self.transition_func.__func__())
        if self.timeout and (1 or self.level == 1):
            self.timeout_time = datetime.today() + timedelta(seconds=self.timeout)
        return self

    def refresh(self):
        if self.timeout and self.level >= 1:
            self.timeout_time = datetime.today() + timedelta(seconds=self.timeout)

    def release(self):
        if self.level:
            self.level = 0
            self.timeout_time = None
            if self.release_func:
                _safely(lambda: self.release_func())
            if self.thread_coro:
                _safely(lambda: self.thread_coro.close())
                self.thread_coro = None
            if self.rule:
                _safely(lambda: self.rule.disable())
            active_instances = sorted([_f for _f in self.instances if _f], key=lambda m: m.active_time)
            MultiMode.current = active_instances[-1] if active_instances else None
            if self.transition_func:
                _safely(lambda: self.transition_func.__func__())

    @classmethod
    def release_all(cls, sticky=None):
        old_mode = cls.current
        for mode in cls.instances:
            if sticky or not mode.sticky:
                _safely(lambda: mode.release())
        return old_mode

    @classmethod
    def heartbeat(cls):
        now = datetime.today()
        for mode in cls.instances:
            if mode.timeout_time and now >= mode.timeout_time:
                _safely(lambda: mode.release())
        _safely(lambda: Deferred.heartbeat())
        for mode in cls.instances:
            if mode.thread_coro and mode.level:
                try:
                    next(mode.thread_coro)
                except StopIteration as e:
                    _safely(lambda: mode.release())
                except Exception as e:
                    traceback.print_exc()
                    _safely(lambda: mode.release())

    activate = pump
    deactivate = release
    deactivate_all = release_all

    singletons = dict()

    @classmethod
    def singleton_pump(cls, *args, **kwargs):
        frame,filename,line_number,function_name,lines,index = inspect.getouterframes(inspect.currentframe())[1]
        key = (filename, line_number)
        if key not in cls.singletons:
            kwargs = dict(kwargs, singleton=True)
            cls.singletons[key] = cls(*args, **kwargs)
        return cls.singletons[key].pump()


################################################################################################################################################################

class Deferred(object):

    instances = []

    def __init__(self, delay, func):
        self.func = func
        self.delay = delay
        self.target_time = datetime.today() + timedelta(seconds=self.delay)
        Deferred.instances.append(self)

    def execute(self):
        _safely(lambda: self.func())
        Deferred.instances.remove(self)

    def cancel(self):
        Deferred.instances.remove(self)

    @classmethod
    def heartbeat(cls):
        now = datetime.today()
        for deferred in cls.instances:
            if deferred.target_time and now >= deferred.target_time:
                _safely(lambda: deferred.execute())


################################################################################################################################################################

class throttle(object):
    """
    Decorator that prevents a function from being called more than once every
    time period.

    To create a function that cannot be called more than once a minute:

        @throttle(minutes=1)
        def my_fun():
            pass
    """

    def __init__(self, seconds=0, minutes=0, hours=0):
        self.throttle_period = timedelta(
            seconds=seconds, minutes=minutes, hours=hours
        )
        self.time_of_last_call = datetime.min

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            time_since_last_call = now - self.time_of_last_call

            if time_since_last_call > self.throttle_period:
                self.time_of_last_call = now
                return fn(*args, **kwargs)

        return wrapper

class ramp(object):
    """
    Decorator that executes a function if it's called at least count times every time period.
    """

    def __init__(self, count=2, seconds=0, minutes=0, hours=0):
        self.times = collections.deque(maxlen=count)
        self.ramp_period = timedelta(seconds=seconds, minutes=minutes, hours=hours)

    def __call__(self, fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            now = datetime.now()
            self.times.append(now)
            while self.times and self.times[0] < (now - self.ramp_period):
                self.times.popleft()
            if len(self.times) == self.times.maxlen:
                return fn(*args, **kwargs)

        return wrapper

"""
@mode.throttle(minutes=1)
def ringer():
    print "ringer(): won't be executed more than 1 every 1 minute"
@mode.ramp(3, minutes=1)
def ringer():
    print "ringer(): must be called at least 3 times within 1 minute"
@mode.ramp(3, minutes=5)
@mode.throttle(minutes=1)
def ringer():
    print "ringer(): must be called at least 3 times within 1 minute, but won't be executed more than 1 every 1 minute"
"""
