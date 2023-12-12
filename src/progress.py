import sublime

bar = None


# I straight up stole this progress bar from SublimeText/UnitTesting.
class ProgressBar:
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def __init__(self, label):
        self.label = label

    def start(self):
        self.done = False
        self.update()

    def stop(self):
        sublime.status_message("")
        self.done = True

    def update(self, frame=0):
        if self.done:
            return

        sublime.status_message(f"{self.frames[frame % len(self.frames)]} {self.label}")
        sublime.set_timeout(lambda: self.update(frame + 1), 100)


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
