import cProfile
import functools


def profile(func):
    @functools.wraps(func)
    def inner(*args, **kwargs):
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            retval = func(*args, **kwargs)
        finally:
            profiler.disable()
            profiler.dump_stats("/tmp/tutkain.prof")
        return retval

    return inner
