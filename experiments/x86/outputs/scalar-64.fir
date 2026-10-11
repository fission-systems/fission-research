x86 program mode=64 base=0x1000 bytes=24 decoder=owned-x86-v1 input-sha256=f54283137f412e1943e920ecd38b20dfa924a8b4e14c3864fd259731d919195a package-sha256=0423223eaf7238013177aceb9b7c09f7448a682752668e3124ab9c651b46515a
instance address=0x1000 offset=0 length=10 raw=48b80700000000000000 code="mov_opreg_imm" body=mov64_imm fields=[("destination", 0), ("source", 0), ("base", 0), ("index", 0), ("immediate", 7), ("scale", 0)]
instance address=0x100a offset=10 length=10 raw=48bb0500000000000000 code="mov_opreg_imm" body=mov64_imm fields=[("destination", 3), ("source", 0), ("base", 0), ("index", 0), ("immediate", 5), ("scale", 0)]
instance address=0x1014 offset=20 length=3 raw=4801d8 code="add_rm_reg" body=add64_reg fields=[("destination", 0), ("source", 3), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x1017 offset=23 length=1 raw=c3 code="ret" body=ret64 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instruction mov64_imm encoding=Encoding { bits: 128, mask: 340277174624079928635746076935438991360, value: 218076468058462760398280845827244032, fields: [BitField { name: "destination", offset: 0, bits: 5, excluded: [] }, BitField { name: "source", offset: 5, bits: 5, excluded: [] }, BitField { name: "base", offset: 10, bits: 5, excluded: [] }, BitField { name: "index", offset: 15, bits: 5, excluded: [] }, BitField { name: "immediate", offset: 20, bits: 64, excluded: [] }, BitField { name: "scale", offset: 84, bits: 2, excluded: [] }] }
  %v0: u64 = register.read destination
  %v1: u64 = field.read immediate
  %v2: u64 = field.read immediate
  register.write destination, %v2
instruction add64_reg
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
  %v42: u1 name=cf
  %v43: u64 name=lr
  %v44: u64 name=lo
  %v45: u64 name=all
  %v46: u64 name=notlr
  %v47: u64 name=ov
  %v48: u64 name=ovsign
  %v49: u1 name=of
  %v50: u64 name=afmix
  %v51: u64 name=afmask
  %v52: u64 name=afbit
  %v53: u1 name=af
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 0 }
  RegisterRead { output: ValueId(1), field: 1 }
  IntAddWrap { output: ValueId(2), left: ValueId(0), right: ValueId(1) }
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
  IntAddCarry { output: ValueId(42), left: ValueId(0), right: ValueId(1) }
  IntBinary { output: ValueId(43), left: ValueId(0), right: ValueId(1), op: Xor }
  IntBinary { output: ValueId(44), left: ValueId(0), right: ValueId(2), op: Xor }
  IntConstant { output: ValueId(45), value: 18446744073709551615 }
  IntBinary { output: ValueId(46), left: ValueId(43), right: ValueId(45), op: Xor }
  IntBinary { output: ValueId(47), left: ValueId(46), right: ValueId(44), op: And }
  IntBinary { output: ValueId(48), left: ValueId(47), right: ValueId(7), op: And }
  IntCompare { output: ValueId(49), left: ValueId(48), right: ValueId(7), predicate: Equal }
  IntBinary { output: ValueId(50), left: ValueId(43), right: ValueId(2), op: Xor }
  IntConstant { output: ValueId(51), value: 16 }
  IntBinary { output: ValueId(52), left: ValueId(50), right: ValueId(51), op: And }
  IntCompare { output: ValueId(53), left: ValueId(52), right: ValueId(51), predicate: Equal }
  FlagWrite { slot: 0, value: ValueId(42) }
  FlagWrite { slot: 4, value: ValueId(49) }
  FlagWrite { slot: 5, value: ValueId(53) }
  FlagWrite { slot: 11, value: ValueId(5) }
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
