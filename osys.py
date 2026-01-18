import time
import sys

class OSys: 
    def __init__(self):
        self.SW = 40
        self.SH = 20
        self.screen = [[32] * self.SW for _ in range(self.SH)]

        self.keybuf = []

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
        else:
            print(f"Unknown system call: {sysno}")