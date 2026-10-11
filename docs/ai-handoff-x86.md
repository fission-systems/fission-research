# 현재 x86 FSL/FIR 작업 이관 — 2026-10-11

이 문서는 이전 FirSequence 단계의 이관 자료보다 최신이다. 시작할 때 branch,
dirty state, AGENTS.md, PR #176과 CI를 다시 확인한다.

## 위치와 계약

- 연구: `/Users/sjkim1127/Documents/ChatGPT/fission-research`, `main`.
  실행 fixture/report 기준 `69b6f89`, Linux CI 연결 기준 `c718c31`.
- Native: `/Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity`,
  `codex/fsl-jvm-iadd-parity`, `8211a05610204670a4f5542298d8a4e0d9fe5983`.
  제품 main에 commit/push하지 않는다.
- 비교 입력: 연구 `Fission/`, 고정 `96fc71f75cecdee305faf9497561c577a8955468`.
  실제 구현 checkout으로 혼동하지 않는다.
- [PR #176 — FSL/FIR 실험지원](https://github.com/fission-systems/Fission/pull/176)은
  사용자 후속 결정까지 열어 둔다. Merge하지 않는다.
- 외부 instruction decoder 의존성 금지. 하나의 FIR, 정확성과 동작 보존 재컴파일
  우선. Unsupported fail closed; source prototype/ABI/type을 추측해 확정하지 않는다.

## 최신 실행 범위와 의미 소유자

`crates/fission-fsl`의 `package/parser/semantics/state`가 typed canonical FIR을
소유한다. `MemoryStoreLittle` / `memory.store.le`는 v11 op tag 22이며 이전 버전과
기존 artifact 형식을 유지한다. ISA별 arithmetic executor를 추가하지 않는다.

`x86_decode.rs`는 `.fslx` encoding rule과 generic operand forms를 읽고,
`x86.rs`는 loader가 제공하는 selected executable spans의 raw bytes/origin을 유지한
채 FIR body를 bind한다. `scalar-stateful.fslx` 48 rules,
`scalar-stateful-bodies.fsl` 141 bodies. MOV store, PUSH/POP, 기존 readonly scalar
forms까지 포함하며 full x86 migration은 아니다.

`recovery.rs`는 FIR의 entry register/memory dependencies, modular affine address,
ordered store origins와 read-after-store/possible aliases를 파생한다. Exact 같은
주소·폭과 중간 alias 없음만 forwarding한다. Partial/unknown alias는 후보를 보존한다.
Stack spill과 input pointer가 겹칠 수 있어 RBP 후보가 반환값에 남을 수 있다.
Convention unselected; argument count/source signature/pointer type unknown.

Readonly/mutable memory window의 권한이 명시적이다. `execute_mut`와 C/Rust wrapper는
성공한 supplied window의 state/memory/exit만 commit한다. Mutable cap 1 MiB,
출력은 memory와 같은 길이의 disjoint scratch를 요구한다. 실패 시 scratch는 unspecified.
CPU fault ordering/atomicity나 guest concurrent memory model로 설명하지 않는다.
16-bit stack은 modern IA-32이고 8086 PUSH SP를 포함하지 않는다.
Stack-address-width=mode, SS.base=0; descriptor B flag 복구는 없다.

## 재현과 관찰된 증거

```sh
cd /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity
/Users/sjkim1127/.cargo/bin/rustup run stable cargo build --locked -p fission-fsl --features x86 --bins
/Users/sjkim1127/.cargo/bin/rustup run stable cargo nextest run --locked -p fission-fsl --features x86 --test-threads 1
/Users/sjkim1127/.cargo/bin/rustup run stable cargo build --locked -p fission-emulator --example x86_fir_baseline

cd /Users/sjkim1127/Documents/ChatGPT/fission-research
FISSION_RESOURCE_ROOT=/Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity \
python3 tools/x86_stateful_validate.py \
  --fsl-x86 /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity/target/debug/fsl-x86 \
  --pcode-baseline /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity/target/debug/examples/x86_fir_baseline \
  --baseline-root /Users/sjkim1127/Fission.worktrees/fsl-jvm-iadd-parity \
  --cc /opt/homebrew/opt/llvm/bin/clang \
  --rustc '/Users/sjkim1127/.cargo/bin/rustup run stable rustc'
```

이번 로컬 검사: full nextest 66 passed/0 skipped, Python 27, strict FSL Clippy/format,
이전 x86/structured/register/sequence 및 migration artifact 재현.
세 fixed ELF의 FIR 768 states와 C/Rust O0/O2 success/rollback 6,144회가 일치한다.
Rosetta64 original bytes의 result/six defined flags/RBP/SP balance/external words
512회가 일치했다. i386 original은 로컬에서 미실행이며 Linux CI adapter가 필수다.
전체 modeled GPR/memory 비교와 machine adapter의 제한된 관찰 범위를 혼동하지 않는다.

Actual SLA/canonical P-code baseline의 GPR/exit/160 bytes는 일치하고 fixture마다
AF 96/256 차이가 있다. 기존 명세 누락이며 P-code 표현력 한계가 아니다.
Controlled metadata ablation 및 일반 함수 ABI 정확도 비교는 아직 미수행이다.
Source/ELF/package/output/tool/hash/checkout 상태는
[잠금과 보고서](../experiments/x86/stateful/README.md)에 있다.
CI 결론은 live run과 보관 보고서를 확인하고 과거 결과와 구분한다.

원격에서도 native `8211a0561`의 [Fission CI](https://github.com/fission-systems/Fission/actions/runs/38130023456),
연구 `623a806`의 [보완된 oracle CI](https://github.com/fission-systems/fission-research/actions/runs/38130695902)가
통과했다. 후자의 Linux original32/64 768회와 FIR 768/C·Rust 6,144회가 일치했다.
Report 보관 이후의 data/doc-only head 재실행과 이 측정 head의 결과를 구분한다.

## 다음 구현의 경계

1. 현재 normalized operand token은 displacement와 immediate가 같은 field를
   사용한다. **분리 binding/형식 검증**을 먼저 설계하고 memory immediate를 거부하는
   현 계약을 유지한다. 기존 package bytes를 조용히 재해석하지 않는다.
2. 그 다음 CALL/return의 state/memory/control 계약, callee ABI allocation과
   register save/restore evidence를 연결한다. Source prototype을 확정하지 않는다.
3. Recovered guest CFG join/loop의 effect/alias 계약은 별도 단위다. 현재 input
   evidence는 unknown control을 거부하며 전체 함수 동치 증거가 아니다.
4. 같은 semantic coverage의 baseline과 origin/context/definedness/structure
   ablation을 독립 oracle에서 비교해야 FIR 정보 보존의 정확도 효과를 주장할 수 있다.

FSL만 수정한 추가, 공통 primitive, ISA operand binding, architecture semantic escape를
각각 기록한다. Native experimental commit/push → research fixture/lock/CI pin 갱신 →
research main commit/push 순서로 진행하고 기존 PR 설명을 갱신한다.
