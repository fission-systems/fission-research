instruction iadd encoding=Encoding { bits: 8, mask: 255, value: 96, fields: [] }
  %v0: i32 = vm.stack.pop
  %v1: i32 = vm.stack.pop
  %v2: i32 = int.add.wrap %v1, %v0
  vm.stack.push %v2
