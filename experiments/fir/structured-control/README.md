# 단일 FIR의 블록·즉시값·비교·분기

2026-10-04. 자체 작성한 instruction semantic-body CFG slice다. 실제 CPU/GPU/VM
함수의 바이너리 lifting이나 원본 소스 제어 구조 복원 실험은 아니다.

## 구현

- `FirOp::IntConstant`, `IntCompare(Equal/UnsignedLess/SignedLess)`.
- 단일 `CompiledInstruction`의 값/연산 테이블과 `FirBlock` op 범위·parameter,
  `FirTerminator` return/branch/conditional branch.
- 범위·타입·정의·도달 가능성·branch arity 검증. 다른 block의 값은 edge 인자로 전달.
- `.fslc` v6 직렬화. v1–v5 layout 보존, legacy body는 entry/return view로 처리.
- 비순환 정수/스택 CFG의 reference/C/Rust 실행. 선택된 successor만 효과를 실행.

`stack-branch-join.fsl`은 입력을 u32로 truncate하고 10 미만이면 1, 그 외에는
2를 wrapping add한 다음 양쪽 결과를 join parameter로 전달한다. `.fir`, `.c`,
`.rs`는 이 단일 FIR의 출력이다. [lock](control.lock.toml)은 source/package/output
해시를 고정한다. 바이너리 패키지는 `artifacts/`에 재생성한다.

## 관찰

Rust gate는 16개 프로파일의 2,048개 reference/oracle 상태와 8,192개
C/Rust O0/O2 실행 비교를 통과했다. 폭 1/8/32/64, 세 비교 종류, block argument
재정렬, linear constant, empty body, transient stack peak를 포함한다.
별도 첫 명세의 65,536개 입력을 독립 계산식과 비교했다. Native CLI는 포장된
명세를 실행하고, GPU/register/JIT/AOT backend 거부를 검사한다.

C/Rust 실패 비교는 backing slot 네 개 전부를 확인하고, 성공 비교는 active
stack을 확인한다. 컴파일은 warnings를 거부한다. 이것은 합성 의미 계약 증거이고
디컴파일 품질이나 전체 함수 동치의 증거가 아니다.

```sh
python3 tools/structured_fir_reproduce.py --fslc /path/to/fslc
# Fission 실험 worktree에서:
cargo nextest run -p fission-fsl --test control --nocapture
```

재현 프로브는 package hash와 출력 세 개를 확인하고, 독립 CLI 계산식 12개,
실패 시 active state 보존 두 개를 검사한다. Rust 실행·재컴파일 gate와 검증
건수를 합치지 않는다.

## 아직 미지원

순환 CFG와 스택 delta가 다른 join/return은 FIR로 보존할 수 있지만 reference 및
C/Rust backend는 거부한다. 이 backend는 모든 syntactic path의 최악 stack
깊이를 preflight하며, 실행하지 않을 branch도 capacity 요구를 높일 수 있다.
이는 명시적 도구 실행 전제이며 guest trap 의미가 아니다.

Structured GPU/SIMT 실행, register-state CFG, memory/exception/call, multi-instruction
binary function lifting, nested domain region, 구조 FIR의 native JIT/AOT 실행은
미지원이다. 기존 GPU·register·native lift-record 소비자는 control body를 거부해
flat op 테이블을 무조건 실행하지 못하도록 했다.
