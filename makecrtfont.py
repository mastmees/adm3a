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

font=open("adm3.fnt","rb").read()

result=bytearray()

def dw(b):
    r=0
    if b&0x80:
      r|=0xc000
    if b&0x40:
      r|=0x3000
    if b&0x20:
      r|=0x0c00
    if b&0x10:
      r|=0x0300
    if b&0x08:
      r|=0x00c0
    if b&0x04:
      r|=0x0030
    if b&0x02:
      r|=0x000c
    if b&0x01:
      r|=0x0003
    return bytearray((r>>8,r&255))
      
for c in range(256):
  b = font[c*8:(c+1)*8]
  for r in range(8):
      result.extend(dw(b[r]))
      result.extend(dw(b[r]))
      result.extend(dw(0))

with open("adm3a.fnt","wb") as f:
  f.write(result)
 