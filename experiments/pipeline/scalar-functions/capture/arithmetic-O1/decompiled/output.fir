x86 program mode=64 base=0x401000 bytes=8 decoder=owned-x86-v2 input-sha256=a11d4f531f99edd897c757d22feff14d252d3f8247dfa5b389faaf7e7fd4b67d package-sha256=4f21befdc46ff60cb74913f0e2dea88b770cc1edbcb414590c99a72b90a67470
binary file-sha256=796531f6f693f05836889aaf23907741c7645da918922819e995ae3078b5935f file-offset=4096 section=.text
instance address=0x401000 offset=0 length=4 raw=488d0437 code="lea" body=lea64_a64 fields=[("destination", 0), ("source", 0), ("base", 7), ("index", 6), ("immediate", 0), ("scale", 0)]
instance address=0x401004 offset=4 length=3 raw=4831d0 code="xor_rm_reg" body=xor64_reg fields=[("destination", 0), ("source", 2), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x401007 offset=7 length=1 raw=c3 code="ret" body=ret64 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instruction xor64_reg
  %v0: u64 name=lhs
  %v1: u64 name=rhs
  %v2: u64 name=result
  %v3: u64 name=zero
  %v4: u1 name=off
  %v5: u1 name=on
  %v6: u1 name=zf
  %v7: u64 name=sign
  %v8: u64 name=signbit
  %v9: u1 name=sf
  %v10: u64 name=p_mask0
  %v11: u64 name=p_bit0
  %v12: u1 name=p0
  %v13: u64 name=p_mask1
  %v14: u64 name=p_bit1
  %v15: u1 name=p1
  %v16: u64 name=p_mask2
  %v17: u64 name=p_bit2
  %v18: u1 name=p2
  %v19: u64 name=p_mask3
  %v20: u64 name=p_bit3
  %v21: u1 name=p3
  %v22: u64 name=p_mask4
  %v23: u64 name=p_bit4
  %v24: u1 name=p4
  %v25: u64 name=p_mask5
  %v26: u64 name=p_bit5
  %v27: u1 name=p5
  %v28: u64 name=p_mask6
  %v29: u64 name=p_bit6
  %v30: u1 name=p6
  %v31: u64 name=p_mask7
  %v32: u64 name=p_bit7
  %v33: u1 name=p7
  %v34: u1 name=parity1
  %v35: u1 name=parity2
  %v36: u1 name=parity3
  %v37: u1 name=parity4
  %v38: u1 name=parity5
  %v39: u1 name=parity6
  %v40: u1 name=parity7
  %v41: u1 name=pf
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 0 }
  RegisterRead { output: ValueId(1), field: 1 }
  IntBinary { output: ValueId(2), left: ValueId(0), right: ValueId(1), op: Xor }
  IntConstant { output: ValueId(3), value: 0 }
  IntConstant { output: ValueId(4), value: 0 }
  IntConstant { output: ValueId(5), value: 1 }
  IntCompare { output: ValueId(6), left: ValueId(2), right: ValueId(3), predicate: Equal }
  IntConstant { output: ValueId(7), value: 9223372036854775808 }
  IntBinary { output: ValueId(8), left: ValueId(2), right: ValueId(7), op: And }
  IntCompare { output: ValueId(9), left: ValueId(8), right: ValueId(7), predicate: Equal }
  IntConstant { output: ValueId(10), value: 1 }
  IntBinary { output: ValueId(11), left: ValueId(2), right: ValueId(10), op: And }
  IntCompare { output: ValueId(12), left: ValueId(11), right: ValueId(10), predicate: Equal }
  IntConstant { output: ValueId(13), value: 2 }
  IntBinary { output: ValueId(14), left: ValueId(2), right: ValueId(13), op: And }
  IntCompare { output: ValueId(15), left: ValueId(14), right: ValueId(13), predicate: Equal }
  IntConstant { output: ValueId(16), value: 4 }
  IntBinary { output: ValueId(17), left: ValueId(2), right: ValueId(16), op: And }
  IntCompare { output: ValueId(18), left: ValueId(17), right: ValueId(16), predicate: Equal }
  IntConstant { output: ValueId(19), value: 8 }
  IntBinary { output: ValueId(20), left: ValueId(2), right: ValueId(19), op: And }
  IntCompare { output: ValueId(21), left: ValueId(20), right: ValueId(19), predicate: Equal }
  IntConstant { output: ValueId(22), value: 16 }
  IntBinary { output: ValueId(23), left: ValueId(2), right: ValueId(22), op: And }
  IntCompare { output: ValueId(24), left: ValueId(23), right: ValueId(22), predicate: Equal }
  IntConstant { output: ValueId(25), value: 32 }
  IntBinary { output: ValueId(26), left: ValueId(2), right: ValueId(25), op: And }
  IntCompare { output: ValueId(27), left: ValueId(26), right: ValueId(25), predicate: Equal }
  IntConstant { output: ValueId(28), value: 64 }
  IntBinary { output: ValueId(29), left: ValueId(2), right: ValueId(28), op: And }
  IntCompare { output: ValueId(30), left: ValueId(29), right: ValueId(28), predicate: Equal }
  IntConstant { output: ValueId(31), value: 128 }
  IntBinary { output: ValueId(32), left: ValueId(2), right: ValueId(31), op: And }
  IntCompare { output: ValueId(33), left: ValueId(32), right: ValueId(31), predicate: Equal }
  IntBinary { output: ValueId(34), left: ValueId(12), right: ValueId(15), op: Xor }
  IntBinary { output: ValueId(35), left: ValueId(34), right: ValueId(18), op: Xor }
  IntBinary { output: ValueId(36), left: ValueId(35), right: ValueId(21), op: Xor }
  IntBinary { output: ValueId(37), left: ValueId(36), right: ValueId(24), op: Xor }
  IntBinary { output: ValueId(38), left: ValueId(37), right: ValueId(27), op: Xor }
  IntBinary { output: ValueId(39), left: ValueId(38), right: ValueId(30), op: Xor }
  IntBinary { output: ValueId(40), left: ValueId(39), right: ValueId(33), op: Xor }
  IntCompare { output: ValueId(41), left: ValueId(40), right: ValueId(4), predicate: Equal }
  FlagWrite { slot: 0, value: ValueId(4) }
  FlagWrite { slot: 4, value: ValueId(4) }
  FlagWrite { slot: 11, value: ValueId(4) }
  FlagWrite { slot: 1, value: ValueId(41) }
  FlagWrite { slot: 2, value: ValueId(6) }
  FlagWrite { slot: 3, value: ValueId(9) }
  FlagWrite { slot: 6, value: ValueId(5) }
  FlagWrite { slot: 7, value: ValueId(5) }
  FlagWrite { slot: 8, value: ValueId(5) }
  FlagWrite { slot: 9, value: ValueId(5) }
  FlagWrite { slot: 10, value: ValueId(5) }
  RegisterWrite { field: 0, value: ValueId(2) }
  Return
instruction lea64_a64
  %v0: u64 name=base
  %v1: u64 name=index
  %v2: u64 name=scale
  %v3: u64 name=s0
  %v4: u64 name=s1
  %v5: u64 name=s2
  %v6: u1 name=c0
  %v7: u1 name=c1
  %v8: u1 name=c2
  %v9: u64 name=b1
  %v10: u64 name=i1
  %v11: u64 name=bc
  %v12: u64 name=ic
  %v13: u1 name=c_one
  %v14: u1 name=c_two
  %v15: u64 name=doubled
  %v16: u64 name=b2
  %v17: u64 name=i2
  %v18: u64 name=bm
  %v19: u64 name=im
  %v20: u1 name=cm
  %v21: u64 name=quad
  %v22: u64 name=b4
  %v23: u64 name=i4
  %v24: u64 name=b8
  %v25: u64 name=i8
  %v26: u64 name=oct
  %v27: u64 name=bs
  %v28: u64 name=ix
  %v29: u64 name=displacement64
  %v30: u64 name=disp
  %v31: u64 name=sum
  %v32: u64 name=addr
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 2 }
  RegisterRead { output: ValueId(1), field: 3 }
  FieldRead { output: ValueId(2), field: 5 }
  IntConstant { output: ValueId(3), value: 0 }
  IntConstant { output: ValueId(4), value: 1 }
  IntConstant { output: ValueId(5), value: 2 }
  IntCompare { output: ValueId(6), left: ValueId(2), right: ValueId(3), predicate: Equal }
  IntCompare { output: ValueId(7), left: ValueId(2), right: ValueId(4), predicate: Equal }
  IntCompare { output: ValueId(8), left: ValueId(2), right: ValueId(5), predicate: Equal }
  CondBranch { condition: ValueId(6), on_true: FirEdge { target: 1, arguments: [ValueId(0), ValueId(1)] }, on_false: FirEdge { target: 2, arguments: [ValueId(0), ValueId(1), ValueId(7), ValueId(8)] } }
block 1 one parameters=[ValueId(9), ValueId(10)]
  Branch(FirEdge { target: 7, arguments: [ValueId(9), ValueId(10)] })
block 2 choose parameters=[ValueId(11), ValueId(12), ValueId(13), ValueId(14)]
  IntAddWrap { output: ValueId(15), left: ValueId(12), right: ValueId(12) }
  CondBranch { condition: ValueId(13), on_true: FirEdge { target: 3, arguments: [ValueId(11), ValueId(15)] }, on_false: FirEdge { target: 4, arguments: [ValueId(11), ValueId(15), ValueId(14)] } }
block 3 two parameters=[ValueId(16), ValueId(17)]
  Branch(FirEdge { target: 7, arguments: [ValueId(16), ValueId(17)] })
block 4 more parameters=[ValueId(18), ValueId(19), ValueId(20)]
  IntAddWrap { output: ValueId(21), left: ValueId(19), right: ValueId(19) }
  CondBranch { condition: ValueId(20), on_true: FirEdge { target: 5, arguments: [ValueId(18), ValueId(21)] }, on_false: FirEdge { target: 6, arguments: [ValueId(18), ValueId(21)] } }
block 5 four parameters=[ValueId(22), ValueId(23)]
  Branch(FirEdge { target: 7, arguments: [ValueId(22), ValueId(23)] })
block 6 eight parameters=[ValueId(24), ValueId(25)]
  IntAddWrap { output: ValueId(26), left: ValueId(25), right: ValueId(25) }
  Branch(FirEdge { target: 7, arguments: [ValueId(24), ValueId(26)] })
block 7 sum parameters=[ValueId(27), ValueId(28)]
  FieldRead { output: ValueId(29), field: 4 }
  FieldRead { output: ValueId(30), field: 4 }
  IntAddWrap { output: ValueId(31), left: ValueId(27), right: ValueId(28) }
  IntAddWrap { output: ValueId(32), left: ValueId(31), right: ValueId(30) }
  RegisterWrite { field: 0, value: ValueId(32) }
  Return
instruction ret64
  %v0: u64 name=sp
  %v1: u64 name=address
  %v2: u64 name=target
  %v3: u64 name=step
  %v4: u64 name=after
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 0 }
  RegisterRead { output: ValueId(1), field: 0 }
  MemoryLoadLittle { output: ValueId(2), address: ValueId(1) }
  IntConstant { output: ValueId(3), value: 8 }
  IntAddWrap { output: ValueId(4), left: ValueId(0), right: ValueId(3) }
  RegisterWrite { field: 0, value: ValueId(4) }
  GuestNextPcWrite { value: ValueId(2) }
  Return
