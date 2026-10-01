# GPU 바이너리·드라이버 연구 지도

## 연구 범위

GPU 분석은 하나의 instruction-set lifter가 아니다. 같은 애플리케이션 안에도 호스트 실행파일, 디바이스 코드 객체, 커널 ABI, 런타임 로더/JIT, Linux 커널 드라이버, 펌웨어, GPU 실행 상태가 함께 나타날 수 있다. 연구에서는 이 층을 분리해서 기록하고, 어떤 층 사이의 주장을 어떤 자료로 확인했는지 연결한다.

현재 프로젝트의 범위는 GPU 연산 코드, 그래픽 셰이더, 드라이버, 펌웨어까지 열어 둔다. 첫 실험은 분석 가능한 기준 도구가 있는 AMD GCN 계열의 작은 정적 샘플로 시작한다. 이는 최종 벤더 선택이나 범위 제한이 아니다.

## 산출물 종류

| 층 | 대표 산출물 | 우선 질문 |
|---|---|---|
| 호스트 컨테이너 | ELF, Mach-O, fat binary, fatbin section | 어떤 디바이스 이미지가 포함되고 어떤 target에 대응하는가? |
| 가상 디바이스 ISA | PTX, SPIR-V, HSAIL 등 | 버전·환경에 따라 의미가 어떻게 달라지는가? |
| 네이티브 디바이스 코드 | NVIDIA cubin/SASS, AMDGPU code object/ISA | opcode, 레지스터, wave 실행 의미를 어떻게 복원하는가? |
| 코드 객체 ABI | ELF notes/metadata, kernel descriptor, relocations | 인자 배치, wave 크기, 자원 사용, 로딩 제약은 무엇인가? |
| 사용자 공간 런타임 | compiler, assembler, JIT, loader, graphics/compute API | 가상 ISA가 언제 어떤 실제 코드로 변환되는가? |
| Linux 드라이버 | DRM, KFD, vendor kernel modules, ioctls | 메모리, 명령 큐, dispatch, 동기화가 어떻게 연결되는가? |
| 펌웨어·명령 프로세서 | GSP, MEC, command processor firmware, packet formats | 드라이버와 장치 사이의 실제 제어 경계는 어디인가? |

PTX나 SPIR-V 같은 입력을 SASS/AMDGPU ISA와 같은 층으로 취급하지 않는다. 또한 커널 instruction semantics만으로 dispatch, address-space mapping, barriers, host/device synchronization을 전부 설명할 수 있다고 가정하지 않는다.

## 관찰한 공개 자료와 환경

- NVIDIA CUDA 애플리케이션의 fatbin에는 PTX와 cubin이 함께 들어갈 수 있다. PTX는 driver JIT를 거쳐 실제 디바이스 코드가 될 수 있고, `cuobjdump`는 fatbin에서 PTX·SASS·ELF를 덤프하는 도구다.
- NVIDIA의 공개 Linux 커널 모듈은 전체 드라이버 스택이 아니다. 공개 저장소는 대응되는 GSP firmware 및 사용자 공간 구성 요소를 요구하며, `nvidia.ko`의 OS-agnostic 부분도 배포 바이너리로 제공되는 구성이 문서화돼 있다.
- Linux의 AMDGPU와 AMDKFD 코드는 GPU 메모리, 장치 스케줄링, 사용자 인터페이스, 펌웨어 연동을 추적할 수 있는 공개 기준 자료다. AMDGPU code object의 ISA target과 ABI/code-object version은 서로 다른 버전 축으로 기록해야 한다.
- [AMDGPU HIP/HSA source trace](amdgpu-runtime-trace.md)는 fat binary image selection부터 ROCr/HSAKMT의 `AMDKFD_IOC_CREATE_QUEUE`, KFD queue setup, ROCclr의 64-byte AQL dispatch packet/doorbell publish까지를 2026-09-29 source commits에 고정해 연결한다. 핵심 관찰은 queue-creation ioctl과 각 kernel dispatch가 서로 다른 경로라는 점이다.
- LLVM의 [AMDGPU backend guide](https://llvm.org/docs/AMDGPUUsage.html)는 code-object v3 이상에서 `NT_AMDGPU_METADATA` note payload가 MessagePack이라고 명시한다. `llvm-readobj`는 그 payload를 구조화된 YAML 비슷한 출력으로 보여주지만, 원본 파일은 YAML이 아니다.
- 이 개발 환경은 macOS arm64이고 실제 GPU 런타임은 확인되지 않았다. Homebrew LLVM 22.1.8에는 `amdgcn`, `nvptx`, `spirv` backend가 등록돼 있다. 따라서 지금은 정적 코드 객체·인코딩 연구가 가능하지만, 장치에서 실행한 차등 검증은 이 환경에서 수행하지 않는다.

## FSL/FIR에 필요한 분리

FSL/FIR의 GPU 경로는 아래 모델들을 합쳐 하나의 opcode 언어로 만들기보다, 버전이 연결된 여러 profile로 표현하는 편이 낫다.

1. **Container profile**: 파일/section/ELF note/metadata, embedded image, relocation, target 선택 규칙
2. **Virtual ISA profile**: PTX/SPIR-V 버전, 타입과 제어 흐름, virtual memory와 execution model
3. **Native ISA profile**: 비트 패턴, operand decode, scalar/vector execution, register classes, flags/predicate
4. **Kernel ABI profile**: argument layout, descriptors, resource metadata, entry point contract
5. **Parallel execution profile**: lane, wave/warp, active mask, divergence/reconvergence, barrier, memory scope/order
6. **Runtime/driver profile**: load/JIT/dispatch, command queue, synchronization, host/device memory effects
7. **Firmware boundary profile**: 공개 프로토콜 사실, 역추적 근거, 미확인 필드, 버전 범위

FIR instruction operation은 원본 인코딩과 ISA reference까지 provenance를 가져야 한다. 반면 드라이버가 큐에 넣는 packet의 효과는 kernel instruction 의미로 위장하지 않고 별도 runtime/command layer로 둔다. 미확인 동작은 `unknown` 또는 범위가 지정된 외부 효과로 남긴다.

## 단계별 연구

### A. 정적 기준선

- LLVM 22.1.8의 AMDGPU assembler/disassembler를 oracle로 사용해 GFX9 scalar, vector, barrier, end-program 인코딩을 확인했다.
- LLVM IR에서 작은 `amdgpu_kernel`을 컴파일해 AMDGPU ELF header, sections, symbols, note, kernel metadata를 inspect했다.
- 첫 code object에서 ELF HSA OSABI/ABI version, `gfx900` target flag, 272-byte kernarg segment, hidden launch arguments, wavefront size 64, VGPR/SGPR counts를 관찰했다. ELF ABI version, metadata schema version, target ISA는 별도 필드로 유지한다.
- PTX와 SPIR-V를 별도 언어 입력으로 두고, 같은 수학 연산이어도 실행 모델이 다르다는 점을 기록한다.

첫 실행 산출물은 [`experiments/gpu/amdgpu-gfx900/`](../experiments/gpu/amdgpu-gfx900/)에 있다. 이것은 소스에서 생성한 정적 샘플이며 GPU에서 실행한 결과가 아니다. [`tools/gpu_elf_probe.py`](../tools/gpu_elf_probe.py)는 ELF64 little-endian `EM_AMDGPU` 객체의 header, section table, symbol table, note record를 독립적으로 읽고, AMDGPU metadata MessagePack을 JSON으로 보존한다. 지금은 section relocations, extended section numbering, kernel descriptor binary layout, ISA instruction decoding은 구현하지 않았다.

### B. 코드 객체와 커널 ABI

- AMDGPU ELF code object의 OSABI, e_flags, notes, relocations, symbols, kernel descriptors를 schema화한다.
- LLVM/ROCm 버전, target ISA, ABI version, compiler flags, input hash를 각 산출물과 함께 기록한다.
- NVIDIA fatbin/cubin과 AMDGPU ELF를 공통 wrapper로 억지 합치지 않고 vendor-specific parser와 공통 provenance API를 분리한다.

### C. 명령어 의미와 검증

- 산술·벡터 연산에서 시작해 predicate, lane masks, branch, load/store, atomic, barrier 순으로 확장한다.
- 공식 ISA 문서와 LLVM MC table, disassembler를 각각 근거/관측 계층으로 유지한다.
- 비교 장치가 생기면 compiler-generated test kernels, ISA simulator/emulator, 실제 GPU execution 결과를 삼각 비교한다.
- “명령어를 디코드했다”, “각 lane의 효과를 표현했다”, “workgroup/runtime까지 동등하다”를 별도 성공 기준으로 둔다.

### D. Linux 드라이버·런타임 추적

- 완료한 AMD 첫 소스 추적은 공개 HIP/HSA, HSAKMT, Linux AMDKFD에서 image selection, code-object load, queue ioctl, AQL packet publish까지 연결한다. 실제 firmware/hardware handoff와 memory mapping은 실행 trace가 없어 아직 미확정이다.
- 같은 workload를 Mesa graphics stack과 ROCm/HSA compute stack에서 각각 추적해 공유되는 kernel driver interface와 다른 runtime paths를 분리한다.
- NVIDIA는 PTX JIT/finalization, kernel-module source boundary, user-space binary, GSP firmware 경계를 별도 case study로 추가한다.
- 각 경로에서 확인한 내용에 source commit, file/function, kernel/driver/firmware version, runtime trace provenance를 붙인다.

## 이번 프로토타입에서 확정하지 않는 것

- GFX900 sample은 현대 AMD GPU 전반을 대표하지 않는다.
- LLVM 22.1.8의 encoding/decoder는 강한 비교 기준이지만 자체적인 semantic proof는 아니다.
- 코드 객체의 구조를 읽는 것만으로 런타임 동작이나 GPU ISA 의미가 확정되지는 않는다.
- 공개 커널 드라이버 코드는 사용자 공간 compiler/JIT, firmware, hardware behavior 전체를 대체하지 않는다.
- 로컬 장치가 없어 현재 단계의 실제 GPU differential execution은 미수행이다.

## 다음 체크포인트

1. [완료] 독립 AQL packet parser와 합성 64-byte dispatch fixture를 만들었다. [runtime trace 문서](amdgpu-runtime-trace.md)와 `experiments/gpu/amdgpu-gfx900/` 참조.
2. [완료: 소스 추적] ROCclr의 loaded-symbol lookup → HSA kernel-object query → AQL `kernel_object` 대입 경로를 연결하고, code-object-v3 `.kd` descriptor와 정적 metadata provenance를 기록했다. [evidence sidecar](../experiments/gpu/amdgpu-gfx900/kernel-object-link.json) 참조. 런타임 포인터 주소와 packet 상관관계는 미관측이다.
3. 실제 AMDGPU Linux 장치에서 loaded-symbol 주소와 dispatch packet을 캡처해 code-object hash, descriptor, metadata와 상관 분석한다.
4. [완료: 4-pattern vertical slice] FSL/TOML 원문을 컴파일된 profile로 만들고 scalar move, vector add, barrier, end-program을 데이터 기반으로 디코드했다. 이전 form-switch 디코더와 네 decode record가 같음을 대조했다. [FSL compiler note](fsl-first-compiler-slice.md)와 [decoder note](gfx9-decoder-first-slice.md) 참조.
5. 확장 워드와 branch target을 package schema로 표현하고, bitfield 조합·상대 주소 계산을 포함해 FSL primitive 범위를 넓힌다.
6. ELF relocation, extended section numbering, descriptor layout을 schema화하고 code-object version 차이를 추가한다.
7. ROCm compute와 Mesa graphics, KFD scheduler/hardware 세대별 차이를 분리해 조사한다.
