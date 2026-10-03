# FSL/FIR 연구 진행 현황

기준일: 2026-10-03. 이 문서는 설계 결정, 구현 위치, 기존 관찰 결과와 미지원 범위를 구분한다. 각 실행 단계의 검증 범위를 별도로 기록한다.

## 채택한 방향

- FSL 명세·컴파일러·FIR을 직접 소유하고 최종적으로 SLEIGH 의존성을 제거한다.
- 단일 FIR에서 C·Rust·진단·분석 등 여러 출력 계층을 만든다. 새 의미 파이프라인에 NIR/HIR 구분을 도입하지 않는다.
- 정확성과 동작 보존 재컴파일을 우선한다. 원본 바이트 일치와 실행 동작 일치는 별도 기준이다.
- `.fsl` 텍스트 → 검증된 바이너리 `.fslc` → 선택적 AOT/JIT를 지향한다. JSON은 기존 프로브 자료나 디버그·교환 출력에 한정한다.
- 아키텍처·버전·출처와 지원 범위를 명시한다. 미지원 효과를 일반 연산이나 no-op으로 바꾸지 않는다.

## 구현의 소유 위치

| 위치 | 소유하는 산출물 |
|---|---|
| 이 연구 리포 | 독립 Python 프로브, 자체 작성 fixture, 초기 TOML/JSON 실험, 연구·참고 소스 기록 |
| [Fission PR #176](https://github.com/fission-systems/Fission/pull/176) | Rust `fission-fsl`, 텍스트 문법, 바이너리 패키지, canonical FIR, 실행 출력과 인코딩 프런트엔드 |
| 로컬 `Fission/`, `Vendor/` | 비교·참고 소스; 런타임 의존성이 아니며 클론 자체는 이 리포에 커밋하지 않음 |

Fission 작업 브랜치는 `codex/fsl-jvm-iadd-parity`다. 최근 구현 스냅샷은 다음과 같다.

| 커밋 | 구현 |
|---|---|
| [`891f4a539`](https://github.com/fission-systems/Fission/commit/891f4a539454fa90ab7d318eec335923f8bb9400) | 단일 FIR의 기준 평가기와 C·Rust 실행 출력, SSA·타입 검증 |
| [`5376310b2`](https://github.com/fission-systems/Fission/commit/5376310b2077807de713d908ea100411efd73ef9) | 고정폭 인코딩 계획, `.fslc` v2, GFX900 네 규칙, 필드 추출·재인코딩 |
| [`fbc96040d`](https://github.com/fission-systems/Fission/commit/fbc96040dc8ac1130b68bf10f6904f87aee41a0d) | package v3 상태 FIR, GFX900 `s_add_u32` SGPR/SCC 실행과 C/Rust 재컴파일 검사 |
| [`cfcb0e0f3`](https://github.com/fission-systems/Fission/commit/cfcb0e0f3635849e5bcfd23d4f94def0ccd2094d) | package v4 carry-in, `s_addc_u32`, 자체 ABI 문법과 첫 eBPF Sleigh leaf 이관 |
| [`0bc0efbb1`](https://github.com/fission-systems/Fission/commit/0bc0efbb107e77c2baa84c942b567938da63d571) | package v5 lane 효과, wave64 EXEC 및 `v_add_u32`, uniform broadcast |
| [`cf2a023ff`](https://github.com/fission-systems/Fission/commit/cf2a023ff3c7cd7bbf17d5d902b1f5ffb485c9fc) | byte register layout·alias 저장소, strict ABI linking, FIR slot adapter |
| [`217d7eafd`](https://github.com/fission-systems/Fission/commit/217d7eafd90b396edc46f0c24fdb6372caf60354) | SLA-derived layout·ADD64 candidate, 원문/바이너리 parity·재컴파일 검증 |
| [`3eb686625`](https://github.com/fission-systems/Fission/commit/3eb6866250321fa2c0aef54238ae2b8168737a35) | 기존 단일 stack FIR의 CUDA C++ / PTX reference kernel 출력 |
| [`a67807616`](https://github.com/fission-systems/Fission/commit/a67807616a2d4c2b623819b2ded5d1b0e3b0fc29) | 자체 `.fsldb` prototype candidate reader와 native exact symbol 조회 |

Rust 구현을 연구 리포에 복사하지 않는다. 명세 소스와 API는 [해당 커밋의 crate](https://github.com/fission-systems/Fission/tree/5376310b2077807de713d908ea100411efd73ef9/crates/fission-fsl), 한계는 [GFX900 구현 보고서](https://github.com/fission-systems/Fission/blob/5376310b2077807de713d908ea100411efd73ef9/docs/research/fsl-gfx900-encoding-slice.md)를 참조한다. 이 기록은 메인 브랜치 채택이나 PR 병합을 뜻하지 않는다.

## 이 리포에 보관한 기존 연구 자료

- [SLA 스캔 기록](../notes/sla-corpus-scan-2026-09-30.md): 기존 스냅샷의 133개 SLA 구조 인벤토리. 구조 파싱은 의미 복원 완료를 뜻하지 않는다.
- [GFX900 실험](../experiments/gpu/amdgpu-gfx900/README.md): 자체 작성 어셈블리·LLVM IR, 작은 ELF 객체와 관찰 출력. GPU에서 실행하지 않았다.
- [JVM `iadd` 실험](../experiments/jvm/java-se-26/README.md): 초기 프로파일과 projection 자료. Python의 소스 문자열 출력은 실행 검증과 구분한다.
- [HIP/HSA/KFD 소스 추적](amdgpu-runtime-trace.md): 고정 소스 경로 조사와 synthetic AQL packet. 실제 런타임 캡처가 아니다.
- [GPU 참고 자료](../Vendor/README.md): NVIDIA·AMD·Intel 소스 5개와 AMD XML 10개의 커밋·해시 인벤토리. 클론은 로컬에만 둔다.
- [보관한 초기 P-code 조사](archive/fsl-fir-first-probe.md): 채택한 단일 FIR 연구 방향 이전의 질문과 관찰.

## Rust 구현에서 기록한 증거

`891f4a539` 단계는 C·Rust 각각 두 최적화 수준에서 1,920개 정수·스택 입력을 실행 비교했고 7,680회 비교가 통과했다. 이는 제한된 명령 계약의 증거이며 전체 함수·GPU 커널 동치 증명이 아니다.

`5376310b2` 단계는 빌드·Clippy·포맷 검사와 CLI 동작을 확인했다. `01 05 00 68`의 GFX900 원시 필드 추출과 destination=3 수정에 따른 `01 05 06 68` 재인코딩, 기존 JVM `iadd` JIT·실행 및 v1 패키지 읽기를 관찰했다. 앞 단계의 재컴파일 회귀 검사를 이 인코딩 변경에서 다시 실행하지 않았다. 과거 비교 횟수를 새 인코딩 지원의 검증 결과로 합산하지 않는다.

## 2026-10-01 자동 재현과 SOP2 확장

- `make test reproduce`: 기존 artifact 9개가 잠금 SHA-256과 일치했다. SLA 133개 구조 통계도 재현됐다.
- 새 Rust 텍스트 FSL 프로파일에 GFX900 SOP2 opcode 0x00..0x1f 32개를 추가했다. 기존 4개 프로파일과 별도로 컴파일한다.
- LLVM 22.1.8 조립/역조립 oracle과 256개 SGPR 입력의 명령·필드를 비교했다. 원형 round-trip 256개와 목적지 수정 후 독립 재조립 256개가 일치했다. 범위 밖 입력 99개를 거부했다.
- 추가 분류: 명세만 수정 32개, 공통 primitive 0개, 아키텍처별 코드 확장 0개. **인코딩에 한정한 결과**이며 실행 의미 표현력의 KPI가 아니다.
- Fission `bf49f27a9b8f0fdafedeba0c88a232522a39f267`에서 인코딩 회귀 검사 5개를 추가했다. crate 전체 9개 테스트와 Clippy가 통과했다. 기존 1,920개 입력 / 7,680회 C·Rust 실행 비교도 다시 통과했다.
- 기존 GPU `unsupported` 의미의 평가기·C/Rust 출력·JIT·AOT 거부와 상태 불변을 확인했다. 이는 새 `s_add_u32` 상태 slice와 별도 범위다.
- 연구 CI는 기존 artifact 재현과 SOP2/FIR 검증을 별도 job으로 실행한다. 원격 실행 결과는 GitHub Actions에서 확인한다.
- Fission 브랜치 `fbc96040d`에 단일 `s_add_u32` 상태 slice를 추가했다. FIR은 SGPR 읽기·쓰기, `u32` wrap add, `u1` carry, SCC flag 쓰기를 표현한다. 독립 widened-sum oracle과 reference/C/Rust O0/O2를 1,030개 상태 입력에서 4,120회 비교했고 모두 일치했다.
- 이 상태 slice는 package v3와 `execute-state` CLI를 실제 Fission crate에서 검사했다. 범위 밖 selector, 부족한 register/flag bank, 잘못된 flag, 변조된 decode observation은 상태를 변경하지 않고 거부한다. Cranelift JIT/AOT, EXEC/lane/wave, GPU hardware와 whole-kernel equivalence는 여전히 미지원이다.

자세한 범위·출처·해시는 [SOP2 실험](../experiments/gpu/gfx900-sop2/README.md)과 [상태 검증 기록](../experiments/gpu/gfx900-sop2/state-validation-2026-10-01.json), 재현 방법은 [자동 재현](reproduction.md)을 참조한다. LLVM opcode 참고 자료와 LLVM 실행 oracle은 계보를 공유하므로, 그 일치만으로 vendor 명세 독립 검증이나 GPU 실행 동치를 주장하지 않는다.

## 2026-10-01 carry-in 및 명세 이관

- Fission `cfcb0e0f3`에서 `s_addc_u32`의 SCC 읽기·합·carry-out을 단일 FIR에 연결했다. carry-in 연산은 package v4이며 기존 v1/v2/v3는 계속 읽는다.
- GFX900 32비트 상태 입력 1,030개 / C·Rust O0/O2 4,120회가 독립 widened-sum oracle과 일치했다. 공통 FIR 폭 1·8·16·32·64 전체는 5,150개 입력 / 20,600회이며, 32 이외의 폭은 synthetic primitive 검사다.
- `s_add_u32 → s_addc_u32`를 연결한 64비트 덧셈 1,060개가 reference oracle과 일치했다. 이 연결 검사는 C/Rust 재컴파일된 두 명령 연결의 증거는 아니다.
- eBPF ADD64 register leaf를 Sleigh 원문에서 실행 가능한 `.fsl`로 이관했다. 484개 상태 / 1,936회 C·Rust 비교가 통과했다. 기존 SLA 런타임에서도 실제 byte/length·register binding·IntAdd template 121개를 확인했다.
- BPF/eBPF의 `cspec` metadata를 자체 `.fslabi` 문법으로 변환하고 Fission의 typed parser로 읽었다. recursive cspec 110개 중 2개가 지원되고 108개는 미지원 이유를 기록한다. register linking·parameter allocator·call execution·binary ABI packaging은 미지원이다.
- 이관 산출물 4개가 고정 스냅샷에서 바이트 단위로 재현됐다. 기존 artifact 9개 재현도 다시 통과했다. Rust crate 17개 검사, Python 7개 검사, fmt/Clippy가 통과했다.

증거는 [carry 검증](../experiments/gpu/gfx900-sop2/carry-validation-2026-10-01.json)과 [명세 이관 실험](../experiments/migration/first-slice/README.md)에 있다. 직접 SLA-to-FIR 의미 변환은 아직 미구현이다. 이 스냅샷의 EXEC/lane은 [당시 상태 계약](https://github.com/fission-systems/Fission/blob/cfcb0e0f3635849e5bcfd23d4f94def0ccd2094d/docs/research/fsl-state-and-migration.md)에 설계만 된 단계였다.

## 2026-10-02 wave64 EXEC 및 vector add

- 단일 FIR에 mask snapshot·lane read·masked write를 추가하고 package v5로 직렬화했다. uniform/mask/lane 도메인은 typed producer에서 파생되며 별도 의미 IR을 만들지 않는다.
- `v_add_u32`는 VGPR/VGPR, SGPR0..95 broadcast/VGPR 두 패턴을 지원한다. 새 공통 primitive 3개와 FSL 패턴 2개가 추가됐으며 아키텍처별 실행 escape는 없다.
- 1,984개 정상 상태와 19개 잘못된 출력 입력, 총 2,003행 / C·Rust O0/O2 8,012회가 기대한 전체 상태와 일치했다. EXEC=0·전체 활성·희소·lane63·seeded mask, register aliasing, 비활성 lane high bits 보존을 포함한다.
- 별도 synthetic 4-lane 계약의 4행 / 16회 비교로 mask 범위, EXEC=0 scalar 효과, masked write, 늦은 bank 실패 이전의 무변경 거부를 확인했다. 이것은 GFX900 wave32 지원 증거가 아니다.
- LLVM 조립 128개에서 필드·원본 왕복·수정 후 조립 bytes가 일치했고 9개 미지원 입력을 거부했다. source/package/corpus SHA-256을 잠갔다. LLVM은 GPU 실행 oracle이 아니다.
- 기존 scalar·stack·eBPF 이관 회귀를 포함해 Rust crate 22개 검사와 fmt/Clippy가 통과했다. `execute-wave` CLI도 실제 컴파일 패키지를 실행했다.
- 실제 LLVM-compiled GFX900 ELF의 kernel slice 두 개에서 vector/scalar 입력 명령 행을 추출했다. `.text` 실제 bytes와 objdump·FSL 필드가 일치하고 reference CLI 합성 상태 6개가 통과했다. 나머지 kernel 명령과 whole-kernel 실행은 지원하지 않는다.

범위와 증거는 [wave64 실험](../experiments/gpu/gfx900-wave64/README.md)에 있다. GPU hardware/emulator, EXEC 쓰기·VCC·divergence·barrier·메모리·커널 동치, wave JIT/AOT는 미지원이다. register layout과 ABI 연결 및 직접 SLA 의미 이관은 다음 단계로 남아 있다.

## 2026-10-02 register layout 및 ABI 연결

- 자체 `.fslregs` 문법으로 공간·주소 폭·byte order·default memory·레지스터 offset/폭을 표현한다. BPF LE 15개 view와 15개 겹침, eBPF LE/BE 각 12개 view를 고정 원문에서 이관했다.
- `RegisterFile`은 공간별 backing bytes를 공유하고 부분 view 쓰기에서 나머지 바이트를 보존한다. 비바이트 주소 단위, 이름 중복·범위 초과·지나친 저장소 할당은 거부한다. zero extension이나 read-only 의미는 추정하지 않는다.
- eBPF의 R1–R5 인자, R0 반환, R6–R10 보존, R10 stack pointer를 실제 register identity/offset/폭으로 연결한다. BPF 원문은 RS=4바이트와 `pointer_size=8`이므로 최초 strict stack-width gate에서 거부하며 원문을 고치지 않는다.
- 단일 FIR reference evaluator에 명시적인 slot binding을 연결했다. 겹치는 logical slot과 폭 불일치는 거부한다. 동일 selector의 operand alias는 지원하며, 실패는 backing bytes를 변경하지 않는다.
- LE instruction profile을 두 register-storage byte order에서 평가한 968개 synthetic 상태가 별도 byte-storage oracle과 일치했다. BE eBPF decode·GPU layout·call ABI 실행·새 storage C/Rust projection의 증거는 아니다.
- 새 자료 4개는 정확히 재생성되고 native CLI 8개 gate가 통과했다. Python 10개 검사, Rust 29개 검사, fmt/Clippy와 기존 재컴파일 검사를 재실행했다. 실행 결과와 범위는 [register layout 실험](../experiments/migration/register-layout/README.md)에 기록한다.

이 단계는 package v5와 기존 encoding lock을 변경하지 않는다. direct SLA 결정 트리/context/template 이관은 아직 미구현이며, ABI allocator·call 효과·GPU lane 저장 layout은 다음 계약 확장이다.

## 2026-10-02 직접 SLA symbol/template 이관

- `sla_migrate.py`가 packed SLA v4를 직접 읽어 eBPF register symbol 12개와 공간·default memory를 `.fslregs`로 생성한다. `.sinc`/`.slaspec`이나 legacy decoder는 변환 과정에 사용하지 않는다.
- 129개 constructor 중 root는 98개다. BUILD → pure register export → handle INT_ADD인 root 한 경로와 export dependency 하나를 소비했다. 즉시값 branch와 나머지는 ID·source metadata·opcode·거부 사유를 기록한다.
- 결정 트리의 ancestor bit constraints와 leaf pair 순서를 보존한다. 앞선 competing pair는 거부하며, 뒤에 겹치는 넓은 jump 패턴은 기록한다. 알려진 opcode byte·mnemonic·constructor 번호·source line으로 의미를 선택하지 않는다.
- SLA-derived layout·encoding·canonical FIR이 원문 이관 결과와 일치했다. opcode/selector prefix 65,536개에서 같은 121개만 허용했다. SLA 후보의 synthetic 상태 484개 / C·Rust O0/O2 1,936회와 별도 byte-storage 상태 484개가 통과했다.
- 기존 SLA runtime의 byte/length·binding·IntAdd oracle 121개도 다시 통과했다. 원문과 SLA는 같은 계보이므로 이것은 vendor 독립 증명이나 eBPF verifier 실행이 아니다.
- opcode·context·extra effect·handle·BUILD·selector·export·priority 변조 8개를 거부했다. 새 산출물 3개와 package SHA가 재현됐고 native CLI 4개 gate가 통과했다. Rust 전체 32개, Python 14개, fmt/Clippy와 기존 재컴파일 회귀가 통과했다.

[SLA 이관 실험](../experiments/migration/sla-first-slice/README.md)에 registry·출처·해시·지원 범위가 있다. 직접 이관의 첫 branch가 구현된 단계이며 general SLA context·동적 handle·메모리·제어 흐름, 전체 VM·함수, GPU layout·kernel ABI는 미지원이다.

## 2026-10-03 독립 의미론 및 GPU 출력

- FIR을 자체 타입·연산·상태·효과·오류 규칙으로 정의하는 [중간 의미론 계약](fir-semantic-contract.md)을 채택했다. P-code는 목표 실행/분석 경로의 필수 단계가 아니다. 문서의 전체 계약이 구현 완료된 것은 아니다.
- Fission `3eb686625`가 동일한 `CompiledInstruction`에서 C/Rust와 CUDA C++/PTX를 출력한다. GPU 출력은 기존 stack pop/push와 1..64-bit wrapping add로 제한한다. 새로운 FIR 종류나 package version을 만들지 않았다.
- 한 상태를 좌표가 모두 0인 한 thread에서 처리하는 reference ABI를 명시했다. 깊이/underflow/peak capacity를 쓰기 전에 검사하며 status를 제외한 실패 상태와 non-owner의 무접근을 검증한다. 이 ABI는 GPU 바이너리에서 복원한 커널 ABI가 아니다.
- 41 profiles / 3,444개 generated-PTX scalar reference 상태가 별도 정수·상태 oracle과 일치했고 CUDA C++를 O0/O2에서 82회 Clang NVPTX로 컴파일했다. reference는 flat 주소와 작은 scalar subset만 모델링하며 GPU scheduling/memory consistency를 검증하지 않는다.
- Rust 전체 35개(새 projection 검사 3개), Python 18개가 통과했다. 기존 stack/scalar/carry/wave/eBPF C/Rust 재컴파일 회귀와 fmt/Clippy를 재실행했다. 8개 지원 밖 source/target 조합이 semantic gate에서 거부됐다.
- Linux CI에는 hash-locked NVIDIA ptxas로 direct/Clang PTX를 assemble하는 경로를 추가했다. 로컬 macOS에서는 ptxas를 실행하지 않았으며 assembly 결과는 CI report로 별도 확인한다.

[출력 실험](../experiments/gpu/fir-projections/README.md)은 3개 재현 artifact와 package/toolchain lock, source·license 근거를 보관한다. GPU hardware 실행, 실제 CUDA guest kernel decode/ABI 복원, GPU 병렬 메모리·분기·동기화·atomic과 자체 SASS backend는 미지원이다.

## 자체 자산 인벤토리와 library corpus — 2026-10-03

[자체 자산·구조 FIR 결정](owned-assets-and-structured-fir.md)은 SLEIGH source/SLA/cspec/pspec/ldefs/FPK의 대체 경로와 block·region·ordered effects 계약을 기록한다. 고정 `utils/`의 988개 파일을 해시 인벤토리로 남겼다. 현재 FIR 실행기는 단일 명령 연산열이며, 구조 계약의 구현 완료나 전체 자산 이관을 뜻하지 않는다.

FPK는 Fission 자체 container다. 이번에는 함수 후보 payload 하나를 `.fslib` TOML과 `.fsldb` binary schema 1로 이관했다. C library 64-bit의 31,418개 후보와 15,455개 parameter를 보존하고, source SHA/commit과 type·variadic 정보의 불확실성을 명시한다. 매크로와 누락된 variadic marker를 확정 함수·ABI로 승격하지 않는다.

Fission `a67807616`은 FPK를 호출하지 않는 독립 reader와 native inspect/exact query를 구현했다. 로컬에서 전체 행 파싱, `memcpy`/`malloc`/`printf` 조회 3건, 자체 작성 fixture의 TOML→binary 일치를 확인했다. Rust 37개 검사, Python 21개 검사, formatting과 warning-denied Clippy가 통과했다. 기존 C/Rust 실행·재컴파일 회귀 검사도 Rust gate에서 다시 실행했다.

[실험/lock](../experiments/migration/asset-replacement/README.md)에 재현 방법과 metadata 보존 범위를 기록했다. 제품 `fission-signatures` loader 교체, binary 함수 식별, ABI allocator, 전체 FPK corpus 이관, 구조 FIR 실행과 decompiler 품질 개선의 증거는 아니다. CI에 인벤토리·library 재현과 native reader 검증을 연결했다.

## 남은 문제와 다음 구현

1. 원시 selector를 아키텍처별 레지스터·상수·특수 레지스터로 해석하고 유효 범위를 검증한다.
2. EXEC 쓰기·VCC 연산·분기와 lane 상태의 상호작용을 명시적으로 확장한다. 현재는 입력 EXEC를 읽고 wrapping add를 수행하는 범위다.
3. GFX900 scalar move와 기존 GPU 네 규칙·SOP2 32개 규칙의 미지원 의미를 단계별로 연결한다. 별도 실행 프로파일은 scalar add/carry와 wave64 vector add이며 원래 encoding-only 프로파일은 계속 `unsupported`다.
4. 조건부 확장 워드, 분산 필드, 압축 인코딩과 가변 길이를 지원한다. 현재 프로파일은 고정폭이며 최대 256개 규칙을 담는다.
5. AMD 세대별 규칙을 구분하고, NVIDIA sm_80·Intel Xe는 고정 참고 소스를 기반으로 별도 slice를 만든다. 현재 이들의 바이너리 지원을 주장하지 않는다.
6. CFG·메모리 공간·kernel ABI·동기화·컨테이너 정보를 연결한 뒤 전체 커널의 동작 보존 재컴파일을 평가한다.
7. 초기 register layout과 eBPF ABI linking을 GPU lane bank·kernel ABI로 확장하고, `cspec` 거부 목록의 group·join·stack storage·allocation rule을 지원한다. 최초 SLA bound-add registry를 context·다른 ConstructTpl 연산으로 확장한다.
