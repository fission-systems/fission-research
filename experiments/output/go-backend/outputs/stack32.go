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
func fsl_execute(stack []uint64, depth *int) uint32 {
if depth==nil || *depth<0 || *depth>len(stack) { return 3 }
if *depth<2 { return 1 }
if 0>len(stack)-*depth { return 2 }
s:=append([]uint64(nil),stack...); sp:=*depth; _=sp
var v [3]uint64; _=v
block:=0
for { switch block {
case 0:
sp--; v[0]=s[sp]&uint64(0xffffffff)
sp--; v[1]=s[sp]&uint64(0xffffffff)
v[2]=(v[1]+v[0]) & uint64(0xffffffff)
s[sp]=v[2]; sp++
copy(stack,s); *depth=sp; return 0
default: return 3
} }
}
