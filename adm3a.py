# MIT License
#
# Copyright (c) 2023 Madis Kaal
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
import sys
import serial
from collections import deque
import threading
import os
import tkinter as tk


class Terminal:
    def __init__(self):
        self.height = 24
        self.width = 80
        self.visible = list((-1,) * (self.width * self.height))
        self.clear()
        self.home()

    def clear(self):
        self.chars = list((32,) * self.height * self.width)

    def clearline(self):
        for x in range(self.width):
            self.chars[self.cury * self.width + x] = 32

    def scroll_up(self):
        self.chars = self.chars[self.width :]
        self.chars.extend(list((32,) * self.width))

    def home(self):
        self.goto(0, 0)

    def goto(self, curx, cury):
        self.curx = max(0, min(curx, self.width - 1))
        self.cury = max(0, min(cury, self.height - 1))

    def cursor_up(self):
        if self.cury > 0:
            self.cury -= 1

    def cursor_down(self):
        self.cury += 1
        if self.cury >= self.height:
            self.cury = self.height - 1
            self.scroll_up()

    def cursor_left(self):
        if self.curx > 0:
            self.curx -= 1

    def cursor_right(self):
        self.curx += 1
        if self.curx >= self.width:
            if self.cury < self.height - 1:
                self.curx = 0
                self.cursor_down()
            else:
                self.curx = self.width - 1

    def putc(self, character):
        if character >= 32 and character != 127:
            self.chars[self.cury * self.width + self.curx] = character
            self.cursor_right()

    def cursor_start_of_line(self):
        self.curx = 0

    def update(self, rendercb):
        for y in range(self.height):
            for x in range(self.width):
                ofs = y * self.width + x
                if self.visible[ofs] != self.chars[ofs]:
                    rendercb(x, y, self.chars[ofs])
                    self.visible[ofs] = self.chars[ofs]


class Adm3a(Terminal):
    def __init__(self):
        super().__init__()
        self.state = 0
        self.cy = 0
        self.answer_back = False

    def output(self, character):
        if self.state == 0:
            if character == 5:  # ctrl-E (ENQ)
                self.answer_back = True
            elif character == 8:  # BS
                self.cursor_left()
            elif character == 10:  # LF
                self.cursor_down()
            elif character == 11:  # VT
                self.cursor_up()
            elif character == 12:  # FF
                self.cursor_right()
            elif character == 13:  # CR
                self.cursor_start_of_line()
            elif character == 26:  # ctrl-Z (SUB)
                self.clear()
            elif character == 27:  # ESC
                self.state = 1
            elif character == 30:
                self.home()
            elif character >= 32:
                self.putc(character)
        elif self.state == 1:
            if character == ord(b"="):
                self.state = 2
            else:
                self.state = 0
        elif self.state == 2:
            self.cy = character - 32
            self.state = 3
        elif self.state == 3:
            self.goto(character - 32, self.cy)
            self.state = 0


class Emulator(tk.Tk):
    def __init__(self, serialport, baud=57600):
        super().__init__()
        self.configure(bg="black")
        self.resizable(False, False)
        self.title(f"ADM-3A on {serialport}@{baud}")
        self.terminal = Adm3a()
        self.cheight = 24
        self.cwidth = 13
        self.cursor_on = False
        self.canvas = tk.Canvas(
            self,
            width=self.terminal.width * self.cwidth,
            height=self.terminal.height * self.cheight,
            borderwidth=0,
            background="black",
            highlightthickness=0,
            relief="flat",
        )
        self.canvas.pack(padx=20, pady=20)
        self.loadfont()
        self.bitmaps = list((None,) * (self.terminal.width * self.terminal.height))
        self.terminal.update(self.render)
        self.rqueue = deque()
        self.port = serial.Serial(serialport, baud, timeout=0.1)
        self.rthread = threading.Thread(target=self._receiver, daemon=True)
        if self.rthread:
            self.rthread.start()
        self.bind("<Key>", self.keypress)
        self.after(20, self.work)
        self.after(500, self.blink_cursor)

    def _receiver(self):
        while True:
            s = self.port.read(self.port.in_waiting)
            for c in s:
                self.rqueue.append(c)
            if s:
                self.after(0, self.work)

    def keypress(self, event):
        if event.char:
            self.port.write(event.char.encode("utf8"))

    def work(self):
        if len(self.rqueue):
            if self.cursor_on:
                self.hide_cursor()
            while len(self.rqueue):
                self.terminal.output(self.rqueue.popleft())
            self.terminal.update(self.render)
            if self.cursor_on:
                self.show_cursor()

    def show_cursor(self):
        self.render(
            self.terminal.curx,
            self.terminal.cury,
            self.terminal.chars[
                self.terminal.cury * self.terminal.width + self.terminal.curx
            ]
            | 0x80,
        )

    def hide_cursor(self):
        self.render(
            self.terminal.curx,
            self.terminal.cury,
            self.terminal.chars[
                self.terminal.cury * self.terminal.width + self.terminal.curx
            ],
        )

    def blink_cursor(self):
        self.after(500, self.blink_cursor)
        if self.cursor_on:
            self.cursor_on = False
            self.hide_cursor()
        else:
            self.cursor_on = True
            self.show_cursor()

    def loadfont(self):
        def flip(b):
            r = 0
            for i in range(8):
                r = (r << 1) | (b & 1)
                b = b >> 1
            return r

        fontfile = "adm3a.fnt"
        self.font = []
        rbytes = 2
        cbytes = rbytes * self.cheight
        with open(fontfile, "rb") as f:
            d = bytearray(f.read())
            for c in range(256):
                s = (
                    "#define im_width %d\n#define im_height %d\nstatic char im_bits[] = {\n"
                    % (self.cwidth, self.cheight)
                )
                for i in range(0, cbytes, rbytes):
                    for b in range(rbytes):
                        bm = d[c * cbytes + i + b]
                        s += "0x%02x," % (flip(bm))
                s = s[:-1]
                s += "\n};\n"
                self.font.append(
                    tk.BitmapImage(data=s, foreground="#ffbf00", background="black")
                )

    def render(self, col, row, char):
        if col >= self.terminal.width or row >= self.terminal.height:
            return
        i = int(row * self.terminal.width + col)
        if self.bitmaps[i] != None:
            self.canvas.delete(self.bitmaps[i])
        self.bitmaps[i] = self.canvas.create_image(
            col * self.cwidth,
            row * self.cheight,
            image=self.font[char & 255],
            anchor=tk.NW,
        )


if len(sys.argv) > 1:
    emulator = Emulator(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 57600)
    emulator.mainloop()
else:
    print("Usage: python3 adm3a.py <serialdevice> [baudrate]")
