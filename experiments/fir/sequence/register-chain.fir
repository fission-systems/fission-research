fir-sequence version=1 profile="register.branch.convert" base=0x1000 registers=3 flags=3 steps=3
input-sha256=3805c5efdfd4f7e35d5548b580716a918ba05935ee599767d3d9cab61ba31880
package-sha256=39c3146c31657708041b1e7cd4207876f3bb78c41c2fbf3106beec467f7154f1
step=0 address=0x1000 offset=0 length=4 raw=10a20000 body=0 name="choose" fields=[("source", 0), ("destination", 1), ("auxiliary", 2)]
evidence=[Evidence { source_id: "self-authored", url: "synthetic", revision: "v1", claim: "Integer conversion, ordered register/flag effects and acyclic join; no binary function lifting or GPU CFG claim." }]
step=1 address=0x1004 offset=4 length=4 raw=21a00000 body=0 name="choose" fields=[("source", 1), ("destination", 2), ("auxiliary", 0)]
evidence=[Evidence { source_id: "self-authored", url: "synthetic", revision: "v1", claim: "Integer conversion, ordered register/flag effects and acyclic join; no binary function lifting or GPU CFG claim." }]
step=2 address=0x1008 offset=8 length=4 raw=02a10000 body=0 name="choose" fields=[("source", 2), ("destination", 0), ("auxiliary", 1)]
evidence=[Evidence { source_id: "self-authored", url: "synthetic", revision: "v1", claim: "Integer conversion, ordered register/flag effects and acyclic join; no binary function lifting or GPU CFG claim." }]
body=0
instruction choose
  %v0: i8 name=input
  %v1: i32 name=wide
  %v2: u8 name=unsigned
  %v3: u64 name=zero_extended
  %v4: i32 name=zero
  %v5: u1 name=negative
  %v6: i32 name=negative_input
  %v7: i16 name=narrow
  %v8: i32 name=restored
  %v9: u1 name=one
  %v10: i32 name=positive_input
  %v11: i8 name=small
  %v12: i32 name=restored_positive
  %v13: u1 name=off
  %v14: i32 name=joined
  %v15: i32 name=observed
  %v16: u1 name=equal
  %v17: u1 name=flag
block 0 entry parameters=[]
  RegisterRead { output: ValueId(0), field: 0 }
  IntConvert { output: ValueId(1), input: ValueId(0), kind: SignExtend }
  RegisterRead { output: ValueId(2), field: 0 }
  IntConvert { output: ValueId(3), input: ValueId(2), kind: ZeroExtend }
  RegisterWrite { field: 2, value: ValueId(3) }
  IntConstant { output: ValueId(4), value: 0 }
  IntCompare { output: ValueId(5), left: ValueId(1), right: ValueId(4), predicate: SignedLess }
  CondBranch { condition: ValueId(5), on_true: FirEdge { target: 1, arguments: [ValueId(1)] }, on_false: FirEdge { target: 2, arguments: [ValueId(1)] } }
block 1 negative parameters=[ValueId(6)]
  IntConvert { output: ValueId(7), input: ValueId(6), kind: Truncate }
  IntConvert { output: ValueId(8), input: ValueId(7), kind: SignExtend }
  RegisterWrite { field: 1, value: ValueId(8) }
  IntConstant { output: ValueId(9), value: 1 }
  FlagWrite { slot: 0, value: ValueId(9) }
  Branch(FirEdge { target: 3, arguments: [ValueId(8)] })
block 2 positive parameters=[ValueId(10)]
  IntConvert { output: ValueId(11), input: ValueId(10), kind: Truncate }
  IntConvert { output: ValueId(12), input: ValueId(11), kind: SignExtend }
  RegisterWrite { field: 1, value: ValueId(12) }
  IntConstant { output: ValueId(13), value: 0 }
  FlagWrite { slot: 0, value: ValueId(13) }
  Branch(FirEdge { target: 3, arguments: [ValueId(12)] })
block 3 join parameters=[ValueId(14)]
  RegisterRead { output: ValueId(15), field: 1 }
  IntCompare { output: ValueId(16), left: ValueId(15), right: ValueId(14), predicate: Equal }
  FlagWrite { slot: 1, value: ValueId(16) }
  FlagRead { output: ValueId(17), slot: 0 }
  FlagWrite { slot: 2, value: ValueId(17) }
  Return
