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
// x86 mode=32 input-sha256=95bdabe718268114efb3749ef9861a5fe045350c5054bd39695f597c61356263 package-sha256=9c9d8479202b7bd842f89ae0d8c17ef1c4d6b4a51c74d1e78b3138ca2fbbe10b decoder=owned-x86-v1
// binary file-sha256=9db3806444d0870bd071cb36b8c503b85aa702e7878449bd48f0bfe8334a2671 file-offset=4096
func x86_body_20(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
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
v[0]=registers[fields[0]]&uint64(0xffffffff)
v[1]=registers[fields[1]]&uint64(0xffffffff)
registers[fields[0]]=v[1]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_39(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [6]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[0]]&uint64(0xffffffff)
v[1]=v[0] & uint64(0xffffffffffffffff)
if v[1]<memory_base || v[1]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[1]-memory_base)<4 { return 3,0,false }
v[2]=(uint64(memory[v[1]-memory_base+0])<<0)|(uint64(memory[v[1]-memory_base+1])<<8)|(uint64(memory[v[1]-memory_base+2])<<16)|(uint64(memory[v[1]-memory_base+3])<<24)
v[3]=uint64(0x4)
v[4]=(v[0]+v[3]) & uint64(0xffffffff)
registers[fields[0]]=v[4]
v[5]=v[2] & uint64(0xffffffffffffffff)
if changed { return 3,0,false }; next=v[5]; changed=true
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_91(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
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
var v [36]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffff)
v[1]=registers[fields[3]]&uint64(0xffffffff)
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
v[15]=(v[12]+v[12]) & uint64(0xffffffff)
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
v[21]=(v[19]+v[19]) & uint64(0xffffffff)
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
v[26]=(v[25]+v[25]) & uint64(0xffffffff)
v[27],v[28] = v[24],v[26]
block=7; continue
case 7:
v[29]=fields[4]&uint64(0xffffffffffffffff)
v[30]=v[29] & uint64(0xffffffff)
v[31]=(v[27]+v[28]) & uint64(0xffffffff)
v[32]=(v[31]+v[30]) & uint64(0xffffffff)
v[33]=v[32] & uint64(0xffffffffffffffff)
if v[33]<memory_base || v[33]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[33]-memory_base)<4 { return 3,0,false }
v[34]=(uint64(memory[v[33]-memory_base+0])<<0)|(uint64(memory[v[33]-memory_base+1])<<8)|(uint64(memory[v[33]-memory_base+2])<<16)|(uint64(memory[v[33]-memory_base+3])<<24)
v[35]=registers[fields[0]]&uint64(0xffffffff)
registers[fields[0]]=v[34]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_92(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
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
var v [88]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffff)
v[1]=registers[fields[3]]&uint64(0xffffffff)
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
v[15]=(v[12]+v[12]) & uint64(0xffffffff)
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
v[21]=(v[19]+v[19]) & uint64(0xffffffff)
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
v[26]=(v[25]+v[25]) & uint64(0xffffffff)
v[27],v[28] = v[24],v[26]
block=7; continue
case 7:
v[29]=fields[4]&uint64(0xffffffffffffffff)
v[30]=v[29] & uint64(0xffffffff)
v[31]=(v[27]+v[28]) & uint64(0xffffffff)
v[32]=(v[31]+v[30]) & uint64(0xffffffff)
v[33]=v[32] & uint64(0xffffffffffffffff)
if v[33]<memory_base || v[33]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[33]-memory_base)<4 { return 3,0,false }
v[34]=(uint64(memory[v[33]-memory_base+0])<<0)|(uint64(memory[v[33]-memory_base+1])<<8)|(uint64(memory[v[33]-memory_base+2])<<16)|(uint64(memory[v[33]-memory_base+3])<<24)
v[35]=registers[fields[0]]&uint64(0xffffffff)
v[36]=(v[35]+v[34]) & uint64(0xffffffff)
v[37]=uint64(0x0)
v[38]=uint64(0x0)
v[39]=uint64(0x1)
v[40]=fsl_runtime_bool(v[36]==v[37])
v[41]=uint64(0x80000000)
v[42]=(v[36] & v[41]) & uint64(0xffffffff)
v[43]=fsl_runtime_bool(v[42]==v[41])
v[44]=uint64(0x1)
v[45]=(v[36] & v[44]) & uint64(0xffffffff)
v[46]=fsl_runtime_bool(v[45]==v[44])
v[47]=uint64(0x2)
v[48]=(v[36] & v[47]) & uint64(0xffffffff)
v[49]=fsl_runtime_bool(v[48]==v[47])
v[50]=uint64(0x4)
v[51]=(v[36] & v[50]) & uint64(0xffffffff)
v[52]=fsl_runtime_bool(v[51]==v[50])
v[53]=uint64(0x8)
v[54]=(v[36] & v[53]) & uint64(0xffffffff)
v[55]=fsl_runtime_bool(v[54]==v[53])
v[56]=uint64(0x10)
v[57]=(v[36] & v[56]) & uint64(0xffffffff)
v[58]=fsl_runtime_bool(v[57]==v[56])
v[59]=uint64(0x20)
v[60]=(v[36] & v[59]) & uint64(0xffffffff)
v[61]=fsl_runtime_bool(v[60]==v[59])
v[62]=uint64(0x40)
v[63]=(v[36] & v[62]) & uint64(0xffffffff)
v[64]=fsl_runtime_bool(v[63]==v[62])
v[65]=uint64(0x80)
v[66]=(v[36] & v[65]) & uint64(0xffffffff)
v[67]=fsl_runtime_bool(v[66]==v[65])
v[68]=(v[46] ^ v[49]) & uint64(0x1)
v[69]=(v[68] ^ v[52]) & uint64(0x1)
v[70]=(v[69] ^ v[55]) & uint64(0x1)
v[71]=(v[70] ^ v[58]) & uint64(0x1)
v[72]=(v[71] ^ v[61]) & uint64(0x1)
v[73]=(v[72] ^ v[64]) & uint64(0x1)
v[74]=(v[73] ^ v[67]) & uint64(0x1)
v[75]=fsl_runtime_bool(v[74]==v[38])
v[76]=fsl_runtime_carry(v[35],v[34],0,uint64(0xffffffff))
v[77]=(v[35] ^ v[34]) & uint64(0xffffffff)
v[78]=(v[35] ^ v[36]) & uint64(0xffffffff)
v[79]=uint64(0xffffffff)
v[80]=(v[77] ^ v[79]) & uint64(0xffffffff)
v[81]=(v[80] & v[78]) & uint64(0xffffffff)
v[82]=(v[81] & v[41]) & uint64(0xffffffff)
v[83]=fsl_runtime_bool(v[82]==v[41])
v[84]=(v[77] ^ v[36]) & uint64(0xffffffff)
v[85]=uint64(0x10)
v[86]=(v[84] & v[85]) & uint64(0xffffffff)
v[87]=fsl_runtime_bool(v[86]==v[85])
flags[0]=v[76]
flags[4]=v[83]
flags[5]=v[87]
flags[11]=v[39]
flags[1]=v[75]
flags[2]=v[40]
flags[3]=v[43]
flags[6]=v[39]
flags[7]=v[39]
flags[8]=v[39]
flags[9]=v[39]
flags[10]=v[39]
registers[fields[0]]=v[36]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_134(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
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
var v [5]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[0]]&uint64(0xffffffff)
v[1]=registers[fields[2]]&uint64(0xffffffff)
v[2]=uint64(0x4)
v[3]=(v[1] - v[2]) & uint64(0xffffffff)
v[4]=v[3] & uint64(0xffffffffffffffff)
if v[4]<memory_base || v[4]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[4]-memory_base)<4 { return 3,0,false }
memory[v[4]-memory_base+0]=byte(v[0]>>0)
memory[v[4]-memory_base+1]=byte(v[0]>>8)
memory[v[4]-memory_base+2]=byte(v[0]>>16)
memory[v[4]-memory_base+3]=byte(v[0]>>24)
registers[fields[2]]=v[3]
return 0,next,changed
default: return 3,0,false
} }
}
func x86_body_135(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=6 { return 3,0,false }
if fields[0]>uint64(0x1f) { return 3,0,false }
if fields[1]>uint64(0x1f) { return 3,0,false }
if fields[2]>uint64(0x1f) { return 3,0,false }
if fields[3]>uint64(0x1f) { return 3,0,false }
if fields[5]>uint64(0x3) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [5]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[2]]&uint64(0xffffffff)
v[1]=v[0] & uint64(0xffffffffffffffff)
if v[1]<memory_base || v[1]-memory_base>uint64(len(memory)) || uint64(len(memory))-(v[1]-memory_base)<4 { return 3,0,false }
v[2]=(uint64(memory[v[1]-memory_base+0])<<0)|(uint64(memory[v[1]-memory_base+1])<<8)|(uint64(memory[v[1]-memory_base+2])<<16)|(uint64(memory[v[1]-memory_base+3])<<24)
v[3]=uint64(0x4)
v[4]=(v[0]+v[3]) & uint64(0xffffffff)
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
status,next,changed:=x86_body_134(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401001 }
case 0x401001: // raw=89e5
fields:=[]uint64{0x5,0x4,0x0,0x0,0x0,0x0}
status,next,changed:=x86_body_20(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401003 }
case 0x401003: // raw=8b450c
fields:=[]uint64{0x0,0x0,0x5,0x10,0xc,0x0}
status,next,changed:=x86_body_91(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401006 }
case 0x401006: // raw=8b4508
fields:=[]uint64{0x0,0x0,0x5,0x10,0x8,0x0}
status,next,changed:=x86_body_91(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401009 }
case 0x401009: // raw=8b4508
fields:=[]uint64{0x0,0x0,0x5,0x10,0x8,0x0}
status,next,changed:=x86_body_91(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x40100c }
case 0x40100c: // raw=03450c
fields:=[]uint64{0x0,0x0,0x5,0x10,0xc,0x0}
status,next,changed:=x86_body_92(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x40100f }
case 0x40100f: // raw=5d
fields:=[]uint64{0x5,0x0,0x4,0x0,0x0,0x0}
status,next,changed:=x86_body_135(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if changed { pc=next } else { pc=0x401010 }
case 0x401010: // raw=c3
fields:=[]uint64{0x4,0x0,0x0,0x0,0x0,0x0}
status,next,changed:=x86_body_39(r,f,fields,pc,memory,memory_base)
if status!=0 { return status }
if !changed { return 3 }; copy(registers,r); copy(flags,f); copy(destination_memory,memory); *exit_pc=next; return 0
default: return 3
} }
return 3
}
