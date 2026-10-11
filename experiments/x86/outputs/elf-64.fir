x86 program mode=64 base=0x401000 bytes=5 decoder=owned-x86-v1 input-sha256=d9cf89c572e9a193175b8735a341790208fabfe36d704868ed206cb6a85af1ba package-sha256=0423223eaf7238013177aceb9b7c09f7448a682752668e3124ab9c651b46515a
binary file-sha256=588d20aa4045b9e6694a8d39931f0bbf10881bfcf1b0090a4b3830ba2704184f file-offset=4096 section=.text
instance address=0x401000 offset=0 length=4 raw=488d0437 code="lea" body=lea64_a64 fields=[("destination", 0), ("source", 0), ("base", 7), ("index", 6), ("immediate", 0), ("scale", 0)]
instance address=0x401004 offset=4 length=1 raw=c3 code="ret" body=ret64 fields=[("destination", 4), ("source", 0), ("base", 0), ("index", 0), ("immediate", 0), ("scale", 0)]
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
