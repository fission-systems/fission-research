# x86 readonly memory와 입력 근거 — 2026-10-11

목표는 정확성을 유지하면서 일반 함수 ABI 복구로 나아가는 것이다. 이번 단위는
**세 실제 compiled ELF의 readonly memory source와 입력 의존성 후보**다.
전체 x86 이관, 일반 ABI 복구, 전체 함수 동치 검증은 여전히 미완료다.

## 동일한 FIR 경로

```text
46 FSL encoding rules + 126 canonical FIR bodies
  → offline binary package → owned x86 reader → original-byte instances
  → canonical FIR → reference / C / Rust / derived input evidence
```

`tools/x86_migrate.py --memory-sources`는 초기 63개 body에 MOV/ADD/SUB/CMP/
AND/OR/XOR memory source body 63개를 추가한다. 기존 LEA 주소 body와 scalar
연산 body를 재사용한다. Rust decoder는 generic RegRm memory form을 연결했다.
새 opcode rule이나 arithmetic executor, 외부 decoder 의존성은 추가하지 않았다.
126개라는 수는 작성한 template 수이며 모두 독립 oracle로 검증한 수가 아니다.
이전 flag 없는 generator 출력과 초기 artifact 해시는 유지된다.

| 고정 ELF | 원본 span @ `0x401000` | FIR에서 추적한 입력 후보 |
|---|---|---|
| cdecl32 | `8b44240803442404c3` | entry ESP+8 / ESP+4의 32-bit 읽기 |
| pointer64 | `488b4708480307c3` | entry RDI+8 / RDI+0의 64-bit 읽기 |
| pointer64_xor | `488b4708483307c3` | entry RDI+8 / RDI+0의 64-bit 읽기 |

각 ELF는 Clang/LLD 22.1.8로 C fixture를 컴파일했다. cdecl32는 regparm이 아닌
기본 i386 cdecl이고, 64-bit fixture는 pointer를 받는 SysV AMD64 leaf다. 이는
fixture 생성 계약이다. 복구기는 ABI를 선택하지 않는다. FIR 분석은 register0를
반환값으로 가정한 사실을 표시하며 원래 prototype·signedness·pointer type·argument
count는 unknown이다. RET의 entry SP+0 읽기는 control/other로 구분한다.
원본 bytes, instruction 주소, FIR operation index와 memory width가 근거에 남는다.

`recovery::RecoveryState`는 canonical FIR의 abstract interpretation이다.
실행 의미를 별도로 정의하지 않는다. Typed 연산·conversion·block argument에서
entry dependency와 modular affine address를 추적한다. Unknown branch와 지원하지
않는 transfer는 거부한다. 더 좁은 modular wrap을 넓은 addition으로 바꾸지 않는다.

## 관찰

[로컬 보고서](validation-2026-10-11.json)는 compiler/tool/host 및 기존 SLA,
canonical evaluator와 baseline executable 해시를 기록한다.
[Linux x86 CI 보고서](validation-linux-ci-38100633006.json)는 같은 compiler commit의
[실행 38100633006](https://github.com/fission-systems/fission-research/actions/runs/38100633006)에서
받은 원본 artifact다. Ubuntu clang 18.1.3 / Rust 1.98.1 / x86_64에서 측정했다.

| 검사 | 실제 결과 |
|---|---|
| Native full x86-feature nextest | 61 passed / 0 skipped |
| 세 ELF의 FIR 상태 | 256 × 3 = 768, 독립 arithmetic/state 계산과 일치 |
| 생성 C/Rust O0/O2 실행 | 3,072회, 전체 modeled state와 exit 일치 |
| 원본 64-bit ADD/XOR bytes | Rosetta 실행 512회, 결과와 정의된 arithmetic flags 일치 |
| 원본 32/64-bit bytes | Linux x86 CI 768회, result와 defined flags 일치; 로컬 i386 미실행 |
| 기존 SLA/P-code ADD | 각 fixture 256개 중 AF 차이 96개; 다른 flags/GPR/exit 차이 0 |
| 기존 SLA/P-code XOR | 정의된 flags/GPR/exit 차이 0; undefined AF 256개 제외 |
| 초기 artifact 재현 | 기존 15개 출력 / reference 실행 5개 / source compile 10개 유지 |

P-code baseline은 실제 compiled SLA frontend와 기존 canonical evaluator를 쓰는
Fission의 research-only example이다. FSL runtime의 dependency가 아니다. 기존
`ia.sinc`의 `resultflags`에 `AF not implemented`가 명시되어 있다. ADD 1+15에서
기존 AF=0, FIR AF=1이며 원본 64-bit Rosetta 관찰 AF=1이다. 이 차이는 현재
명세 구현의 누락 사례다. P-code 자체의 표현 불가능성을 의미하지 않는다.
[P-code는 memory와 control 연산도 제공한다](https://ghidra.re/ghidra_docs/languages/html/pcodedescription.html).
FIR 철학의 정확도 효과를 확인할 추가 실험은 [평가 설계](../../../docs/fir-evidence-and-accuracy.md)에 있다.

XOR의 AF는 [Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)
상 undefined다. FIR은 known bit를 지우고 비교기는 AF placeholder를 비교하지 않는다.
Undefined 값까지 우연히 맞는 것을 정확성으로 계산하지 않는다.

## 재현

실험 Fission checkout에서:

```sh
cargo build --locked -p fission-fsl --features x86 --bins
cargo nextest run --locked -p fission-fsl --features x86 --test-threads 1
cargo build --locked -p fission-emulator --example x86_fir_baseline
```

연구 저장소에서:

```sh
python3 tools/x86_migrate.py --fission-root Fission --memory-sources \
  --output-dir artifacts/x86-memory-specs
python3 tools/x86_semantics_validate.py \
  --fsl-x86 /path/to/Fission/target/debug/fsl-x86 \
  --pcode-baseline /path/to/Fission/target/debug/examples/x86_fir_baseline \
  --baseline-root /path/to/Fission \
  --cc clang --rustc 'rustup run stable rustc'
```

`source.lock.json`은 원문 snapshot, fixed ELF/source/spec/package와 12개 출력
해시를 고정한다. Validator는 inputs/package/output을 다시 비교하고 768개 FIR 상태와
emitted-source executable을 실행한다. 256개 입력은 boundary 64개 + deterministic
random 192개다. P-code 차이는 관찰값이며 예상 차이를 강제로 통과 조건으로 쓰지 않는다.
Machine 실행이 가능한 host는 그것도 필수 비교한다. `none`은 report에 미실행으로 남는다.

Linux x86 CI에서는 original32의 libc 없는 static i386 adapter와 original64 adapter를
실제로 실행했다. 세 fixture 각각 256회, 총 768회가 FIR과 일치했다. Generated C/Rust
3,072회도 재검증했으며 legacy ADD AF 차이 96개씩과 XOR AF 제외도 재현했다. 원본 ELF의 locked instruction bytes를 그대로 내장하며 decoder나
C 재구현이 아니다. 이 세 leaf는 PC-relative 참조가 없어서 adapter 주소로 옮길 수 있다.
원본 machine oracle는 result와 defined flags만 비교한다. All-register hardware snapshot,
fault·privilege·concurrency·임의 relocation·전체 ABI는 측정하지 않는다.

FSL strict Clippy와 format은 통과했다. Baseline은 build와 제품 CI와 같은
`-D warnings -A clippy::style -A clippy::complexity` 조건에서 통과했다.
Unqualified strict baseline Clippy는 기존 solver/emulator의 style/complexity lint에서
실패했다. 해당 library 변경은 없다.

## 현재 계약과 다음 단위

Bounded readonly flat memory, segment bases=0, caller 지정 executable span이 계약이다.
Stores, LOCK, stack frame, CALL/callee ABI, unknown control joins, memory ordering/fault,
대부분의 x86 명령과 source prototype 복구는 지원하지 않는다. Wrapper의 실패 rollback은
CPU exception ordering을 의미하지 않는다. 실행 비교는 세 leaf에 한정되며 전체 함수
동치 증명이나 일반 디컴파일 품질 지표가 아니다.

다음은 store/stack-frame/call 효과와 CFG join을 같은 FIR에 연결하고, origin·relocation·
symbol·DWARF·기존 ABI metadata의 후보를 충돌 없이 연결하는 것이다. Convention/type
선택은 추가 근거와 실행 검증이 있을 때만 허용한다.
