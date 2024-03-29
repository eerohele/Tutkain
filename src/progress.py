import sublime

bar = None


# I straight up stole this progress bar from SublimeText/UnitTesting.
class ProgressBar:
    def __init__(self, label, width=10):
        self.label = label
        self.width = width

    def start(self):
        self.done = False
        self.update()

    def stop(self):
        sublime.status_message("")
        self.done = True

    def update(self, status=0):
        if self.done:
            return
        status = status % (2 * self.width)
        before = min(status, (2 * self.width) - status)
        after = self.width - before
        sublime.status_message("%s [%s=%s]" % (self.label, " " * before, " " * after))
        sublime.set_timeout(lambda: self.update(status + 1), 100)


def start(message):
    global bar

    if bar:
        bar.stop()

    bar = ProgressBar(message)
    bar.start()


def stop():
    global bar
    if bar:
        bar.stop()
