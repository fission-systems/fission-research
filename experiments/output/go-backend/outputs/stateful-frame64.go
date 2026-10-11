// Generated from canonical FIR. Bounded state model; no guest fault/concurrency model.
package fsl

func fsl_runtime_bool(value bool) uint64 { if value { return 1 }; return 0 }
func fsl_runtime_carry(left, right, carry, mask uint64) uint64 {
    return fsl_runtime_bool(right > mask-left || carry > mask-((left+right)&mask))
}
// Safe Go permits overlapping slices. Refuse overlapping output banks explicitly.
func fsl_runtime_disjoint(a, b []uint64) bool {
    if len(a)==0 || len(b)==0 { return true }
    for i := range a { if &a[i]==&b[0] { return false } }
    for i := range b { if &b[i]==&a[0] { return false } }
    return true
}
// x86 mode=64 input-sha256=cef20a263b27e13e27c3730106f6d07229a55cb03812a85eeffc05366b212ff9 package-sha256=9c9d8479202b7bd842f89ae0d8c17ef1c4d6b4a51c74d1e78b3138ca2fbbe10b decoder=owned-x86-v1
// binary file-sha256=9b5c4396ab499ff6b82f8430661ee19c1e201b3ee7f7dd7d9862d40ded6f9945 file-offset=4096
func x86_body_40(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[1]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [2]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[0]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[1]]&uint64(0xffffffffffffffff)
registers[fields[0]]=v[1]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_59(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [5]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[0]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[0]]&uint64(0xffffffffffffffff)
if v[1]<memory_base || v[1]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[1]-memory_base)<8 { return 3,0,false }
v[2]=(uint64(memory[v[1]-memory_base+0])<<0)|(uint64(memory[v[1]-memory_base+1])<<8)|(uint64(memory[v[1]-memory_base+2])<<16)|(uint64(memory[v[1]-memory_base+3])<<24)|(uint64(memory[v[1]-memory_base+4])<<32)|(uint64(memory[v[1]-memory_base+5])<<40)|(uint64(memory[v[1]-memory_base+6])<<48)|(uint64(memory[v[1]-memory_base+7])<<56)
v[3]=uint64(0x8)
v[4]=(v[0]+v[3]) & uint64(0xffffffffffffffff)
registers[fields[0]]=v[4]
if changed { return 3,0,false }; next=v[2]; changed=true
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_119(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[3]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [35]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[3]]&uint64(0xffffffffffffffff)
v[2]=fields[5]&uint64(0xffffffffffffffff)
v[3]=uint64(0x0)
v[4]=uint64(0x1)
v[5]=uint64(0x2)
v[6]=fsl_runtime_bool(v[2]==v[3])
v[7]=fsl_runtime_bool(v[2]==v[4])
v[8]=fsl_runtime_bool(v[2]==v[5])
if v[6]!=0 {
v[9],v[10] = v[0],v[1]
block=1; continue
} else {
v[11],v[12],v[13],v[14] = v[0],v[1],v[7],v[8]
block=2; continue
}
case 1:
v[27],v[28] = v[9],v[10]
block=7; continue
case 2:
v[15]=(v[12]+v[12]) & uint64(0xffffffffffffffff)
if v[13]!=0 {
v[16],v[17] = v[11],v[15]
block=3; continue
} else {
v[18],v[19],v[20] = v[11],v[15],v[14]
block=4; continue
}
case 3:
v[27],v[28] = v[16],v[17]
block=7; continue
case 4:
v[21]=(v[19]+v[19]) & uint64(0xffffffffffffffff)
if v[20]!=0 {
v[22],v[23] = v[18],v[21]
block=5; continue
} else {
v[24],v[25] = v[18],v[21]
block=6; continue
}
case 5:
v[27],v[28] = v[22],v[23]
block=7; continue
case 6:
v[26]=(v[25]+v[25]) & uint64(0xffffffffffffffff)
v[27],v[28] = v[24],v[26]
block=7; continue
case 7:
v[29]=fields[4]&uint64(0xffffffffffffffff)
v[30]=fields[4]&uint64(0xffffffffffffffff)
v[31]=(v[27]+v[28]) & uint64(0xffffffffffffffff)
v[32]=(v[31]+v[30]) & uint64(0xffffffffffffffff)
if v[32]<memory_base || v[32]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[32]-memory_base)<8 { return 3,0,false }
v[33]=(uint64(memory[v[32]-memory_base+0])<<0)|(uint64(memory[v[32]-memory_base+1])<<8)|(uint64(memory[v[32]-memory_base+2])<<16)|(uint64(memory[v[32]-memory_base+3])<<24)|(uint64(memory[v[32]-memory_base+4])<<32)|(uint64(memory[v[32]-memory_base+5])<<40)|(uint64(memory[v[32]-memory_base+6])<<48)|(uint64(memory[v[32]-memory_base+7])<<56)
v[34]=registers[fields[0]]&uint64(0xffffffffffffffff)
registers[fields[0]]=v[33]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_120(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[3]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if len(flags)<=0 { return 3,0,false }
if len(flags)<=4 { return 3,0,false }
if len(flags)<=5 { return 3,0,false }
if len(flags)<=11 { return 3,0,false }
if len(flags)<=1 { return 3,0,false }
if len(flags)<=2 { return 3,0,false }
if len(flags)<=3 { return 3,0,false }
if len(flags)<=6 { return 3,0,false }
if len(flags)<=7 { return 3,0,false }
if len(flags)<=8 { return 3,0,false }
if len(flags)<=9 { return 3,0,false }
if len(flags)<=10 { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [87]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[3]]&uint64(0xffffffffffffffff)
v[2]=fields[5]&uint64(0xffffffffffffffff)
v[3]=uint64(0x0)
v[4]=uint64(0x1)
v[5]=uint64(0x2)
v[6]=fsl_runtime_bool(v[2]==v[3])
v[7]=fsl_runtime_bool(v[2]==v[4])
v[8]=fsl_runtime_bool(v[2]==v[5])
if v[6]!=0 {
v[9],v[10] = v[0],v[1]
block=1; continue
} else {
v[11],v[12],v[13],v[14] = v[0],v[1],v[7],v[8]
block=2; continue
}
case 1:
v[27],v[28] = v[9],v[10]
block=7; continue
case 2:
v[15]=(v[12]+v[12]) & uint64(0xffffffffffffffff)
if v[13]!=0 {
v[16],v[17] = v[11],v[15]
block=3; continue
} else {
v[18],v[19],v[20] = v[11],v[15],v[14]
block=4; continue
}
case 3:
v[27],v[28] = v[16],v[17]
block=7; continue
case 4:
v[21]=(v[19]+v[19]) & uint64(0xffffffffffffffff)
if v[20]!=0 {
v[22],v[23] = v[18],v[21]
block=5; continue
} else {
v[24],v[25] = v[18],v[21]
block=6; continue
}
case 5:
v[27],v[28] = v[22],v[23]
block=7; continue
case 6:
v[26]=(v[25]+v[25]) & uint64(0xffffffffffffffff)
v[27],v[28] = v[24],v[26]
block=7; continue
case 7:
v[29]=fields[4]&uint64(0xffffffffffffffff)
v[30]=fields[4]&uint64(0xffffffffffffffff)
v[31]=(v[27]+v[28]) & uint64(0xffffffffffffffff)
v[32]=(v[31]+v[30]) & uint64(0xffffffffffffffff)
if v[32]<memory_base || v[32]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[32]-memory_base)<8 { return 3,0,false }
v[33]=(uint64(memory[v[32]-memory_base+0])<<0)|(uint64(memory[v[32]-memory_base+1])<<8)|(uint64(memory[v[32]-memory_base+2])<<16)|(uint64(memory[v[32]-memory_base+3])<<24)|(uint64(memory[v[32]-memory_base+4])<<32)|(uint64(memory[v[32]-memory_base+5])<<40)|(uint64(memory[v[32]-memory_base+6])<<48)|(uint64(memory[v[32]-memory_base+7])<<56)
v[34]=registers[fields[0]]&uint64(0xffffffffffffffff)
v[35]=(v[34]+v[33]) & uint64(0xffffffffffffffff)
v[36]=uint64(0x0)
v[37]=uint64(0x0)
v[38]=uint64(0x1)
v[39]=fsl_runtime_bool(v[35]==v[36])
v[40]=uint64(0x8000000000000000)
v[41]=(v[35] & v[40]) & uint64(0xffffffffffffffff)
v[42]=fsl_runtime_bool(v[41]==v[40])
v[43]=uint64(0x1)
v[44]=(v[35] & v[43]) & uint64(0xffffffffffffffff)
v[45]=fsl_runtime_bool(v[44]==v[43])
v[46]=uint64(0x2)
v[47]=(v[35] & v[46]) & uint64(0xffffffffffffffff)
v[48]=fsl_runtime_bool(v[47]==v[46])
v[49]=uint64(0x4)
v[50]=(v[35] & v[49]) & uint64(0xffffffffffffffff)
v[51]=fsl_runtime_bool(v[50]==v[49])
v[52]=uint64(0x8)
v[53]=(v[35] & v[52]) & uint64(0xffffffffffffffff)
v[54]=fsl_runtime_bool(v[53]==v[52])
v[55]=uint64(0x10)
v[56]=(v[35] & v[55]) & uint64(0xffffffffffffffff)
v[57]=fsl_runtime_bool(v[56]==v[55])
v[58]=uint64(0x20)
v[59]=(v[35] & v[58]) & uint64(0xffffffffffffffff)
v[60]=fsl_runtime_bool(v[59]==v[58])
v[61]=uint64(0x40)
v[62]=(v[35] & v[61]) & uint64(0xffffffffffffffff)
v[63]=fsl_runtime_bool(v[62]==v[61])
v[64]=uint64(0x80)
v[65]=(v[35] & v[64]) & uint64(0xffffffffffffffff)
v[66]=fsl_runtime_bool(v[65]==v[64])
v[67]=(v[45] ^ v[48]) & uint64(0x1)
v[68]=(v[67] ^ v[51]) & uint64(0x1)
v[69]=(v[68] ^ v[54]) & uint64(0x1)
v[70]=(v[69] ^ v[57]) & uint64(0x1)
v[71]=(v[70] ^ v[60]) & uint64(0x1)
v[72]=(v[71] ^ v[63]) & uint64(0x1)
v[73]=(v[72] ^ v[66]) & uint64(0x1)
v[74]=fsl_runtime_bool(v[73]==v[37])
v[75]=fsl_runtime_carry(v[34],v[33],0,uint64(0xffffffffffffffff))
v[76]=(v[34] ^ v[33]) & uint64(0xffffffffffffffff)
v[77]=(v[34] ^ v[35]) & uint64(0xffffffffffffffff)
v[78]=uint64(0xffffffffffffffff)
v[79]=(v[76] ^ v[78]) & uint64(0xffffffffffffffff)
v[80]=(v[79] & v[77]) & uint64(0xffffffffffffffff)
v[81]=(v[80] & v[40]) & uint64(0xffffffffffffffff)
v[82]=fsl_runtime_bool(v[81]==v[40])
v[83]=(v[76] ^ v[35]) & uint64(0xffffffffffffffff)
v[84]=uint64(0x10)
v[85]=(v[83] & v[84]) & uint64(0xffffffffffffffff)
v[86]=fsl_runtime_bool(v[85]==v[84])
flags[0]=v[75]
flags[4]=v[82]
flags[5]=v[86]
flags[11]=v[38]
flags[1]=v[74]
flags[2]=v[39]
flags[3]=v[42]
flags[6]=v[38]
flags[7]=v[38]
flags[8]=v[38]
flags[9]=v[38]
flags[10]=v[38]
registers[fields[0]]=v[35]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_138(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[3]>=uint64(len(registers)) { return 3,0,false }
if fields[1]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [34]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[3]]&uint64(0xffffffffffffffff)
v[2]=fields[5]&uint64(0xffffffffffffffff)
v[3]=uint64(0x0)
v[4]=uint64(0x1)
v[5]=uint64(0x2)
v[6]=fsl_runtime_bool(v[2]==v[3])
v[7]=fsl_runtime_bool(v[2]==v[4])
v[8]=fsl_runtime_bool(v[2]==v[5])
if v[6]!=0 {
v[9],v[10] = v[0],v[1]
block=1; continue
} else {
v[11],v[12],v[13],v[14] = v[0],v[1],v[7],v[8]
block=2; continue
}
case 1:
v[27],v[28] = v[9],v[10]
block=7; continue
case 2:
v[15]=(v[12]+v[12]) & uint64(0xffffffffffffffff)
if v[13]!=0 {
v[16],v[17] = v[11],v[15]
block=3; continue
} else {
v[18],v[19],v[20] = v[11],v[15],v[14]
block=4; continue
}
case 3:
v[27],v[28] = v[16],v[17]
block=7; continue
case 4:
v[21]=(v[19]+v[19]) & uint64(0xffffffffffffffff)
if v[20]!=0 {
v[22],v[23] = v[18],v[21]
block=5; continue
} else {
v[24],v[25] = v[18],v[21]
block=6; continue
}
case 5:
v[27],v[28] = v[22],v[23]
block=7; continue
case 6:
v[26]=(v[25]+v[25]) & uint64(0xffffffffffffffff)
v[27],v[28] = v[24],v[26]
block=7; continue
case 7:
v[29]=fields[4]&uint64(0xffffffffffffffff)
v[30]=fields[4]&uint64(0xffffffffffffffff)
v[31]=(v[27]+v[28]) & uint64(0xffffffffffffffff)
v[32]=(v[31]+v[30]) & uint64(0xffffffffffffffff)
v[33]=registers[fields[1]]&uint64(0xffffffffffffffff)
if v[32]<memory_base || v[32]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[32]-memory_base)<8 { return 3,0,false }
memory[v[32]-memory_base+0]=byte(v[33]>>0)
memory[v[32]-memory_base+1]=byte(v[33]>>8)
memory[v[32]-memory_base+2]=byte(v[33]>>16)
memory[v[32]-memory_base+3]=byte(v[33]>>24)
memory[v[32]-memory_base+4]=byte(v[33]>>32)
memory[v[32]-memory_base+5]=byte(v[33]>>40)
memory[v[32]-memory_base+6]=byte(v[33]>>48)
memory[v[32]-memory_base+7]=byte(v[33]>>56)
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_139(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [4]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[0]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[2]]&uint64(0xffffffffffffffff)
v[2]=uint64(0x8)
v[3]=(v[1] - v[2]) & uint64(0xffffffffffffffff)
if v[3]<memory_base || v[3]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[3]-memory_base)<8 { return 3,0,false }
memory[v[3]-memory_base+0]=byte(v[0]>>0)
memory[v[3]-memory_base+1]=byte(v[0]>>8)
memory[v[3]-memory_base+2]=byte(v[0]>>16)
memory[v[3]-memory_base+3]=byte(v[0]>>24)
memory[v[3]-memory_base+4]=byte(v[0]>>32)
memory[v[3]-memory_base+5]=byte(v[0]>>40)
memory[v[3]-memory_base+6]=byte(v[0]>>48)
memory[v[3]-memory_base+7]=byte(v[0]>>56)
registers[fields[2]]=v[3]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_140(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [5]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffffffffffff)
v[1]=registers[fields[2]]&uint64(0xffffffffffffffff)
if v[1]<memory_base || v[1]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[1]-memory_base)<8 { return 3,0,false }
v[2]=(uint64(memory[v[1]-memory_base+0])<<0)|(uint64(memory[v[1]-memory_base+1])<<8)|(uint64(memory[v[1]-memory_base+2])<<16)|(uint64(memory[v[1]-memory_base+3])<<24)|(uint64(memory[v[1]-memory_base+4])<<32)|(uint64(memory[v[1]-memory_base+5])<<40)|(uint64(memory[v[1]-memory_base+6])<<48)|(uint64(memory[v[1]-memory_base+7])<<56)
v[3]=uint64(0x8)
v[4]=(v[0]+v[3]) & uint64(0xffffffffffffffff)
registers[fields[2]]=v[4]
registers[fields[0]]=v[2]
return 0,next,changed
default: return 3,0,false
} }
}
// Explicit banks: GPR[17], flags[12], bounded byte memory. Concurrent access is unsupported.
// Status 0 commits state/exit. Status 3 preserves caller state/memory/exit.
func fsl_x86(registers, flags []uint64, memory []byte, memory_base uint64, budget int, exit_pc *uint64) uint32 {
if len(registers)!=17 || len(flags)!=12 || registers[16]!=0 || budget<=0 || budget>1000000 || exit_pc==nil || memory_base>^uint64(0)-uint64(len(memory)) || !fsl_runtime_disjoint(registers,flags) { return 3 }
for i, flag:=range flags { if flag>1 || (i>=6 && flag!=1) { return 3 }; if &flags[i]==exit_pc { return 3 } }
for i:=range registers { if &registers[i]==exit_pc { return 3 } }
r:=append([]uint64(nil),registers...); f:=append([]uint64(nil),flags...)
if len(memory)>1048576 { return 3 }
destination_memory:=memory; memory=append([]byte(nil),memory...)
pc:=uint64(0x401000)
for step:=0;step<budget;step++ { switch pc {
case 0x401000: // raw=55
fields:=[]uint64{0x5,0x0,0x4,0x0,0x0,0x0}
status,next,changed:=x86_body_139(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401001 }
case 0x401001: // raw=4889e5
fields:=[]uint64{0x5,0x4,0x0,0x0,0x0,0x0}
status,next,changed:=x86_body_40(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401004 }
case 0x401004: // raw=48897df8
fields:=[]uint64{0x10,0x7,0x5,0x10,0xfffffffffffffff8,0x0}
status,next,changed:=x86_body_138(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401008 }
case 0x401008: // raw=488b45f8
fields:=[]uint64{0x0,0x0,0x5,0x10,0xfffffffffffffff8,0x0}
status,next,changed:=x86_body_119(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x40100c }
case 0x40100c: // raw=488b00
fields:=[]uint64{0x0,0x0,0x0,0x10,0x0,0x0}
status,next,changed:=x86_body_119(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x40100f }
case 0x40100f: // raw=488b4df8
fields:=[]uint64{0x1,0x0,0x5,0x10,0xfffffffffffffff8,0x0}
status,next,changed:=x86_body_119(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401013 }
case 0x401013: // raw=48034108
fields:=[]uint64{0x0,0x0,0x1,0x10,0x8,0x0}
status,next,changed:=x86_body_120(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401017 }
case 0x401017: // raw=5d
fields:=[]uint64{0x5,0x0,0x4,0x0,0x0,0x0}
status,next,changed:=x86_body_140(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401018 }
case 0x401018: // raw=c3
fields:=[]uint64{0x4,0x0,0x0,0x0,0x0,0x0}
status,next,changed:=x86_body_59(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if !changed { return 3 }; copy(registers,r); copy(flags,f); copy(destination_memory,memory); *exit_pc=next; return 0
default: return 3
} }
return 3
}
