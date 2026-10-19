x86 program mode=64 base=0x401000 bytes=20 decoder=owned-x86-v2 input-sha256=16e4581644db155085baad2a2a65be059bafe18d9b05b31845e0ffa1a8fbf6f5 package-sha256=4f21befdc46ff60cb74913f0e2dea88b770cc1edbcb414590c99a72b90a67470
binary file-sha256=adaac705a84dfef0c172814a72b81a9bc6a9cdbd9f2d320827838d56d8df05ef file-offset=4096 section=.text
instance address=0x401000 offset=0 length=3 raw=4889f0 code="mov_rm_reg" body=mov64_reg fields=[("destination", 0), ("source", 6), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x401003 offset=3 length=3 raw=4885ff code="test_rm_reg" body=test64_reg fields=[("destination", 7), ("source", 7), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x401006 offset=6 length=2 raw=7407 code="je_short" body=je fields=[("destination", 0), ("source", 0), ("base", 0), ("index", 0), ("immediate", 4198415), ("scale", 0)]
instance address=0x401008 offset=8 length=3 raw=4831f8 code="xor_rm_reg" body=xor64_reg fields=[("destination", 0), ("source", 7), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x40100b offset=11 length=3 raw=4801d0 code="add_rm_reg" body=add64_reg fields=[("destination", 0), ("source", 2), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x40100e offset=14 length=1 raw=c3 code="ret" body=ret64 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instance address=0x40100f offset=15 length=4 raw=4883c007 code="add_rm_simm8" body=add64_imm fields=[("destination", 0), ("source", 0), ("base", 0), ("index", 0), ("immediate", 7), ("scale", 0)]
instance address=0x401013 offset=19 length=1 raw=c3 code="ret" body=ret64 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
instruction mov64_reg encoding=Encoding { bits: 128, mask: 340277174624079928635746076935438991360, value: 212884171199927932769750349498023936, fields: [BitField { name: "destination", offset: 0, bits: 5, excluded: [] }, BitField { name: "source", offset: 5, bits: 5, excluded: [] }, BitField { name: "base", offset: 10, bits: 5, excluded: [] }, BitField { name: "index", offset: 15, bits: 5, excluded: [] }, BitField { name: "immediate", offset: 20, bits: 64, excluded: [] }, BitField { name: "scale", offset: 84, bits: 2, excluded: [] }] }
  %v0: u64 = register.read destination
  %v1: u64 = register.read source
  register.write destination, %v1
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
instruction add64_imm
  %v0: u64 name=lhs
  %v1: u64 name=imm64
  %v2: u64 name=rhs
  %v3: u64 name=result
  %v4: u64 name=zero
  %v5: u1 name=off
  %v6: u1 name=on
  %v7: u1 name=zf
  %v8: u64 name=sign
  %v9: u64 name=signbit
  %v10: u1 name=sf
  %v11: u64 name=p_mask0
  %v12: u64 name=p_bit0
  %v13: u1 name=p0
  %v14: u64 name=p_mask1
  %v15: u64 name=p_bit1
  %v16: u1 name=p1
  %v17: u64 name=p_mask2
  %v18: u64 name=p_bit2
  %v19: u1 name=p2
  %v20: u64 name=p_mask3
  %v21: u64 name=p_bit3
  %v22: u1 name=p3
  %v23: u64 name=p_mask4
  %v24: u64 name=p_bit4
  %v25: u1 name=p4
  %v26: u64 name=p_mask5
  %v27: u64 name=p_bit5
  %v28: u1 name=p5
  %v29: u64 name=p_mask6
  %v30: u64 name=p_bit6
  %v31: u1 name=p6
  %v32: u64 name=p_mask7
  %v33: u64 name=p_bit7
  %v34: u1 name=p7
  %v35: u1 name=parity1
  %v36: u1 name=parity2
  %v37: u1 name=parity3
  %v38: u1 name=parity4
  %v39: u1 name=parity5
  %v40: u1 name=parity6
  %v41: u1 name=parity7
  %v42: u1 name=pf
  %v43: u1 name=cf
  %v44: u64 name=lr
  %v45: u64 name=lo
  %v46: u64 name=all
  %v47: u64 name=notlr
  %v48: u64 name=ov
  %v49: u64 name=ovsign
  %v50: u1 name=of
  %v51: u64 name=afmix
  %v52: u64 name=afmask
  %v53: u64 name=afbit
  %v54: u1 name=af
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 0 }
  FieldRead { output: ValueId(1), field: 4 }
  FieldRead { output: ValueId(2), field: 4 }
  IntAddWrap { output: ValueId(3), left: ValueId(0), right: ValueId(2) }
  IntConstant { output: ValueId(4), value: 0 }
  IntConstant { output: ValueId(5), value: 0 }
  IntConstant { output: ValueId(6), value: 1 }
  IntCompare { output: ValueId(7), left: ValueId(3), right: ValueId(4), predicate: Equal }
  IntConstant { output: ValueId(8), value: 9223372036854775808 }
  IntBinary { output: ValueId(9), left: ValueId(3), right: ValueId(8), op: And }
  IntCompare { output: ValueId(10), left: ValueId(9), right: ValueId(8), predicate: Equal }
  IntConstant { output: ValueId(11), value: 1 }
  IntBinary { output: ValueId(12), left: ValueId(3), right: ValueId(11), op: And }
  IntCompare { output: ValueId(13), left: ValueId(12), right: ValueId(11), predicate: Equal }
  IntConstant { output: ValueId(14), value: 2 }
  IntBinary { output: ValueId(15), left: ValueId(3), right: ValueId(14), op: And }
  IntCompare { output: ValueId(16), left: ValueId(15), right: ValueId(14), predicate: Equal }
  IntConstant { output: ValueId(17), value: 4 }
  IntBinary { output: ValueId(18), left: ValueId(3), right: ValueId(17), op: And }
  IntCompare { output: ValueId(19), left: ValueId(18), right: ValueId(17), predicate: Equal }
  IntConstant { output: ValueId(20), value: 8 }
  IntBinary { output: ValueId(21), left: ValueId(3), right: ValueId(20), op: And }
  IntCompare { output: ValueId(22), left: ValueId(21), right: ValueId(20), predicate: Equal }
  IntConstant { output: ValueId(23), value: 16 }
  IntBinary { output: ValueId(24), left: ValueId(3), right: ValueId(23), op: And }
  IntCompare { output: ValueId(25), left: ValueId(24), right: ValueId(23), predicate: Equal }
  IntConstant { output: ValueId(26), value: 32 }
  IntBinary { output: ValueId(27), left: ValueId(3), right: ValueId(26), op: And }
  IntCompare { output: ValueId(28), left: ValueId(27), right: ValueId(26), predicate: Equal }
  IntConstant { output: ValueId(29), value: 64 }
  IntBinary { output: ValueId(30), left: ValueId(3), right: ValueId(29), op: And }
  IntCompare { output: ValueId(31), left: ValueId(30), right: ValueId(29), predicate: Equal }
  IntConstant { output: ValueId(32), value: 128 }
  IntBinary { output: ValueId(33), left: ValueId(3), right: ValueId(32), op: And }
  IntCompare { output: ValueId(34), left: ValueId(33), right: ValueId(32), predicate: Equal }
  IntBinary { output: ValueId(35), left: ValueId(13), right: ValueId(16), op: Xor }
  IntBinary { output: ValueId(36), left: ValueId(35), right: ValueId(19), op: Xor }
  IntBinary { output: ValueId(37), left: ValueId(36), right: ValueId(22), op: Xor }
  IntBinary { output: ValueId(38), left: ValueId(37), right: ValueId(25), op: Xor }
  IntBinary { output: ValueId(39), left: ValueId(38), right: ValueId(28), op: Xor }
  IntBinary { output: ValueId(40), left: ValueId(39), right: ValueId(31), op: Xor }
  IntBinary { output: ValueId(41), left: ValueId(40), right: ValueId(34), op: Xor }
  IntCompare { output: ValueId(42), left: ValueId(41), right: ValueId(5), predicate: Equal }
  IntAddCarry { output: ValueId(43), left: ValueId(0), right: ValueId(2) }
  IntBinary { output: ValueId(44), left: ValueId(0), right: ValueId(2), op: Xor }
  IntBinary { output: ValueId(45), left: ValueId(0), right: ValueId(3), op: Xor }
  IntConstant { output: ValueId(46), value: 18446744073709551615 }
  IntBinary { output: ValueId(47), left: ValueId(44), right: ValueId(46), op: Xor }
  IntBinary { output: ValueId(48), left: ValueId(47), right: ValueId(45), op: And }
  IntBinary { output: ValueId(49), left: ValueId(48), right: ValueId(8), op: And }
  IntCompare { output: ValueId(50), left: ValueId(49), right: ValueId(8), predicate: Equal }
  IntBinary { output: ValueId(51), left: ValueId(44), right: ValueId(3), op: Xor }
  IntConstant { output: ValueId(52), value: 16 }
  IntBinary { output: ValueId(53), left: ValueId(51), right: ValueId(52), op: And }
  IntCompare { output: ValueId(54), left: ValueId(53), right: ValueId(52), predicate: Equal }
  FlagWrite { slot: 0, value: ValueId(43) }
  FlagWrite { slot: 4, value: ValueId(50) }
  FlagWrite { slot: 5, value: ValueId(54) }
  FlagWrite { slot: 11, value: ValueId(6) }
  FlagWrite { slot: 1, value: ValueId(42) }
  FlagWrite { slot: 2, value: ValueId(7) }
  FlagWrite { slot: 3, value: ValueId(10) }
  FlagWrite { slot: 6, value: ValueId(6) }
  FlagWrite { slot: 7, value: ValueId(6) }
  FlagWrite { slot: 8, value: ValueId(6) }
  FlagWrite { slot: 9, value: ValueId(6) }
  FlagWrite { slot: 10, value: ValueId(6) }
  RegisterWrite { field: 0, value: ValueId(3) }
  Return
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
instruction test64_reg
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
  IntBinary { output: ValueId(2), left: ValueId(0), right: ValueId(1), op: And }
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
instruction je
  %v0: u1 name=zf
  %v1: u1 name=take
  %v2: u1 name=match
  %v3: u64 name=target
block 0 entry parameters=[]
  FlagRead { output: ValueId(0), slot: 2 }
  IntConstant { output: ValueId(1), value: 1 }
  IntCompare { output: ValueId(2), left: ValueId(0), right: ValueId(1), predicate: Equal }
  CondBranch { condition: ValueId(2), on_true: FirEdge { target: 1, arguments: [] }, on_false: FirEdge { target: 2, arguments: [] } }
block 1 taken parameters=[]
  FieldRead { output: ValueId(3), field: 4 }
  GuestNextPcWrite { value: ValueId(3) }
  Return
block 2 fallthrough parameters=[]
  Return
