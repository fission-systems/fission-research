target triple = "amdgcn-amd-amdhsa"

define amdgpu_kernel void @add(ptr addrspace(1) %out, i32 %a, i32 %b) {
entry:
  %sum = add i32 %a, %b
  store i32 %sum, ptr addrspace(1) %out, align 4
  ret void
}
