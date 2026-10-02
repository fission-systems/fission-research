target triple = "amdgcn-amd-amdhsa"

define amdgpu_kernel void @wave_add_vector(ptr addrspace(1) %out) {
entry:
  %x = call i32 @llvm.amdgcn.workitem.id.x()
  %y = call i32 @llvm.amdgcn.workitem.id.y()
  %xy = add i32 %x, %y
  %index = zext i32 %x to i64
  %address = getelementptr i32, ptr addrspace(1) %out, i64 %index
  store i32 %xy, ptr addrspace(1) %address, align 4
  ret void
}

define amdgpu_kernel void @wave_add_scalar(ptr addrspace(1) %out, i32 %bias) {
entry:
  %x = call i32 @llvm.amdgcn.workitem.id.x()
  %sum = add i32 %x, %bias
  %index = zext i32 %x to i64
  %address = getelementptr i32, ptr addrspace(1) %out, i64 %index
  store i32 %sum, ptr addrspace(1) %address, align 4
  ret void
}

declare i32 @llvm.amdgcn.workitem.id.x()
declare i32 @llvm.amdgcn.workitem.id.y()
