x86 program mode=32 base=0x401000 bytes=9 decoder=owned-x86-v1 input-sha256=03eb65ee1278aaea9e96db8222739d1ba135fbd627cad205af3cafa49abc3a34 package-sha256=c4cc794b0e8f103591df300da4fc1dcfa7edfb78dee9e0e015a7ee0385da9dad
binary file-sha256=1e5840c7021534dde18c4871cedafb9a55c885be45549b8884cb709277a7f0fc file-offset=4096 section=.text
instance address=0x401000 offset=0 length=4 raw=8b442408 code="mov_reg_rm" body=mov32_load_a32 fields=[("destination", 0), ("source", 0), ("base", 4), ("index", 16), ("immediate", 8), ("scale", 0)]
  operand memory-source address-bits=32 domain=flat-byte-window segment-bases=0
instance address=0x401004 offset=4 length=4 raw=03442404 code="add_reg_rm" body=add32_load_a32 fields=[("destination", 0), ("source", 0), ("base", 4), ("index", 16), ("immediate", 4), ("scale", 0)]
  operand memory-source address-bits=32 domain=flat-byte-window segment-bases=0
instance address=0x401008 offset=8 length=1 raw=c3 code="ret" body=ret32 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instruction ret32
  %v0: u32 name=sp
  %v1: u64 name=address
  %v2: u32 name=target
  %v3: u32 name=step
  %v4: u32 name=after
  %v5: u64 name=exit
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 0 }
  IntConvert { output: ValueId(1), input: ValueId(0), kind: ZeroExtend }
  MemoryLoadLittle { output: ValueId(2), address: ValueId(1) }
  IntConstant { output: ValueId(3), value: 4 }
  IntAddWrap { output: ValueId(4), left: ValueId(0), right: ValueId(3) }
  RegisterWrite { field: 0, value: ValueId(4) }
  IntConvert { output: ValueId(5), input: ValueId(2), kind: ZeroExtend }
  GuestNextPcWrite { value: ValueId(5) }
  Return
instruction mov32_load_a32
  %v0: u32 name=base
  %v1: u32 name=index
  %v2: u64 name=scale
  %v3: u64 name=s0
  %v4: u64 name=s1
  %v5: u64 name=s2
  %v6: u1 name=c0
  %v7: u1 name=c1
  %v8: u1 name=c2
  %v9: u32 name=b1
  %v10: u32 name=i1
  %v11: u32 name=bc
  %v12: u32 name=ic
  %v13: u1 name=c_one
  %v14: u1 name=c_two
  %v15: u32 name=doubled
  %v16: u32 name=b2
  %v17: u32 name=i2
  %v18: u32 name=bm
  %v19: u32 name=im
  %v20: u1 name=cm
  %v21: u32 name=quad
  %v22: u32 name=b4
  %v23: u32 name=i4
  %v24: u32 name=b8
  %v25: u32 name=i8
  %v26: u32 name=oct
  %v27: u32 name=bs
  %v28: u32 name=ix
  %v29: u64 name=displacement64
  %v30: u32 name=disp
  %v31: u32 name=sum
  %v32: u32 name=addr
  %v33: u64 name=memory_address
  %v34: u32 name=rhs
  %v35: u32 name=lhs
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
  IntConvert { output: ValueId(30), input: ValueId(29), kind: Truncate }
  IntAddWrap { output: ValueId(31), left: ValueId(27), right: ValueId(28) }
  IntAddWrap { output: ValueId(32), left: ValueId(31), right: ValueId(30) }
  IntConvert { output: ValueId(33), input: ValueId(32), kind: ZeroExtend }
  MemoryLoadLittle { output: ValueId(34), address: ValueId(33) }
  RegisterRead { output: ValueId(35), field: 0 }
  RegisterWrite { field: 0, value: ValueId(34) }
  Return
instruction add32_load_a32
  %v0: u32 name=base
  %v1: u32 name=index
  %v2: u64 name=scale
  %v3: u64 name=s0
  %v4: u64 name=s1
  %v5: u64 name=s2
  %v6: u1 name=c0
  %v7: u1 name=c1
  %v8: u1 name=c2
  %v9: u32 name=b1
  %v10: u32 name=i1
  %v11: u32 name=bc
  %v12: u32 name=ic
  %v13: u1 name=c_one
  %v14: u1 name=c_two
  %v15: u32 name=doubled
  %v16: u32 name=b2
  %v17: u32 name=i2
  %v18: u32 name=bm
  %v19: u32 name=im
  %v20: u1 name=cm
  %v21: u32 name=quad
  %v22: u32 name=b4
  %v23: u32 name=i4
  %v24: u32 name=b8
  %v25: u32 name=i8
  %v26: u32 name=oct
  %v27: u32 name=bs
  %v28: u32 name=ix
  %v29: u64 name=displacement64
  %v30: u32 name=disp
  %v31: u32 name=sum
  %v32: u32 name=addr
  %v33: u64 name=memory_address
  %v34: u32 name=rhs
  %v35: u32 name=lhs
  %v36: u32 name=result
  %v37: u32 name=zero
  %v38: u1 name=off
  %v39: u1 name=on
  %v40: u1 name=zf
  %v41: u32 name=sign
  %v42: u32 name=signbit
  %v43: u1 name=sf
  %v44: u32 name=p_mask0
  %v45: u32 name=p_bit0
  %v46: u1 name=p0
  %v47: u32 name=p_mask1
  %v48: u32 name=p_bit1
  %v49: u1 name=p1
  %v50: u32 name=p_mask2
  %v51: u32 name=p_bit2
  %v52: u1 name=p2
  %v53: u32 name=p_mask3
  %v54: u32 name=p_bit3
  %v55: u1 name=p3
  %v56: u32 name=p_mask4
  %v57: u32 name=p_bit4
  %v58: u1 name=p4
  %v59: u32 name=p_mask5
  %v60: u32 name=p_bit5
  %v61: u1 name=p5
  %v62: u32 name=p_mask6
  %v63: u32 name=p_bit6
  %v64: u1 name=p6
  %v65: u32 name=p_mask7
  %v66: u32 name=p_bit7
  %v67: u1 name=p7
  %v68: u1 name=parity1
  %v69: u1 name=parity2
  %v70: u1 name=parity3
  %v71: u1 name=parity4
  %v72: u1 name=parity5
  %v73: u1 name=parity6
  %v74: u1 name=parity7
  %v75: u1 name=pf
  %v76: u1 name=cf
  %v77: u32 name=lr
  %v78: u32 name=lo
  %v79: u32 name=all
  %v80: u32 name=notlr
  %v81: u32 name=ov
  %v82: u32 name=ovsign
  %v83: u1 name=of
  %v84: u32 name=afmix
  %v85: u32 name=afmask
  %v86: u32 name=afbit
  %v87: u1 name=af
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
  IntConvert { output: ValueId(30), input: ValueId(29), kind: Truncate }
  IntAddWrap { output: ValueId(31), left: ValueId(27), right: ValueId(28) }
  IntAddWrap { output: ValueId(32), left: ValueId(31), right: ValueId(30) }
  IntConvert { output: ValueId(33), input: ValueId(32), kind: ZeroExtend }
  MemoryLoadLittle { output: ValueId(34), address: ValueId(33) }
  RegisterRead { output: ValueId(35), field: 0 }
  IntAddWrap { output: ValueId(36), left: ValueId(35), right: ValueId(34) }
  IntConstant { output: ValueId(37), value: 0 }
  IntConstant { output: ValueId(38), value: 0 }
  IntConstant { output: ValueId(39), value: 1 }
  IntCompare { output: ValueId(40), left: ValueId(36), right: ValueId(37), predicate: Equal }
  IntConstant { output: ValueId(41), value: 2147483648 }
  IntBinary { output: ValueId(42), left: ValueId(36), right: ValueId(41), op: And }
  IntCompare { output: ValueId(43), left: ValueId(42), right: ValueId(41), predicate: Equal }
  IntConstant { output: ValueId(44), value: 1 }
  IntBinary { output: ValueId(45), left: ValueId(36), right: ValueId(44), op: And }
  IntCompare { output: ValueId(46), left: ValueId(45), right: ValueId(44), predicate: Equal }
  IntConstant { output: ValueId(47), value: 2 }
  IntBinary { output: ValueId(48), left: ValueId(36), right: ValueId(47), op: And }
  IntCompare { output: ValueId(49), left: ValueId(48), right: ValueId(47), predicate: Equal }
  IntConstant { output: ValueId(50), value: 4 }
  IntBinary { output: ValueId(51), left: ValueId(36), right: ValueId(50), op: And }
  IntCompare { output: ValueId(52), left: ValueId(51), right: ValueId(50), predicate: Equal }
  IntConstant { output: ValueId(53), value: 8 }
  IntBinary { output: ValueId(54), left: ValueId(36), right: ValueId(53), op: And }
  IntCompare { output: ValueId(55), left: ValueId(54), right: ValueId(53), predicate: Equal }
  IntConstant { output: ValueId(56), value: 16 }
  IntBinary { output: ValueId(57), left: ValueId(36), right: ValueId(56), op: And }
  IntCompare { output: ValueId(58), left: ValueId(57), right: ValueId(56), predicate: Equal }
  IntConstant { output: ValueId(59), value: 32 }
  IntBinary { output: ValueId(60), left: ValueId(36), right: ValueId(59), op: And }
  IntCompare { output: ValueId(61), left: ValueId(60), right: ValueId(59), predicate: Equal }
  IntConstant { output: ValueId(62), value: 64 }
  IntBinary { output: ValueId(63), left: ValueId(36), right: ValueId(62), op: And }
  IntCompare { output: ValueId(64), left: ValueId(63), right: ValueId(62), predicate: Equal }
  IntConstant { output: ValueId(65), value: 128 }
  IntBinary { output: ValueId(66), left: ValueId(36), right: ValueId(65), op: And }
  IntCompare { output: ValueId(67), left: ValueId(66), right: ValueId(65), predicate: Equal }
  IntBinary { output: ValueId(68), left: ValueId(46), right: ValueId(49), op: Xor }
  IntBinary { output: ValueId(69), left: ValueId(68), right: ValueId(52), op: Xor }
  IntBinary { output: ValueId(70), left: ValueId(69), right: ValueId(55), op: Xor }
  IntBinary { output: ValueId(71), left: ValueId(70), right: ValueId(58), op: Xor }
  IntBinary { output: ValueId(72), left: ValueId(71), right: ValueId(61), op: Xor }
  IntBinary { output: ValueId(73), left: ValueId(72), right: ValueId(64), op: Xor }
  IntBinary { output: ValueId(74), left: ValueId(73), right: ValueId(67), op: Xor }
  IntCompare { output: ValueId(75), left: ValueId(74), right: ValueId(38), predicate: Equal }
  IntAddCarry { output: ValueId(76), left: ValueId(35), right: ValueId(34) }
  IntBinary { output: ValueId(77), left: ValueId(35), right: ValueId(34), op: Xor }
  IntBinary { output: ValueId(78), left: ValueId(35), right: ValueId(36), op: Xor }
  IntConstant { output: ValueId(79), value: 4294967295 }
  IntBinary { output: ValueId(80), left: ValueId(77), right: ValueId(79), op: Xor }
  IntBinary { output: ValueId(81), left: ValueId(80), right: ValueId(78), op: And }
  IntBinary { output: ValueId(82), left: ValueId(81), right: ValueId(41), op: And }
  IntCompare { output: ValueId(83), left: ValueId(82), right: ValueId(41), predicate: Equal }
  IntBinary { output: ValueId(84), left: ValueId(77), right: ValueId(36), op: Xor }
  IntConstant { output: ValueId(85), value: 16 }
  IntBinary { output: ValueId(86), left: ValueId(84), right: ValueId(85), op: And }
  IntCompare { output: ValueId(87), left: ValueId(86), right: ValueId(85), predicate: Equal }
  FlagWrite { slot: 0, value: ValueId(76) }
  FlagWrite { slot: 4, value: ValueId(83) }
  FlagWrite { slot: 5, value: ValueId(87) }
  FlagWrite { slot: 11, value: ValueId(39) }
  FlagWrite { slot: 1, value: ValueId(75) }
  FlagWrite { slot: 2, value: ValueId(40) }
  FlagWrite { slot: 3, value: ValueId(43) }
  FlagWrite { slot: 6, value: ValueId(39) }
  FlagWrite { slot: 7, value: ValueId(39) }
  FlagWrite { slot: 8, value: ValueId(39) }
  FlagWrite { slot: 9, value: ValueId(39) }
  FlagWrite { slot: 10, value: ValueId(39) }
  RegisterWrite { field: 0, value: ValueId(36) }
  Return
