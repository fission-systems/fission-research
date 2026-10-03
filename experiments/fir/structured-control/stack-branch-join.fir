instruction choose
  %v0: u32 name=input
  %v1: u32 name=limit
  %v2: u1 name=small
  %v3: u32 name=low_input
  %v4: u32 name=low_add
  %v5: u32 name=low_sum
  %v6: u32 name=high_input
  %v7: u32 name=high_add
  %v8: u32 name=high_sum
  %v9: u32 name=joined
block 0 entry parameters=[]
  VmStackPop { output: ValueId(0) }
  IntConstant { output: ValueId(1), value: 10 }
  IntCompare { output: ValueId(2), left: ValueId(0), right: ValueId(1), predicate: UnsignedLess }
  CondBranch { condition: ValueId(2), on_true: FirEdge { target: 1, arguments: [ValueId(0)] }, on_false: FirEdge { target: 2, arguments: [ValueId(0)] } }
block 1 low parameters=[ValueId(3)]
  IntConstant { output: ValueId(4), value: 1 }
  IntAddWrap { output: ValueId(5), left: ValueId(3), right: ValueId(4) }
  Branch(FirEdge { target: 3, arguments: [ValueId(5)] })
block 2 high parameters=[ValueId(6)]
  IntConstant { output: ValueId(7), value: 2 }
  IntAddWrap { output: ValueId(8), left: ValueId(6), right: ValueId(7) }
  Branch(FirEdge { target: 3, arguments: [ValueId(8)] })
block 3 join parameters=[ValueId(9)]
  VmStackPush { value: ValueId(9) }
  Return
