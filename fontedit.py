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
import curses
import traceback
import sys
import os

screen = None
font = []
cell = []
cx = 0
cy = 0
clip = None
filename = None
widefont = False
width = 8
height = 16

for i in range(0, height):
    cell.append(0)
for i in range(0, 256):
    font.append(list(cell))
currentchar = ord("A")
markchar = None


def setfontheight(r):
    global font, cell, cy
    fontrows = len(cell)
    if r == fontrows:
        return
    if r < fontrows:
        for i in range(0, 256):
            font[i] = font[i][:r]
        cell = cell[:r]
        cy = 0
    else:
        for i in range(0, 256):
            for j in range(0, r - fontrows):
                font[i].append(0)
        for j in range(0, r - fontrows):
            cell.append(0)
    clip = None
    markchar = None
    return


def load(file):
    global font, cell, currentchar, filename, widefont, height, width
    filename = file
    try:
        f = open(filename, "rb")
        data = bytearray(f.read())
        f.close()
    except:
        return
    r = len(data) // 256
    if r > 0 and r < 33:
        setfontheight(r)
        widefont = False
        width = 8
        height = r
    else:
        setfontheight(r >> 1)
        widefont = True
        width = 16
        r >>= 1
        height = r
    cell = []
    for i in range(r):
        cell.append(0)
    for c in range(0, 256):
        if widefont == False:
            for i in range(r):
                cell[i] = data[c * r + i]
        else:
            for i in range(r):
                cell[i] = data[c * r * 2 + i * 2] << 8 | data[c * r * 2 + i * 2 + 1]
        font[c] = list(cell)
        cell = list(font[currentchar])
    return


def save():
    global cell, font, currentchar, filename, widefont
    font[currentchar] = list(cell)
    if os.path.exists(filename + "~"):
        os.unlink(filename + "~")
    os.rename(filename, filename + "~")
    f = open(filename, "wb")
    for c in range(0, 256):
        for r in range(0, len(cell)):
            if widefont == False:
                f.write(bytearray((font[c][r],)))
            else:
                f.write(bytearray((font[c][r] >> 8, font[c][r] & 255)))
    f.close()
    return


def redraw():
    global screen, currentchar, width
    for y in range(0, len(cell)):
        v = cell[y]
        screen.addstr(y + 1, 0, str((y + 1) % 10))
        for c in range(0, width):
            if v & 1:
                screen.addstr(y + 1, width * 2 - c * 2, "  ", curses.A_REVERSE)
            else:
                screen.addch(y + 1, width * 2 - c * 2, ".")
                screen.addch(y + 1, width * 2 - c * 2 + 1, ".")
            v = v >> 1
    screen.addstr(1, 40, "%02x" % currentchar)
    if currentchar > 31 and currentchar != 127 and currentchar != 255:
        screen.addstr(2, 40, chr(currentchar))
    else:
        screen.addstr(2, 40, "  ")
    for i in range(len(cell), 21):
        screen.addstr(i + 1, 0, "                        ")
    screen.addstr(0, 2, "1 2 3 4 5 6 7 8")
    screen.move(cy + 1, cx * 2 + 2)
    screen.refresh()
    return


def help():
    global screen
    screen.addstr(5, 40, "q - save and quit")
    screen.addstr(6, 40, "Q - quit without saving")
    screen.addstr(7, 40, "arrow keys - move cursor")
    screen.addstr(8, 40, "pgup/p pgdn/n - prev/next character")
    screen.addstr(9, 40, "space - flip dot")
    screen.addstr(10, 40, "i - invert character/block")
    screen.addstr(11, 40, "z - clear character")
    screen.addstr(12, 40, "r/R - rotate down/up")
    screen.addstr(13, 40, "l/L - rotate left/right")
    screen.addstr(14, 40, "T - make characters taller")
    screen.addstr(15, 40, "S - make characters shorter")
    screen.addstr(16, 40, "")
    screen.addstr(17, 40, "m - mark block start")
    screen.addstr(18, 40, "c - copy character/block")
    screen.addstr(19, 40, "P - paste character/block")


def status(s):
    global screen
    screen.move(0, 40)
    screen.clrtoeol()
    screen.addstr(0, 40, s)


def editor(stdscr):
    global screen, cx, cy, currentchar, cell, clip, markchar, height, width, widefont
    screen = stdscr
    screen.clear()
    help()
    while 1:
        redraw()
        c = screen.getch()
        status("")
        if c == ord("q"):
            save()
            break
        if c == ord("Q"):
            break
        elif c == 261:  # right
            cx = (cx + 1) % width
        elif c == 258:  # down
            cy = (cy + 1) % len(cell)
        elif c == 259:  # up
            cy = (cy - 1) % len(cell)
        elif c == 260:  # left
            cx = (cx - 1) % width
        elif c == 338 or c == ord("n"):  # pgdn
            font[currentchar] = list(cell)
            currentchar = (currentchar + 1) % 256
            cell = list(font[currentchar])
        elif c == 339 or c == ord("p"):  # pgup
            font[currentchar] = list(cell)
            currentchar = (currentchar - 1) % 256
            cell = list(font[currentchar])
        elif c == ord("i"):
            font[currentchar] = list(cell)
            if markchar == None:
                markchar = currentchar
            if markchar < currentchar:
                b = markchar
                e = currentchar
            else:
                b = currentchar
                e = markchar
            for i in range(b, e + 1):
                for r in range(0, len(cell)):
                    if widefont == False:
                        font[i][r] = font[i][r] ^ 0xFF
                    else:
                        font[i][r] = font[i][r] ^ 0xFFFF
            cell = list(font[currentchar])
            status("Inverted %d characters" % (e + 1 - b))
            markchar = None
        elif c == ord("z"):
            for i in range(0, len(cell)):
                cell[i] = 0
        elif c == ord("m"):
            markchar = currentchar
            status("Mark placed")
        elif c == ord("c"):
            font[currentchar] = list(cell)
            clip = []
            if markchar == None:
                markchar = currentchar
            if markchar < currentchar:
                b = markchar
                e = currentchar
            else:
                b = currentchar
                e = markchar
            for i in range(b, e + 1):
                clip.append(list(font[i]))
            status("Copied %d characters" % len(clip))
            markchar = None
        elif c == ord("P"):
            b = currentchar
            for e in clip:
                font[b] = e
                b = (b + 1) % 256
            cell = list(clip[0])
            status("Pasted %d characters" % len(clip))
        elif c == ord("R"):
            cell.append(cell.pop(0))
        elif c == ord("r"):
            cell.insert(0, cell.pop())
        elif c == ord("L"):
            for i in range(len(cell)):
                cell[i] = cell[i] >> 1
        elif c == ord("l"):
            for i in range(len(cell)):
                cell[i] = cell[i] << 1
        elif c == ord("T"):
            if len(cell) < 20:
                setfontheight(len(cell) + 1)
        elif c == ord("S"):
            if len(cell) > 1:
                setfontheight(len(cell) - 1)
        elif c == ord(" "):
            v = cell[cy]
            if widefont == True:
                v = v ^ (1 << (15 - cx))
            else:
                v = v ^ (1 << (7 - cx))
            cell[cy] = v
        else:
            status("Unhandled key %s" % (str(c)))
    return


for a in sys.argv:
    if a.startswith("-"):
        if a == "-w":
            widefont = True
    else:
        filename = a

load(filename)
curses.wrapper(editor)
