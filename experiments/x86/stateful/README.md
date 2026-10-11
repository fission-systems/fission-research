# x86 store·스택 프레임 — 2026-10-11

같은 canonical FIR에 ordered `memory.store.le`를 추가하고 실제 함수의 스택
저장·복원을 연결했다. 전체 x86 이관이나 일반 함수 ABI 복구 완료를 의미하지 않는다.

구현 pin: [`8211a0561`](https://github.com/fission-systems/Fission/commit/8211a05610204670a4f5542298d8a4e0d9fe5983).

## 구현과 계약

- 자체 reader를 유지하며 **48 encoding rules / 141 FIR bodies**를 컴파일한다.
  기존 readonly pool 126개에 MOV store 9개 + PUSH/POP 6개를 추가했다.
- Register→memory MOV의 주소는 기존 generic ModRM/SIB reader가 bind하고,
  memory write 및 stack arithmetic은 FSL body가 소유한다. 별도 mnemonic executor 없음.
- PUSH는 이전 input/SP를 캡처한 뒤 저장하고 SP를 갱신한다. POP는 이전 SP에서
  읽고 SP를 증가한 다음 destination을 쓴다. POP SP도 이 순서를 따른다.
- 16비트는 현대 IA-32 의미이며 8086 `PUSH SP`는 포함하지 않는다. Stack address
  width는 선택 mode와 같고 SS base는 0이다. Descriptor B flag를 복구하지 않는다.
  [Intel SDM Vol. 2B의 PUSH/POP](https://www.intel.com/content/dam/www/public/us/en/documents/manuals/64-ia-32-architectures-software-developer-vol-2b-manual.pdf)을
  2026-10-11에 확인했으며 PDF SHA-256을 해당 FSL body의 evidence에 기록했다.
- FIR package v11 op tag 22; 기존 v1..v10과 초기/readonly artifact를 유지한다.
- Mutable window는 최대 1 MiB다. 성공 시만 state/memory/exit를 commit한다.
  C/Rust 출력은 memory와 길이가 같은 disjoint scratch를 받는다. 실패 시 caller
  state/memory/exit는 보존하며 scratch는 unspecified다. CPU fault ordering/atomicity 아님.
- Memory immediate는 변위/즉시값의 분리 binding이 없어 거부한다. 지원하지 않는
  memory ALU body, CALL/LEAVE, prefixed stack forms, MMU/fault/ordering도 거부한다.

외부 instruction decoder나 새 dependency/Cargo.lock 변경은 없다. 기존 Fission loader,
canonical FIR validator/evaluator/emitter를 사용하며 production main을 변경하지 않는다.

### 추가 방식 기록

| 추가 | 명세 | 공통 primitive / ISA operand binding |
|---|---|---|
| MOV register→memory | 값·주소 폭 조합 9 bodies | 공통 `MemoryStoreLittle` 1개; 기존 ModRM/SIB reader의 memory-destination 연결 확장 |
| PUSH/POP register | 폭 16/32/64의 6 bodies, encoding rules 2개 | 위 store primitive 공유; x86 operand forms `push_reg`/`pop_reg` 2개 추가 |

아키텍처별 arithmetic semantic executor는 0개다. 이번 추가는 compiler/reader도
변경했으므로 **15개 body의 명세-only 추가 성공률로 계산하지 않는다.**

## 고정 compiled ELF

| 함수 | 생성 조건 | 실제 효과 |
|---|---|---|
| frame32 | Clang/LLD 22.1.8, i386, O0 / frame pointer | EBP 저장, frame-relative argument reads, ADD, EBP 복원 |
| frame64 | 같은 compiler, AMD64, O0 / frame pointer | RBP 저장, red-zone pointer spill/reload, memory ADD, RBP 복원 |
| store64 | 같은 compiler, AMD64, O2 | two-word pointer read, ADD, 첫 word에 외부 store |

각 function span은 `0x401000`의 17/25/11 bytes다. Source/ELF/compiler command와
원본 bytes, package 및 12개 FIR/C/Rust/input-evidence hash는 `source.lock.json`에 있다.
Oracle adapter는 locked ELF bytes를 그대로 내장한다. 이 세 span은 PC-relative 참조가
없어서 adapter 주소로 이동 가능하다. 임의 바이너리 relocation 지원을 주장하지 않는다.
64-bit adapter는 RBP를 indirect target의 입력 레지스터로 배정하지 못하게 하고,
call-site stack alignment를 검사한다. Adapter executable 및 source lock와 공통
arithmetic oracle module의 SHA-256도 실행 report에 기록한다.

## 입력 근거와 별칭

Derived analysis는 같은 FIR에서 entry register/address dependency와 store의 origin을
추적한다. 주소·폭이 정확히 같고 중간에 가능한 별칭이 없으면 저장한 값을 전달한다.
동일 modular root의 disjoint 범위만 건너뛴다. 부분 overlap이나 서로 다른 entry pointer의
별칭을 알 수 없으면 external-read와 possible-store 의존성을 함께 남긴다.

frame32의 POP는 saved EBP store에서 값이 전달되며 entry ESP+4/+8 argument reads를
추적한다. frame64의 pointer spill/reload는 연결되지만 pointer가 stack 저장 영역과
겹칠 가능성도 후보에 남긴다. 이 때문에 RBP 의존성이 반환값 후보에 포함될 수 있다.
후보가 source prototype·argument count·pointer type·calling convention을 확정하지 않는다.
전체 ABI allocator나 general CFG merge는 아직 없다.

## 관찰된 검사

| 검사 | 로컬 결과 |
|---|---|
| Full x86-feature nextest | 66 passed, 0 skipped |
| 세 ELF의 independent arithmetic/state/memory 계산 | FIR 768개 상태 일치 |
| C/Rust O0/O2 | 성공 3,072 + rollback 3,072 = 6,144회 |
| 원본 64-bit bytes / Rosetta | 512회 result·six defined flags·RBP 보존·SP balance·외부 두 word 일치 |
| 원본 i386 bytes | 로컬 미실행; Linux x86 CI adapter 연결 |
| 실제 SLA + canonical P-code evaluator | 각 fixture 256회 GPR/exit/160-byte memory 일치; AF만 각각 96개 차이 |

실패 corpus는 frame의 PUSH 또는 store64의 실제 MOV store 후에 budget을 소진한다.
별도 native 검사는 store 후 더 넓은 load 실패, late RET 실패, readonly permission,
typed/package version guard, PUSH/POP SP alias와 partial/unknown store alias를 검사한다.
Strict FSL Clippy는 feature on/off에서 통과했다. Baseline Clippy는 제품 CI와 같은
style/complexity 허용 조건에서 통과했다.
실행 보고서는 [local validation](validation-2026-10-11.json)에 보관했다. Native checkout의
commit/clean 상태와 compiler source/executable SHA-256도 함께 기록했다.

Memory comparison의 전체 160 bytes와 17 GPR transport slots는 FIR/C/Rust 및 SLA
state에서 관찰한 것이다. Hardware adapter는 반환값/flags/frame balance/RBP와
외부 두 word만 관찰한다. 실제 모든 레지스터·stack bytes·fault/concurrency·전체 ABI를
hardware에서 비교한 것은 아니다. AF 차이는 기존 명세의 누락이며 P-code IR 표현력
한계나 FIR 철학의 우월성 증거가 아니다. Controlled ablation은 아직 계획 단계다.

## 재현

실험 Fission checkout에서:

```sh
cargo build --locked -p fission-fsl --features x86 --bins
cargo nextest run --locked -p fission-fsl --features x86 --test-threads 1
cargo build --locked -p fission-emulator --example x86_fir_baseline
```

연구 checkout에서:

```sh
python3 tools/x86_migrate.py --fission-root Fission --memory-writes \
  --output-dir artifacts/x86-stateful-specs
python3 tools/x86_stateful_validate.py \
  --fsl-x86 /path/to/Fission/target/debug/fsl-x86 \
  --pcode-baseline /path/to/Fission/target/debug/examples/x86_fir_baseline \
  --baseline-root /path/to/Fission \
  --cc clang --rustc 'rustup run stable rustc'
```

Linux x86 CI는 native 32/64 original-byte adapters를 필수 비교한다. Local ARM64 macOS는
Rosetta64만 실행하고 i386은 미실행으로 기록한다. Tool/host/source/executable hash와
baseline 차이는 report에 분리되며 baseline 차이 수를 통과 조건으로 강제하지 않는다.

다음 단위는 displacement/literal binding 확장, call/return 및 ABI allocation,
guest CFG join과 loop에서의 메모리/상태 계약이다. 전체 함수 실행 동치와 일반 source
prototype 복구는 아직 미완료다.
