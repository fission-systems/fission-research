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
func fsl_execute_body(registers, flags, fields []uint64, guest_pc uint64, memory []byte, memory_base uint64) (uint32,uint64,bool) {
if len(fields)!=3 { return 3,0,false }
if fields[0]>uint64(0xf) { return 3,0,false }
if fields[1]>uint64(0xf) { return 3,0,false }
if fields[2]>uint64(0xf) { return 3,0,false }
if fields[0]>=uint64(len(registers)) { return 3,0,false }
if fields[1]>=uint64(len(registers)) { return 3,0,false }
if len(flags)<=0 { return 3,0,false }
if fields[2]>=uint64(len(registers)) { return 3,0,false }
if len(flags)<=0 { return 3,0,false }
for _, flag := range flags { if flag>1 { return 3,0,false } }
var v [5]uint64; _=v
var next uint64; changed:=false
block:=0
for { switch block {
case 0:
v[0]=registers[fields[0]]&uint64(0xff)
v[1]=registers[fields[1]]&uint64(0xff)
v[2]=flags[0]
v[3]=(v[0]+v[1]+v[2]) & uint64(0xff)
v[4]=fsl_runtime_carry(v[0],v[1],v[2],uint64(0xff))
registers[fields[2]]=v[3]
flags[0]=v[4]
return 0,next,changed
default: return 3,0,false
} }
}
func fsl_execute(registers, flags, fields []uint64) uint32 {
if !fsl_runtime_disjoint(registers,flags) { return 3 }
r:=append([]uint64(nil),registers...); f:=append([]uint64(nil),flags...); fields=append([]uint64(nil),fields...)
status,_,_ := fsl_execute_body(r,f,fields,0,nil,0)
if status==0 { copy(registers,r); copy(flags,f) }
return status
}
