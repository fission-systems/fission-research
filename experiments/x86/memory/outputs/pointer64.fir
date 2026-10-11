x86 program mode=64 base=0x401000 bytes=8 decoder=owned-x86-v1 input-sha256=620d79c713991a3cdfa8915af87b58fe672bc9f6fd18b966d5466becc4aef0c9 package-sha256=c4cc794b0e8f103591df300da4fc1dcfa7edfb78dee9e0e015a7ee0385da9dad
binary file-sha256=90e5c3a8c2ee6136272f708cf638fd4cb222320153f45d8bec7fa0dbdbc97578 file-offset=4096 section=.text
instance address=0x401000 offset=0 length=4 raw=488b4708 code="mov_reg_rm" body=mov64_load_a64 fields=[("destination", 0), ("source", 0), ("base", 7), ("index", 16), ("immediate", 8), ("scale", 0)]
  operand memory-source address-bits=64 domain=flat-byte-window segment-bases=0
instance address=0x401004 offset=4 length=3 raw=480307 code="add_reg_rm" body=add64_load_a64 fields=[("destination", 0), ("source", 0), ("base", 7), ("index", 16), ("immediate", 0), ("scale", 0)]
  operand memory-source address-bits=64 domain=flat-byte-window segment-bases=0
instance address=0x401007 offset=7 length=1 raw=c3 code="ret" body=ret64 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
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
instruction mov64_load_a64
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
  %v33: u64 name=rhs
  %v34: u64 name=lhs
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
  MemoryLoadLittle { output: ValueId(33), address: ValueId(32) }
  RegisterRead { output: ValueId(34), field: 0 }
  RegisterWrite { field: 0, value: ValueId(33) }
  Return
instruction add64_load_a64
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
  %v33: u64 name=rhs
  %v34: u64 name=lhs
  %v35: u64 name=result
  %v36: u64 name=zero
  %v37: u1 name=off
  %v38: u1 name=on
  %v39: u1 name=zf
  %v40: u64 name=sign
  %v41: u64 name=signbit
  %v42: u1 name=sf
  %v43: u64 name=p_mask0
  %v44: u64 name=p_bit0
  %v45: u1 name=p0
  %v46: u64 name=p_mask1
  %v47: u64 name=p_bit1
  %v48: u1 name=p1
  %v49: u64 name=p_mask2
  %v50: u64 name=p_bit2
  %v51: u1 name=p2
  %v52: u64 name=p_mask3
  %v53: u64 name=p_bit3
  %v54: u1 name=p3
  %v55: u64 name=p_mask4
  %v56: u64 name=p_bit4
  %v57: u1 name=p4
  %v58: u64 name=p_mask5
  %v59: u64 name=p_bit5
  %v60: u1 name=p5
  %v61: u64 name=p_mask6
  %v62: u64 name=p_bit6
  %v63: u1 name=p6
  %v64: u64 name=p_mask7
  %v65: u64 name=p_bit7
  %v66: u1 name=p7
  %v67: u1 name=parity1
  %v68: u1 name=parity2
  %v69: u1 name=parity3
  %v70: u1 name=parity4
  %v71: u1 name=parity5
  %v72: u1 name=parity6
  %v73: u1 name=parity7
  %v74: u1 name=pf
  %v75: u1 name=cf
  %v76: u64 name=lr
  %v77: u64 name=lo
  %v78: u64 name=all
  %v79: u64 name=notlr
  %v80: u64 name=ov
  %v81: u64 name=ovsign
  %v82: u1 name=of
  %v83: u64 name=afmix
  %v84: u64 name=afmask
  %v85: u64 name=afbit
  %v86: u1 name=af
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
  MemoryLoadLittle { output: ValueId(33), address: ValueId(32) }
  RegisterRead { output: ValueId(34), field: 0 }
  IntAddWrap { output: ValueId(35), left: ValueId(34), right: ValueId(33) }
  IntConstant { output: ValueId(36), value: 0 }
  IntConstant { output: ValueId(37), value: 0 }
  IntConstant { output: ValueId(38), value: 1 }
  IntCompare { output: ValueId(39), left: ValueId(35), right: ValueId(36), predicate: Equal }
  IntConstant { output: ValueId(40), value: 9223372036854775808 }
  IntBinary { output: ValueId(41), left: ValueId(35), right: ValueId(40), op: And }
  IntCompare { output: ValueId(42), left: ValueId(41), right: ValueId(40), predicate: Equal }
  IntConstant { output: ValueId(43), value: 1 }
  IntBinary { output: ValueId(44), left: ValueId(35), right: ValueId(43), op: And }
  IntCompare { output: ValueId(45), left: ValueId(44), right: ValueId(43), predicate: Equal }
  IntConstant { output: ValueId(46), value: 2 }
  IntBinary { output: ValueId(47), left: ValueId(35), right: ValueId(46), op: And }
  IntCompare { output: ValueId(48), left: ValueId(47), right: ValueId(46), predicate: Equal }
  IntConstant { output: ValueId(49), value: 4 }
  IntBinary { output: ValueId(50), left: ValueId(35), right: ValueId(49), op: And }
  IntCompare { output: ValueId(51), left: ValueId(50), right: ValueId(49), predicate: Equal }
  IntConstant { output: ValueId(52), value: 8 }
  IntBinary { output: ValueId(53), left: ValueId(35), right: ValueId(52), op: And }
  IntCompare { output: ValueId(54), left: ValueId(53), right: ValueId(52), predicate: Equal }
  IntConstant { output: ValueId(55), value: 16 }
  IntBinary { output: ValueId(56), left: ValueId(35), right: ValueId(55), op: And }
  IntCompare { output: ValueId(57), left: ValueId(56), right: ValueId(55), predicate: Equal }
  IntConstant { output: ValueId(58), value: 32 }
  IntBinary { output: ValueId(59), left: ValueId(35), right: ValueId(58), op: And }
  IntCompare { output: ValueId(60), left: ValueId(59), right: ValueId(58), predicate: Equal }
  IntConstant { output: ValueId(61), value: 64 }
  IntBinary { output: ValueId(62), left: ValueId(35), right: ValueId(61), op: And }
  IntCompare { output: ValueId(63), left: ValueId(62), right: ValueId(61), predicate: Equal }
  IntConstant { output: ValueId(64), value: 128 }
  IntBinary { output: ValueId(65), left: ValueId(35), right: ValueId(64), op: And }
  IntCompare { output: ValueId(66), left: ValueId(65), right: ValueId(64), predicate: Equal }
  IntBinary { output: ValueId(67), left: ValueId(45), right: ValueId(48), op: Xor }
  IntBinary { output: ValueId(68), left: ValueId(67), right: ValueId(51), op: Xor }
  IntBinary { output: ValueId(69), left: ValueId(68), right: ValueId(54), op: Xor }
  IntBinary { output: ValueId(70), left: ValueId(69), right: ValueId(57), op: Xor }
  IntBinary { output: ValueId(71), left: ValueId(70), right: ValueId(60), op: Xor }
  IntBinary { output: ValueId(72), left: ValueId(71), right: ValueId(63), op: Xor }
  IntBinary { output: ValueId(73), left: ValueId(72), right: ValueId(66), op: Xor }
  IntCompare { output: ValueId(74), left: ValueId(73), right: ValueId(37), predicate: Equal }
  IntAddCarry { output: ValueId(75), left: ValueId(34), right: ValueId(33) }
  IntBinary { output: ValueId(76), left: ValueId(34), right: ValueId(33), op: Xor }
  IntBinary { output: ValueId(77), left: ValueId(34), right: ValueId(35), op: Xor }
  IntConstant { output: ValueId(78), value: 18446744073709551615 }
  IntBinary { output: ValueId(79), left: ValueId(76), right: ValueId(78), op: Xor }
  IntBinary { output: ValueId(80), left: ValueId(79), right: ValueId(77), op: And }
  IntBinary { output: ValueId(81), left: ValueId(80), right: ValueId(40), op: And }
  IntCompare { output: ValueId(82), left: ValueId(81), right: ValueId(40), predicate: Equal }
  IntBinary { output: ValueId(83), left: ValueId(76), right: ValueId(35), op: Xor }
  IntConstant { output: ValueId(84), value: 16 }
  IntBinary { output: ValueId(85), left: ValueId(83), right: ValueId(84), op: And }
  IntCompare { output: ValueId(86), left: ValueId(85), right: ValueId(84), predicate: Equal }
  FlagWrite { slot: 0, value: ValueId(75) }
  FlagWrite { slot: 4, value: ValueId(82) }
  FlagWrite { slot: 5, value: ValueId(86) }
  FlagWrite { slot: 11, value: ValueId(38) }
  FlagWrite { slot: 1, value: ValueId(74) }
  FlagWrite { slot: 2, value: ValueId(39) }
  FlagWrite { slot: 3, value: ValueId(42) }
  FlagWrite { slot: 6, value: ValueId(38) }
  FlagWrite { slot: 7, value: ValueId(38) }
  FlagWrite { slot: 8, value: ValueId(38) }
  FlagWrite { slot: 9, value: ValueId(38) }
  FlagWrite { slot: 10, value: ValueId(38) }
  RegisterWrite { field: 0, value: ValueId(35) }
  Return
