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
func fsl_execute(registers, flags, lane_registers []uint64, lanes uint16, exec uint64, fields []uint64) uint32 {
if lanes!=64 || exec & ^uint64(0xffffffffffffffff)!=0 || len(lane_registers)%64!=0 { return 3 }
if !fsl_runtime_disjoint(registers,flags) || !fsl_runtime_disjoint(registers,lane_registers) || !fsl_runtime_disjoint(flags,lane_registers) { return 3 }
if len(fields)!=3 { return 3 }
if fields[0]>uint64(0x1ff) { return 3 }
if fields[0]&uint64(0x100)!=uint64(0x100) { return 3 }
if fields[1]>uint64(0xff) { return 3 }
if fields[2]>uint64(0xff) { return 3 }
for _, flag := range flags { if flag>1 { return 3 } }
if fields[0]<uint64(0x100) || fields[0]-uint64(0x100)>=uint64(len(lane_registers)/64) { return 3 }
if fields[1]<uint64(0x0) || fields[1]-uint64(0x0)>=uint64(len(lane_registers)/64) { return 3 }
if fields[2]>=uint64(len(lane_registers)/64) { return 3 }
fields=append([]uint64(nil),fields...)
var v [4][64]uint64; _=v
v[0][0]=exec
for lane:=0;lane<64;lane++ { v[1][lane]=lane_registers[(fields[0]-uint64(0x100))*64+uint64(lane)]&uint64(0xffffffff) }
for lane:=0;lane<64;lane++ { v[2][lane]=lane_registers[(fields[1]-uint64(0x0))*64+uint64(lane)]&uint64(0xffffffff) }
for lane:=0;lane<64;lane++ { v[3][lane]=(v[1][lane]+v[2][lane])&uint64(0xffffffff) }
for lane:=0;lane<64;lane++ { if v[0][0] & (uint64(1)<<uint(lane))!=0 { lane_registers[fields[2]*64+uint64(lane)]=v[3][lane] } }
return 0
}
