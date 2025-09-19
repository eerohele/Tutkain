import sublime

bar = None


# Initial implementation adapted from SublimeText/UnitTesting.
#
# Copyright (c) 2016 Randy Lai <randy.cs.lai@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


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
