# 단일 FIR의 CUDA C++ / PTX 출력

2026-10-03 첫 출력 실험. 기존 stack FIR을 GPU reference 커널로 투영한다.
입력 GPU 바이너리의 디컴파일·ABI 복원이나 하드웨어 실행을 수행한 실험은 아니다.

## 의미 소유권과 범위

- Rust `fission-fsl`의 동일 `CompiledInstruction` / `FirOp`를 C, Rust, CUDA C++, PTX가 소비한다. 출력용 별도 의미 IR은 없다.
- stack pop/push, wrapping add, 1..64-bit signed/unsigned bit-vector 타입을 지원한다.
- stack capacity와 required input/peak growth는 기존 `StackContract`에서 구한다.
- GPU register/flag/lane 효과, 128-bit 값, unsupported body와 malformed SSA는 출력 전에 거부한다. GPU 상태를 임의로 stack 연산으로 바꾸지 않는다.
- `jvm-iadd.fsl`은 기존 JVM fixture의 복사본이다. JVM 전체 실행이나 CUDA로 작성된 원본 커널 복원을 뜻하지 않는다.

## Reference kernel ABI v1

| 인자 | 표현 / 전제 |
|---|---|
| `stack_ptr` | 유효 global allocation의 8-byte bit-vector slots; capacity 전체를 수용 |
| `depth_ptr` | 8-byte unsigned depth, 자연 정렬 |
| `capacity` | unsigned 64-bit slot 수; allocation 범위와 주소 산술이 유효 |
| `status_ptr` | 4-byte unsigned status, 자연 정렬 |

버퍼는 서로 겹치지 않아야 한다. block/thread 좌표의 x/y/z가 모두 0인 thread만 상태를 처리한다. 다른 thread와 null status는 global memory를 접근하지 않는다. status가 유효할 때 null stack/depth는 3을 쓴다. 실패한 preflight는 stack/depth를 보존하며 status만 기록한다. 한 상태는 동시에 여러 launch에서 처리하지 않는다. 호스트는 커널 완료를 기다린 뒤 결과를 읽는다.

성공 0, underflow 1, capacity 2, invalid state 3은 기존 reference 상태 계약을 따른다. signed 값도 bit pattern으로 저장하며 pop 시 폭을 자르고 덧셈은 해당 폭에서 wrap한다. pop한 backing slot은 뒤의 ordered push가 쓰기 전까지 보존한다. 이 ABI는 우리가 정의한 reference wrapper 계약이다.

## 검증 경로

1. 각 FSL → portable package → 동일 FIR → CUDA/PTX 출력.
2. 5 widths × 2 signs × 4 bodies(add/duplicate/ordered pop-push/pop-only), JVM fixture 1개 = **41 profiles**.
3. 직접 생성한 PTX를 제한된 scalar reference로 실행하고, 별도 정수/상태 oracle과 **3,444개 상태**를 비교한다. 전체 backing slots, depth, status와 실패/non-owner 접근 trace를 확인한다.
4. CUDA 소스를 Clang NVPTX로 O0/O2에서 **82회 device compile**한다.
5. Linux에서는 직접 PTX 41개와 Clang PTX 82개를 NVIDIA ptxas로 assemble하고 ELF cubin 출력을 확인한다. 이것은 compilation/assembly 증거다.
6. 4 unsupported source cases × 2 GPU targets = **8개 semantic refusal**. 기존 C/Rust recompilation gates는 native crate tests에서 별도로 재실행한다.

[`ptx_reference.py`](../../../tools/ptx_reference.py)는 PTX 7.0/sm_70의 이 출력에서 쓰는 작은 scalar subset만 해석한다. 주소는 인공적인 flat global mapping이며 `cvta`는 identity로 가정한다. unknown opcode/arity, label, register, unmapped address는 실패한다. NVIDIA GPU emulator, independent ISA proof, warp scheduler, fault/atomic/memory consistency model이 아니다.

## 재현

```sh
python3 tools/gpu_projection_validate.py \
  --fslc /path/to/Fission/target/debug/fslc --clang clang-18

# Linux x86_64: pinned assembler와 포함 license hash를 확인하고 복원
python3 tools/gpu_projection_toolchain.py
python3 tools/gpu_projection_validate.py \
  --fslc /path/to/Fission/target/debug/fslc --clang clang-18 \
  --ptxas .cuda-toolchain/ptxas
```

macOS 로컬 검증은 Homebrew Clang 22.1.8을 사용했다. NVIDIA ptxas의 Linux binary는 로컬에서 실행하지 않았다. CI는 Clang 18과 pinned ptxas 12.8.93을 사용한다. toolchain lock은 wheel/실행 파일/license 해시를 포함한다. NVIDIA 도구를 production runtime에 연결하지 않는다.

`jvm-iadd.fir`, `.cu`, `.ptx`는 정확히 재생성해 비교하고, package SHA도 lock으로 검증한다. 도구 버전에 따라 달라질 수 있는 Clang PTX와 cubin의 바이너리 hash는 artifact 동치 기준으로 삼지 않는다. 보고서는 `artifacts/gpu-projection.json`에 기록하며 실패 시 이전 성공을 덮어쓴다.

공식 형식 근거는 [PTX ISA](https://docs.nvidia.com/cuda/parallel-thread-execution/index.html), [CUDA Binary Utilities](https://docs.nvidia.com/cuda/cuda-binary-utilities/index.html)다. `.entry`, `.param`, integer wrapping, global loads/stores와 thread/block special registers를 출력에 사용한다. 실제 GPU 바이너리에서 kernel body/ABI를 복원하거나 병렬 메모리 의미를 지원하는 것은 후속 연구다.
