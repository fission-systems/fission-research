"""Bounded scalar PTX reference for emitted FSL kernels, not a GPU emulator.

Only PTX 7.0/sm_70, a single entry, integer instructions and flat valid global
buffers are admitted. cvta is identity in this artificial address environment.
No warp scheduling, memory consistency, faults, atomics or hardware is modeled.
Unknown instructions, addresses, labels and uninitialized registers fail.
"""
from __future__ import annotations

import re
import struct


class PtxError(ValueError):
    pass


class Program:
    def __init__(self, text):
        text = re.sub(r"//[^\n]*", "", text)
        match = re.fullmatch(
            r"\s*\.version 7\.0\s+\.target sm_70\s+\.address_size 64\s+"
            r"\.visible \.entry ([A-Za-z_]\w*)\((.*?)\)\s*\{(.*?)\}\s*",
            text, re.S)
        if not match:
            raise PtxError("outside the reference entry/header grammar")
        params = match[2].split(',')
        self.params = []
        for param in params:
            item = re.fullmatch(r"\s*\.param \.u64 ([A-Za-z_]\w*)\s*", param)
            if not item or item[1] in self.params:
                raise PtxError("invalid/duplicate parameter")
            self.params.append(item[1])
        if len(self.params) != 4:
            raise PtxError("reference ABI requires four u64 parameters")
        self.code, self.labels = [], {}
        for line in match[3].splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith('.reg '):
                if not re.fullmatch(r"\.reg \.(pred|u32|u64|b64) %\w+(, %\w+)*;", line):
                    raise PtxError("invalid register declaration")
                continue
            if line.endswith(':'):
                label = line[:-1]
                if not re.fullmatch(r"[A-Za-z_]\w*", label) or label in self.labels:
                    raise PtxError("invalid/duplicate label")
                self.labels[label] = len(self.code)
                continue
            if not line.endswith(';'):
                raise PtxError("instruction must end in semicolon")
            parts = line[:-1].split(None, 1)
            guard = None
            if parts[0].startswith('@'):
                guard = parts[0][1:]
                parts = parts[1].split(None, 1)
                if not re.fullmatch(r"%\w+", guard):
                    raise PtxError("unknown predicate syntax")
            opcode = parts[0]
            operands = [x.strip() for x in parts[1].split(',')] if len(parts) == 2 else []
            counts = {'mov.u32': 2, 'or.b32': 3, 'ld.param.u64': 2,
                      'cvta.to.global.u64': 2, 'ld.global.u64': 2,
                      'st.global.u64': 2, 'st.global.u32': 2,
                      'add.u64': 3, 'sub.u64': 3, 'shl.b64': 3,
                      'and.b64': 3, 'setp.ne.u32': 3, 'setp.eq.u64': 3,
                      'setp.gt.u64': 3, 'setp.lt.u64': 3, 'bra': 1, 'ret': 0}
            if opcode not in counts or len(operands) != counts[opcode]:
                raise PtxError("unmodeled instruction/arity: " + opcode)
            self.code.append((guard, opcode, operands))
        for _, op, args in self.code:
            if op == 'bra' and args[0] not in self.labels:
                raise PtxError("unknown branch label")

    def execute(self, slots, depth, capacity, coordinates=(0, 0, 0, 0, 0, 0), null=None):
        if len(coordinates) != 6 or any(not 0 <= x <= 0xffffffff for x in coordinates):
            raise PtxError("invalid coordinates")
        if any(not 0 <= x <= 0xffffffffffffffff for x in [*slots, depth, capacity]):
            raise PtxError("invalid u64 state")
        if null not in (None, 'stack', 'depth', 'status'):
            raise PtxError("invalid null selector")
        memory, trace = {}, []
        addresses = {'stack': 0x1000, 'depth': 0x10000, 'status': 0x20000}
        def install(address, data):
            for index, byte in enumerate(data):
                if address+index in memory:
                    raise PtxError("overlapping reference buffers")
                memory[address+index] = byte
        install(addresses['stack'], b''.join(struct.pack('<Q', x) for x in slots))
        install(addresses['depth'], struct.pack('<Q', depth))
        install(addresses['status'], struct.pack('<I', 0xeeeeeeee))
        params = dict(zip(self.params, [0 if null == 'stack' else addresses['stack'],
                                      0 if null == 'depth' else addresses['depth'],
                                      capacity, 0 if null == 'status' else addresses['status']]))
        regs = dict(zip(['%ctaid.x', '%ctaid.y', '%ctaid.z', '%tid.x', '%tid.y', '%tid.z'], coordinates))
        def value(token):
            if token.startswith('%'):
                if token not in regs:
                    raise PtxError("uninitialized register: " + token)
                return regs[token]
            try:
                return int(token, 0)
            except ValueError as exc:
                raise PtxError("unknown operand: " + token) from exc
        def read(address, width):
            if address % width or any(address+i not in memory for i in range(width)):
                raise PtxError("unaligned/unmapped read")
            trace.append(('read', address, width))
            return int.from_bytes(bytes(memory[address+i] for i in range(width)), 'little')
        def write(address, width, data):
            if address % width or any(address+i not in memory for i in range(width)):
                raise PtxError("unaligned/unmapped write")
            trace.append(('write', address, width))
            for index, byte in enumerate((data & ((1 << (8*width))-1)).to_bytes(width, 'little')):
                memory[address+index] = byte
        def bracket(token):
            match = re.fullmatch(r"\[([^\[\]]+)\]", token)
            if not match:
                raise PtxError("unknown address syntax")
            return match[1]
        pc = 0
        for _ in range(max(1, len(self.code))*4):
            if pc >= len(self.code):
                raise PtxError("fell through without ret")
            guard, op, args = self.code[pc]
            pc += 1
            if guard is not None and not value(guard):
                continue
            if op == 'ret':
                break
            if op == 'bra':
                pc = self.labels[args[0]]
                continue
            if op.startswith('st.global.'):
                write(value(bracket(args[0])), 4 if op.endswith('u32') else 8, value(args[1]))
                continue
            out = args[0]
            if not re.fullmatch(r"%\w+", out):
                raise PtxError("invalid destination register")
            if op == 'ld.param.u64':
                name = bracket(args[1])
                if name not in params:
                    raise PtxError("unknown parameter")
                result = params[name]
            elif op == 'ld.global.u64':
                result = read(value(bracket(args[1])), 8)
            elif op in ('mov.u32', 'cvta.to.global.u64'):
                result = value(args[1])
            elif op.startswith('setp.'):
                a, b = value(args[1]), value(args[2])
                result = {'eq': a == b, 'ne': a != b, 'gt': a > b, 'lt': a < b}[op.split('.')[1]]
            else:
                a, b = value(args[1]), value(args[2])
                if op == 'or.b32': result = a | b
                elif op == 'and.b64': result = a & b
                elif op == 'add.u64': result = a + b
                elif op == 'sub.u64': result = a - b
                elif op == 'shl.b64': result = 0 if b >= 64 else a << b
                else: raise PtxError("unmodeled execution")
            regs[out] = int(result) & (0xffffffff if op.endswith(('u32', 'b32')) else 0xffffffffffffffff)
        else:
            raise PtxError("reference step bound exceeded")
        def snapshot(address, width):
            return int.from_bytes(bytes(memory[address+i] for i in range(width)), 'little')
        return {'slots': [snapshot(addresses['stack']+i*8, 8) for i in range(len(slots))],
                'depth': snapshot(addresses['depth'], 8),
                'status': snapshot(addresses['status'], 4), 'trace': trace}
