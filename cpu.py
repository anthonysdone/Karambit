from isa import *

class CPU:
    def __init__(self, mem, entry, os): 
        self.mem = mem
        self.pc = entry
        self.os = os
        self.regs = [0, 0, 0, 0]
        self.z = False
        self.running = False
        self.step_count = 0
        self.debug = False

    def read_addr(self, pc):
        lo = self.mem[pc]
        hi = self.mem[pc + 1]
        return lo + (hi << 8)

    def run(self):
        self.running = True
        while self.running and 0 <= self.pc < len(self.mem):
            if self.debug:
                self.print_state()
            self.step()
            self.step_count += 1

    def print_state(self):
        opcode = self.mem[self.pc]
        mnemonic = "???"
        for name, code in OPCODES.items():
            if code == opcode:
                mnemonic = name
                break

        size = SIZES.get(opcode, 1)
        instr_bytes = " ".join(f"{self.mem[self.pc + i]:02X}" for i in range(size))

        print(f"[{self.step_count:03d}] PC: 0x{self.pc:03X} | {instr_bytes:10} | {mnemonic:6} | R0: {self.regs[0]:4d} | R1: {self.regs[1]:4d} | R2: {self.regs[2]:4d} | R3: {self.regs[3]:4d} | Z: {int(self.z)}")

    def step(self):
        opcode = self.mem[self.pc]

        if opcode == OPCODES["LDI"]:
            r = self.mem[self.pc + 1]
            imm = self.mem[self.pc + 2]
            self.regs[r] = imm
            self.pc += SIZES[opcode]
        
        elif opcode == OPCODES["LDM"]:
            r = self.mem[self.pc + 1]
            addr = self.read_addr(self.pc + 2)
            self.regs[r] = self.mem[addr]
            self.pc += SIZES[opcode]
        
        elif opcode == OPCODES["STM"]:
            r = self.mem[self.pc + 1]
            addr = self.read_addr(self.pc + 2)
            self.mem[addr] = self.regs[r]
            self.pc += SIZES[opcode]

        elif opcode == OPCODES["MOV"]:
            rd = self.mem[self.pc + 1]
            rs = self.mem[self.pc + 2]
            self.regs[rd] = self.regs[rs]
            self.pc += SIZES[opcode]
        
        elif opcode == OPCODES["ADD"]:
            rd = self.mem[self.pc + 1]
            rs = self.mem[self.pc + 2]
            self.regs[rd] = (self.regs[rd] + self.regs[rs]) & 0xFF
            self.pc += SIZES[opcode]

        elif opcode == OPCODES["ADDI"]:
            r = self.mem[self.pc + 1]
            imm = self.mem[self.pc + 2]
            self.regs[r] = (self.regs[r] + imm) & 0xFF
            self.pc += SIZES[opcode]

        elif opcode == OPCODES["SUB"]:
            rd = self.mem[self.pc + 1]
            rs = self.mem[self.pc + 2]
            self.regs[rd] = (self.regs[rd] - self.regs[rs]) & 0xFF
            self.pc += SIZES[opcode]

        elif opcode == OPCODES["SUBI"]:
            r = self.mem[self.pc + 1]
            imm = self.mem[self.pc + 2]
            self.regs[r] = (self.regs[r] - imm) & 0xFF
            self.pc += SIZES[opcode]

        elif opcode == OPCODES["CMP"]:
            ra = self.mem[self.pc + 1]
            rb = self.mem[self.pc + 2]
            self.z = (self.regs[ra] == self.regs[rb])
            self.pc += SIZES[opcode]

        elif opcode == OPCODES["JMP"]:
            addr = self.read_addr(self.pc + 1)
            self.pc = addr

        elif opcode == OPCODES["JZ"]:
            addr = self.read_addr(self.pc + 1)
            if self.z:
                self.pc = addr
            else:
                self.pc += SIZES[opcode]

        elif opcode == OPCODES["JNZ"]:
            addr = self.read_addr(self.pc + 1)
            if not self.z:
                self.pc = addr
            else:
                self.pc += SIZES[opcode]

        elif opcode == OPCODES["CMPI"]:
            r = self.mem[self.pc + 1]
            imm = self.mem[self.pc + 2]
            self.z = (self.regs[r] == imm)
            self.pc += SIZES[opcode]
        
        elif opcode == OPCODES["SYS"]:
            imm = self.mem[self.pc + 1]
            self.os.handle(imm, self.regs, self.mem)
            self.pc += SIZES[opcode]
        
        elif opcode == OPCODES["HLT"]:
            self.running = False
            self.pc += SIZES[opcode]

        else: 
            raise RuntimeError(f"Illegal opcode 0x{opcode:02X} at address 0x{self.pc:04X}")
        