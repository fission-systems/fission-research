/* Test-only Linux i386 adapter; no libc. Original instruction bytes are supplied separately. */
.section .bss
.align 4
packet: .skip 8
output: .skip 16
.section .text
.globl _start
_start:
    xorl %edi,%edi
read_more:
    movl $3,%eax
    xorl %ebx,%ebx
    leal packet(%edi),%ecx
    movl $8,%edx
    subl %edi,%edx
    int $0x80
    testl %eax,%eax
    js fail
    jz eof
    addl %eax,%edi
    cmpl $8,%edi
    jne read_more
    pushl packet+4
    pushl packet
    pushl $2
    popfl
    movl $0x11223344,%ebp
    movl %esp,output+12
    call oracle_code
    pushfl
    popl %edx
    movl %eax,output
    movl %edx,output+4
    movl %ebp,output+8
    movl %esp,%ecx
    subl output+12,%ecx
    movl %ecx,output+12
    addl $8,%esp
    xorl %edi,%edi
write_more:
    movl $4,%eax
    movl $1,%ebx
    leal output(%edi),%ecx
    movl $16,%edx
    subl %edi,%edx
    int $0x80
    testl %eax,%eax
    jle fail
    addl %eax,%edi
    cmpl $16,%edi
    jne write_more
    jmp _start
eof:
    testl %edi,%edi
    jnz fail
    xorl %ebx,%ebx
    jmp exit
fail:
    movl $3,%ebx
exit:
    movl $1,%eax
    int $0x80
.section .note.GNU-stack,"",@progbits
