import cProfile
import functools
import pstats


def profile(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            retval = func(*args, **kwargs)
        finally:
            profiler.disable()
            profiler.dump_stats('/tmp/tutkain.profile.out')
        return retval

    return inner
