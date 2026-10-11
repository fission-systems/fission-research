# Fission FSL/FIR 연구 — AI 작업 이관

> 아래는 2026-10-05 스냅샷이다. 2026-10-11의 자체 x86 디코드·FIR 출력과 현재 한계는
> [x86 연구 기록](../experiments/x86/README.md)과 [research-status](research-status.md)를 먼저 읽는다.
> 외부 instruction decoder 의존성 없이 진행한다. Branch/dirty 상태는 시작 시 다시 확인한다.

작성·상태 확인: **2026-10-05, Asia/Seoul**.
이 문서는 다음 AI가 대화 전체를 읽지 않고 연구를 이어가기 위한 작업 계약이다.
구현 범위는 저장소 소스와 기존 검증 기록으로 확인했다. 이번 이관 작업에서는
테스트를 재실행하지 않았으며, 아래 수치는 2026-10-04의 기록이다.

## 1. 목적과 이미 합의한 결정

장기 목표는 Fission의 SLEIGH/SLA 및 P-code 의존을 자체 FSL/FIR로 대체하고,
정확한 의미 복구·분석·행동 보존 재컴파일을 지원하는 것이다.
CPU, GPU, JVM, Python 등으로 확장할 수 있지만 현재는 제한된 연구 구현이다.
최종적으로 Fission에 통합할 계획이며, 아직 제품 디컴파일러 전체를 대체하지 않았다.

- **정확성과 재컴파일이 가독성보다 우선**한다.
- **하나의 FIR이 의미를 소유**한다. NIR/HIR로 다시 분리하거나 P-code를 필수 경유하지 않는다.
- C, Rust, CUDA C++, PTX, 분석 그래프 등은 같은 FIR을 소비하는 출력 계층이다.
  출력 계층에 명령 의미의 별도 구현을 숨기지 않는다.
- FSL 텍스트를 오프라인에서 검증·컴파일하여 이식 가능한 `.fslc`로 만든다.
  장기 실행 코드 모델은 AOT 우선, 선택적 JIT, 정확성 기준 인터프리터다.
- JSON은 보고서·디버그 덤프 등에 사용한다. 네이티브 패키지 형식은 바이너리다.
  옛 JSON 실험 artifact는 역사적 재현 대상으로 남아 있다.
- 명세·의미·원본 자료·검증 상태를 provenance로 연결한다.
- 미지원 의미는 명시적으로 거부한다. no-op이나 추측으로 성공시키지 않는다.

사용자는 실험 브랜치에서 기존 Fission 아키텍처 변경까지 허용했다.
이것은 전체 교체가 끝났다는 뜻이나 검증 없이 범위를 확대하라는 뜻은 아니다.

## 2. 저장소, 브랜치, 기준 커밋

| 역할 | 로컬 경로 | 작업 브랜치 | 확인한 HEAD |
|---|---|---|---|
| 연구 자료·명세·golden·재현·CI | `/Users/sjkim1127/Documents/ChatGPT/fission-research` | `main` | `59f0679b3bbd569addc3f34a9ee7f9242dfdb159` |
| 네이티브 컴파일러·FIR 실행·출력 | `/Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity` | `codex/fsl-jvm-iadd-parity` | `16f84f47e0cb53278fddde2522dfbe581fce5ddf` |
| 옛 자산 비교 입력 | 연구 저장소의 `Fission/` | detached, 비교용 | `96fc71f75cecdee305faf9497561c577a8955468` |

확인 시 두 작업 저장소는 모두 clean이었고 origin과 일치했다.
이 문서 추가 전의 스냅샷이며, 다음 AI는 시작할 때 다시 확인해야 한다.

**작업 제약:**

- 연구 저장소는 사용자 지시에 따라 `main`에 커밋·푸시한다.
- 네이티브 Fission은 반드시 `codex/fsl-jvm-iadd-parity`에서 작업한다.
  **제품 `main`에는 커밋·푸시하지 않는다.**
- 기존 [PR #176 — FSL/FIR 실험지원](https://github.com/fission-systems/Fission/pull/176)을 계속 사용한다.
  확인 시 OPEN, draft 아님, base `main`. 병합은 사용자가 나중에 결정한다.
- 연구 저장소 안의 `Fission/`은 고정 비교 입력이다. 네이티브 작업 대상으로 혼동하지 않는다.
- `Vendor/`는 NVIDIA/AMD/Intel 참고 구현 및 자료다. 제품 런타임·빌드 의존성으로 연결하지 않는다.
- 변경 전 관련 `AGENTS.md`를 읽고, 기존 변경과 canonical owner를 보존한다.

현재 커밋의 원격 CI는 이번 이관 시 직접 확인했다.

- [Fission CI: success](https://github.com/fission-systems/Fission/actions/runs/37192748459), native `16f84f47e`.
- [연구 CI: success](https://github.com/fission-systems/fission-research/actions/runs/37192863901), research `59f0679b`.

## 3. 현재 가장 최근에 끝난 실행 단위

**여러 명령의 상태·origin 계약을 연결하는 `FirSequence`**가 구현됐다.
이것은 사용자가 다음 단계로 요청했던 범위다. 실제 함수 lifting은 아직 아니다.

### 의미 소유 및 상태 전달

- 하나의 불변 `.fslc` 패키지가 canonical FIR body들을 소유한다.
- 명령 instance는 body를 복제하거나 평탄화하지 않고 instruction index로 참조한다.
- instance마다 address, input offset, byte length를 기록하고 원본 바이트·decode field를 유지한다.
- 입력 창과 컴파일된 패키지를 각각 SHA-256으로 연결한다.
- 각 body 호출의 로컬 SSA 값은 새로 생성된다.
- 순서 있는 register/flag 상태는 다음 instance로 전달된다.
- `s_add_u32 → s_addc_u32`에서 SCC carry 전달과, 여러 body의 이전 register 쓰기 읽기를 확인했다.

### 실행 계약과 제한

- 하나의 명시적 profile, 고정 길이 명령, 완전한 입력 창만 허용한다.
- 입력은 1~4,096개 명령, 각 register/flag bank는 최대 4,096 logical slot이다.
- 전체 창의 decode·의미 admission·모든 구문 경로의 bank index를 실행 전에 검사한다.
- 현재 sequence 실행은 acyclic scalar register/flag body, 1~64-bit 연산에 한정된다.
- 실제 bank 길이는 계약과 정확히 같아야 하고 flag 값은 0 또는 1이어야 한다.
- 임시 상태에서 실행한 뒤 전체 성공 시 commit한다. 실패 시 원래 상태를 보존한다.
  이것은 wrapper의 트랜잭션이며, 게스트 fault 순서나 CPU 동시 실행 atomicity 모델은 아니다.
- body 내부 branch/return은 해당 명령의 의미 구현 제어 흐름이다.
  body가 끝나면 다음 입력 word를 실행한다. **게스트 분기·PC 변경·함수 return을 의미하지 않는다.**
- sequence 출력은 FIR diagnostic, C, Rust다. CUDA/PTX 및 sequence native JIT/AOT는 미지원이다.
- C 출력 호출자는 유효한 서로 겹치지 않는 배열을 제공해야 한다.
  빈 bank에도 nonnull dummy storage를 제공한다.

### 바이너리 envelope

`.fslseq` v1은 96-byte little-endian header 뒤에 `.fslc`와 정확한 입력 창을 넣는다.
magic은 `FSLSEQ\0\x01`이다. header에는 base address, bank 크기, payload 길이,
package SHA-256, input SHA-256이 있다.
로드 시 길이·EOF·hash를 확인하고 패키지를 다시 decode/compose하여 선택과 origin을 재구성한다.

입력 창 hash는 전체 파일 hash가 아니다. package hash는 원본 `.fsl` 텍스트 hash가 아니다.
base address와 bank 크기는 호출자가 제공한 계약이며, hash만으로 진위가 입증되지 않는다.
ELF file-offset/virtual-address 매핑, relocation, 함수 entry, ABI allocator는 여기서 복구하지 않는다.

## 4. 구현 위치와 읽을 순서

네이티브 owner는 Fission의 **`crates/fission-fsl`**이다.
연구 저장소의 Python 도구는 재현·자료 이관용이며 제품 컴파일러의 대체 owner가 아니다.

| 네이티브 경로 | 역할 |
|---|---|
| `src/lib.rs`, `src/parser.rs` | FSL compile 진입점과 문법 |
| `src/package.rs`, `src/encoding.rs` | versioned `.fslc`, 명령 패턴·필드 decode/encode |
| `src/semantics.rs` | 단일 FIR의 operation/type/SSA 계약 |
| `src/control.rs` | 같은 FIR 안의 block, 인자, 비교, 변환, branch/join |
| `src/state.rs` | register/flag 상태, carry, admission 및 bank preflight |
| `src/sequence.rs` | `FirSequence`, origin, state contract, `.fslseq`, 실행·출력 |
| `src/wave.rs` | 제한된 wave/lane 의미 |
| `src/output.rs`, `src/gpu_output.rs` | FIR 출력 계층 |
| `src/jit.rs` | 제한된 기존 decode/lift용 Cranelift 경로 |
| `src/registers.rs`, `src/abi.rs` | 자체 register layout와 ABI metadata |
| `src/library.rs` | 자체 prototype 후보 데이터베이스 |
| `src/main.rs` | `fslc` CLI |
| `tests/sequence.rs` | 최신 sequence 계약 검사 5개 |

`FirSequence` 주요 API는 `compose`, `execute`, `encode_binary`, `decode_binary`, `emit`이다.
주요 공개 타입은 `SequenceStateContract`, `InstructionOrigin`, `FirInstructionInstance`다.
내부 상태는 private이며 구성 후 외부에서 instance를 임의 수정하지 않는다.

먼저 읽을 문서:

1. 연구 `docs/research-status.md` — 단계별 관찰과 한계. 옛 섹션은 당시 상태다.
2. 연구 `experiments/fir/sequence/README.md` 및 `sequence.lock.toml`.
3. 네이티브 `docs/research/fir-sequence-state-origin.md` — 현재 계약의 상세 설명.
4. 네이티브 `docs/research/fir-integer-conversion-register-cfg.md` — 직전 단계.
5. 연구 `docs/fir-semantic-contract.md`, `docs/owned-assets-and-structured-fir.md`.
6. 네이티브 `docs/adr/0015-fsl-single-fir-recompilation.md`.
7. 연구 `docs/reproduction.md`, `.github/workflows/reproduce.yml`.

## 5. 이미 존재하는 기반과 아직 미지원인 것

### 단일 FIR

`CompiledInstruction`에 values/ops와 block ranges가 함께 있다.
typed constant, 비교, block 인자, branch/conditional branch/join, 명시적 정수 확장·절단,
register/flag 읽기·쓰기와 carry가 구현돼 있다.
block 간 값은 명시적 인자로 전달하며, 암묵적으로 이전 block의 SSA 값을 캡처하지 않는다.
IR 타입 표현 범위와 실행 가능한 폭은 다르다. 현재 scalar reference 실행은 1~64-bit다.
loop는 표현될 수 있어도 현재 실행 admission은 거부한다.
구조 FIR의 stack/register 지원을 wave/CUDA/PTX/JIT 지원으로 확대해서 설명하면 안 된다.

### 자체 자산 형식

| 형식 | 현재 역할 |
|---|---|
| `.fsl` → `.fslc` | 텍스트 명세 → 검증된 네이티브 패키지 |
| `.fslregs` | byte layout, register view/overlap metadata 및 제한된 binding |
| `.fslabi` | 자체 calling metadata, 제한된 linking |
| `.fslib` → `.fsldb` | prototype 후보 corpus와 정확한 query |
| `.fslseq` | body pool과 입력 창을 묶은 순차 instance 실행 계약 |

`.fslc`는 기능별 v1~v7이 존재한다. v6은 구조 제어 흐름, v7은 엄격한 정수 변환을 추가했다.
새 기능 때문에 과거 패키지의 최소 버전·바이트·golden을 무조건 바꾸지 않는다.
sequence는 별도 envelope이며 기존 `.fslc` 형식을 바꾸지 않았다.

### 아키텍처·이관 실험 범위

- GFX900: SOP2 32개 패턴의 명세 중심 확장과 LLVM encoding 비교가 있다.
  패턴 coverage와 실행 의미 coverage는 서로 다르다.
- GPU scalar 실행: `s_add_u32`, `s_addc_u32`, SGPR/SCC의 제한된 profile.
- wave64: EXEC mask 읽기, `v_add_u32`의 VGPR 입력·SGPR broadcast,
  활성 lane 쓰기·비활성 lane 보존. EXEC 쓰기, divergence, memory, barrier,
  전체 kernel ABI 및 GPU 하드웨어 실행 검증은 없다.
- GPU ELF의 실제 컴파일된 일부 명령 행을 확인했다.
  합성 상태 실행을 결합한 것이며 전체 kernel 실행·함수 lifting 증거는 아니다.
- JVM은 `iadd` slice다. 전체 method/class/VM 의미는 아니다.
- SLEIGH/SLA 직접 이관은 선택한 eBPF leaf의 symbol/template 등으로 제한된다.
  일반 context, dynamic handle, control/memory 의미의 일괄 이관은 미완료다.
- SLA/cspec/pspec/ldefs/FPK 등 988개 자산 inventory가 있다. 전체 교체 완료가 아니다.
- 한 C64 FPK corpus의 31,418 후보·15,455 parameter 이관 및 query가 있다.
  unresolved type/unknown variadic을 보존하며 제품 signature loader·calling ABI 대체는 아니다.
- 제한된 FIR의 CUDA C++/PTX 출력과 device compile/assembly 검사가 있다.
  SASS backend나 GPU hardware 실행을 증명하지 않는다.
- 기존 Cranelift 경로는 일부 decode-and-lift host code용이다.
  일반 게스트 프로그램 실행 JIT나 전체 structured/state/wave backend가 아니다.

**제품 디컴파일러의 기존 경로는 여전히 존재한다.** 실험 crate의 성공을 제품 전체
SLEIGH/P-code 제거, 전체 함수 동치, GPU kernel 재컴파일 성공으로 보고하지 않는다.

## 6. 최신 검증 증거와 재현

원본 기록: 연구 `experiments/fir/sequence/validation-2026-10-04.json`.

| 2026-10-04 기록 | 관찰 범위 |
|---|---|
| native 53개 검사 통과 | crate 전체, serial nextest, skipped/leaky 0 |
| Python 27개 검사 통과 | 연구 도구 검사 |
| reference/u128 1,060 상태 | 두 명령 산술 oracle 비교 |
| C/Rust O0/O2 6,324 비교 | scalar 5,280 + register CFG 1,036 + 빈 bank 8 |
| 재현 CLI 112 상태·실패 4개 | 두 envelope, 6개 출력, hash/byte 계약 |
| fmt·Clippy 통과 | warnings denied |

32-bit 외 scalar 폭과 big-endian 운송 검사는 합성 primitive/format 검사다.
추가 GPU ISA 지원이나 GPU 실행 oracle로 설명하지 않는다.
기존 구조·변환·역사적·SLA·layout·ABI·library artifact의 재현도 기록됐다.
이 수치들을 이전 단계 수치와 단순 합산하여 독립 입력 수나 전체 정확도처럼 보고하지 않는다.

### 최소 실행 예시

아래 명령은 다음 작업자가 실행할 수 있는 안내다. 이번 이관 작업에서 다시 실행하지 않았다.
로컬 `cargo` shim 상태 때문에 `cargo +1.98.1` 대신 rustup을 명시하는 편이 안전하다.
CI toolchain은 1.98.1로 고정돼 있다.

```sh
cd /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity
/Users/sjkim1127/.cargo/bin/rustup run stable cargo build --locked -p fission-fsl --bin fslc
target/debug/fslc compile crates/fission-fsl/specs/amdgcn-gfx900-scalar-sequence.fsl /tmp/scalar.fslc
target/debug/fslc compose-sequence /tmp/scalar.fslc amdgcn.gfx900.scalar.sequence 0x1000 7 2 0002048001030582 /tmp/chain.fslseq
target/debug/fslc inspect-sequence /tmp/chain.fslseq
target/debug/fslc execute-sequence /tmp/chain.fslseq 4294967295,0,1,0,99,99,77 1,1
target/debug/fslc emit-sequence /tmp/chain.fslseq c /tmp/chain.c
```

기록된 기대 결과:

```text
status=Success registers=[4294967295, 0, 1, 0, 0, 1, 77] flags=[0, 1]
```

구현 변경의 검증을 요청받은 경우 사용할 주요 명령:

```sh
cd /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity
/Users/sjkim1127/.cargo/bin/rustup run stable cargo fmt --all -- --check
/Users/sjkim1127/.cargo/bin/rustup run stable cargo clippy --locked -p fission-fsl --all-targets -- -D warnings
/Users/sjkim1127/.cargo/bin/rustup run stable cargo nextest run --locked -p fission-fsl --no-capture -j 1

cd /Users/sjkim1127/Documents/ChatGPT/fission-research
python3 -m unittest discover -s tests -v
python3 tools/structured_fir_reproduce.py --fslc /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity/target/debug/fslc
python3 tools/register_fir_reproduce.py --fslc /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity/target/debug/fslc
python3 tools/sequence_fir_reproduce.py --fslc /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity/target/debug/fslc
```

역사적 artifact와 SLA/ABI/library 재현은 `docs/reproduction.md`의 전제 입력과
각 명령을 읽는다. `Fission/`의 고정 리비전이나 signatures를 임의로 최신판으로 바꾸지 않는다.
lock hash는 실패를 없애려고 업데이트하지 말고, 의도한 입력·출력 변경을 검토한 뒤 업데이트한다.

## 7. 다음 구현 단위 — 제안이며 미구현

다음 경계는 **명령 간 branch/PC 계약과 loader에 근거한 byte origin**이다.
기존 명령 내부 CFG와 guest control flow를 구분하는 설계부터 시작한다.

1. guest next-PC, fallthrough, direct/conditional target, address unit 계약을 작성한다.
   기계어 branch를 일반 sequence fallthrough로 실행하지 않는다.
2. 같은 FIR과 instance graph에 제어 효과를 추가한다.
   NIR/HIR이나 P-code 호환 opcode 계층을 새로 만들지 않는다.
3. 처음에는 범위를 명시한 acyclic direct branch/diamond에 한정한다.
   unknown·범위 밖·잘못 정렬된 target은 거부한다.
   loop 실행에는 별도 종료성·실행 상한 계약이 필요하며 현재 지원 범위가 아니다.
4. taken/untaken, join, register alias, bad target, 실패 시 상태 보존을 독립 oracle과
   C/Rust 출력으로 비교한다. 합성 fixture의 성공을 실제 바이너리 lifting이라고 부르지 않는다.
5. loader 연결 전에 native loader의 owner와 `AGENTS.md`를 읽는다.
   기존 canonical loader/program metadata를 사용하고 별도 병렬 fact map을 만들지 않는다.
6. 명시적으로 선택한 실제 바이너리 span의 file offset, virtual address, section,
   exact bytes, whole-file hash와 window hash를 구분해 유지한다.
7. 대상 span에 미지원 명령이나 제어 의미가 있으면 lifting을 거부한다.
   이후 제한한 실제 함수의 state/CFG 비교로 진행한다.

이는 이관용 제안이며 branch/PC나 loader 기반 lifting이 이미 구현됐다는 뜻이 아니다.
GPU memory/kernel ABI, 일반 SLA migration, 최종 machine-code backend는 후속 연구 과제다.

## 8. 후속 작업의 보고·커밋 계약

- 시작할 때 두 checkout의 branch/dirty/HEAD, 관련 구현, PR/CI를 다시 확인한다.
- 과거 측정값과 이번 실행값을 구분한다. 확인하지 않은 CI를 성공이라고 말하지 않는다.
- 구현·관찰·주장할 수 있는 범위·미지원을 명시한다.
- 명령 추가를 FSL 데이터만 수정 / 공통 primitive 추가 / architecture-specific 확장으로 기록한다.
- 독립 oracle의 byte encoding 비교와 execution semantics 비교를 구분한다.
  같은 의미 구현에서 생성한 C/Rust의 일치만으로 명세의 정확성을 증명했다고 말하지 않는다.
- native 변경을 지정 실험 branch에 commit/push한 뒤 연구 fixture/lock/docs와
  CI compiler pin을 업데이트하고 연구 `main`에 commit/push한다.
- PR #176을 업데이트하고 merge하지 않는다. 이번 문서 작성은 다음 단계 구현이 아니다.

## 9. 다른 AI에게 전달할 시작 프롬프트

```text
Fission FSL/FIR 연구를 이어받아 주세요.
먼저 /Users/sjkim1127/Documents/ChatGPT/fission-research/docs/ai-handoff.md를 읽고,
두 checkout의 branch·dirty·HEAD, AGENTS.md, 구현, PR #176과 CI를 다시 확인하세요.

연구 자료는 /Users/sjkim1127/Documents/ChatGPT/fission-research의 main,
native 구현은 /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity의
codex/fsl-jvm-iadd-parity에서 작업합니다. 제품 main에는 commit/push하지 않고 PR은 merge하지 않습니다.

단일 FIR, 정확성·행동 보존 재컴파일 우선, unsupported fail closed를 유지하세요.
NIR/HIR 분리나 필수 P-code lowering을 도입하지 않습니다.
최신 구현은 FirSequence의 순차 state/origin 연결입니다.
다음 단계는 명령 내부 CFG와 구분한 명령 간 branch/PC 계약과 loader 기반 byte origin입니다.
현재 계약을 읽고 제한한 구현 단위를 결정하여 변경과 근거를 기록하세요.
과거 검증을 이번 실행 결과로 취급하지 말고, 합성 성공을 GPU hardware나 전체 함수 동치라고 부르지 마세요.
```
