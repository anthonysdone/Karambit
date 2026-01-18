import time
import random
import sys

class OSys: 
    def __init__(self):
        self.SW = 40
        self.SH = 20
        self.screen = [[32] * self.SW for _ in range(self.SH)]

        self.keybuf = []

        self.gw = 0
        self.gh = 0
        self.grid = []
        self.next_grid = []

        self.arr = [0] * 256

    def putc(self, regs):
        print(chr(regs[0]), end="")
        sys.stdout.flush()

    def prints(self, regs, mem): 
        addr = regs[0] + (regs[1] << 8)
        while mem[addr] != 0:
            print(chr(mem[addr]), end="")
            addr += 1
        sys.stdout.flush()

    def cls(self):
        for y in range(self.SH):
            for x in range(self.SW): 
                self.screen[y][x] = 32

    def putxy(self, regs):
        x, y, c = regs[0], regs[1], regs[2]
        if 0 <= x < self.SW and 0 <= y < self.SH: 
            self.screen[y][x] = c
    
    def render(self):
        print("\x1b[H", end="")
        for row in self.screen:
            print("".join(chr(c) for c in row))
        sys.stdout.flush()
    
    def sleep(self, regs):
        time.sleep(regs[0] / 1000.0)

    def key(self, regs):
        if not self.keybuf:
            line = input()
            for ch in line:
                self.keybuf.append(ord(ch))
            self.keybuf.append(10)

        regs[0] = self.keybuf.pop(0)

    def gridset(self, regs): 
        self.gw = regs[0]
        self.gh = regs[1]
        size = self.gw * self.gh
        self.grid = [0] * size
        self.next_grid = [0] * size

    def gget(self, regs):
        x, y = regs[0], regs[1]
        if 0 <= x < self.gw and 0 <= y < self.gh: 
            regs[0] = self.grid[y * self.gw + x]
        else:
            regs[0] = 0

    def gset(self, regs):
        x, y, val = regs[0], regs[1], regs[2]
        if 0 <= x < self.gw and 0 <= y < self.gh: 
            self.grid[y * self.gw + x] = 1 if val != 0 else 0
    
    def gnset(self, regs):
        x, y, val = regs[0], regs[1], regs[2]
        if 0 <= x < self.gw and 0 <= y < self.gh: 
            self.next_grid[y * self.gw + x] = 1 if val != 0 else 0

    def gswap(self): 
        self.grid, self.next_grid = self.next_grid, self.grid
        for i in range(len(self.next_grid)):
            self.next_grid[i] = 0

    def aget(self, regs):
        idx = regs[0]
        if 0 <= idx < 256:
            regs[0] = self.arr[idx]
        
    def aset(self, regs):
        idx, val = regs[0], regs[1]
        if 0 <= idx < 256:
            self.arr[idx] = val

    def rand(self, regs):
        max_val = regs[0]
        if max_val > 0:
            regs[0] = random.randint(0, max_val - 1)
        else:
            regs[0] = 0
    
    def handle(self, sysno, regs, mem): 
        if sysno == 0:          # PUTC
            self.putc(regs)
        elif sysno == 1:        # PRINTS
            self.prints(regs, mem)
        elif sysno == 2:        # CLS
            self.cls()
        elif sysno == 3:        # PUTXY
            self.putxy(regs)
        elif sysno == 4:        # RENDER
            self.render()
        elif sysno == 5:        # SLEEP
            self.sleep(regs)
        elif sysno == 6:        # KEY
            self.key(regs)
        elif sysno == 10:       # GRIDSET
            self.gridset(regs)
        elif sysno == 11:       # GGET
            self.gget(regs)
        elif sysno == 12:       # GSET
            self.gset(regs)
        elif sysno == 13:       # GNSET
            self.gnset(regs)
        elif sysno == 14:       # GSWAP
            self.gswap()
        elif sysno == 20:       # AGET
            self.aget(regs)
        elif sysno == 21:       # ASET
            self.aset(regs)
        elif sysno == 22:       # RAND
            self.rand(regs)
        else:
            print(f"Unknown system call: {sysno}")