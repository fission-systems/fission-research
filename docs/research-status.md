# FSL/FIR 연구 진행 현황

기준일: 2026-10-04. 이 문서는 설계 결정, 구현 위치, 기존 관찰 결과와 미지원 범위를 구분한다. 각 실행 단계의 검증 범위를 별도로 기록한다.

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
| [`2107f6295`](https://github.com/fission-systems/Fission/commit/2107f6295b8b891301a6aeb6652b5a9c749825b3) | `.fslc` v6 typed block·즉시값·비교·분기와 비순환 정수/스택 reference/C/Rust 실행 |
| [`7f7b22a34`](https://github.com/fission-systems/Fission/commit/7f7b22a344851aa6a5abcd3738fac979202f20eb) | `.fslc` v7 정수 확장·절단과 비순환 scalar register/flag CFG reference/C/Rust 실행 |
| [`16f84f47e`](https://github.com/fission-systems/Fission/commit/16f84f47e0cb53278fddde2522dfbe581fce5ddf) | `.fslseq` v1 순차 FIR instance 상태 전달·byte origin과 reference/C/Rust 실행 |

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

## 구조 FIR 실행 — 2026-10-04

Fission `2107f6295`는 같은 값/연산 테이블에 `FirBlock`의 op 범위·block parameter와 return/branch/conditional terminator를 연결한다. 즉시값과 equality/unsigned-less/signed-less 비교를 자체 FIR로 정의했다. Block 내부 값은 지역 정의와 parameter만 참조하며 edge의 arity·정확한 타입을 검사한다. Source/package/reference/output 경계가 같은 검증을 사용한다. `.fslc` v6에 구조를 저장하고 v1–v5 package byte layout은 유지한다.

첫 backend 범위는 비순환 정수/스택 semantic-body CFG다. Join과 모든 return의 stack delta는 같아야 한다. 모든 syntactic path의 최악 depth를 preflight하며 선택된 successor만 실행한다. 실행하지 않는 path도 capacity 전제를 높일 수 있고, 이 실패 status는 guest trap이 아니다. Cyclic CFG·unequal-delta join은 구조를 보존하지만 실행과 C/Rust 출력은 거부한다. 이 v6 단계에서는 GPU/register/wave/native lift backend도 control body를 거부했다. 후속 v7 단계의 scalar register CFG 지원은 아래에 기록한다.

[실험 기록](../experiments/fir/structured-control/README.md): 16개 프로파일 / 2,048개 독립·reference 상태 / 8,192개 C/Rust O0/O2 비교가 통과했다. 별도 65,536개 input oracle, binary compatibility·scope/type/refusal 및 native CLI 검사를 포함한다. Rust 전체 nextest 43개가 serial 실행에서 통과했고 skip/leaky는 0이다. 병렬 실행에서는 한 leaky classification이 관찰되어 serial gate를 재실행했다. Formatting과 warning-denied Clippy, Python 22개 검사와 기존 artifact 재현이 통과했다.

CI는 같은 compiler commit으로 control gate와 package/output hash·CLI oracle 재현을 수행한다. 현재는 자체 작성한 semantic-body fixture 증거다. 실제 binary function lifting, loops 실행, memory/exception/call, GPU divergence와 nested domain region, 구조 FIR native JIT/AOT는 미지원이다. 이후 단계의 확장·절단과 register-state CFG 검증은 아래 기록을 참조한다. 여러 명령 연결은 아직 미지원이다.

## 정수 확장·절단과 register-state CFG — 2026-10-04

Fission `7f7b22a34`는 `IntConvert`의 zero extension·sign extension·truncation을 단일 FIR에 추가했다. 입력/출력은 1..64비트이며 확장은 엄격히 더 넓게, 절단은 더 좁게 한다. 부호는 일치해야 하며 zext는 unsigned, sext는 signed만 허용한다. 새 op를 쓸 때 `.fslc` v7을 선택하고 v1–v6 byte layout은 유지한다. 기존 v6 package와 FIR/C/Rust 해시가 동일하게 재현됐다.

같은 block graph를 scalar register/flag reference와 C/Rust가 실행한다. 선택된 block만 쓰기 효과를 수행하고 join의 읽기는 그 경로의 선행 쓰기를 관찰한다. edge는 SSA 인자를 동시에 전달하며 register/flag 상태는 하나의 순서 있는 mutable runtime context로 유지한다. First-class domain state/effect SSA, memory token이나 GPU lane join을 구현한 것은 아니다. Narrow write는 logical slot 전체를 결과 bit pattern으로 교체한다. Byte-layout adapter의 exact-width·disjoint-binding 제약은 유지되므로 mixed-width fixture를 그 adapter의 검증으로 세지 않는다.

[실험과 검증 기록](../experiments/fir/register-control/README.md):

- 변환 프로파일 24개, reference/별도 widened oracle 3,072개, C/Rust O0/O2 12,288회 비교.
- Register CFG는 256 input × 27 alias 배치의 6,912개 정상 상태와 거부 8개, 재컴파일 27,680회 비교. 별도 exhaustive reference gate도 실행했다.
- 자체 구성한 32/64비트 carry CFG는 reference/oracle 2,048개와 source ABI 거부 12개, 재컴파일 8,240회 비교. 실제 GPU CFG를 복원한 증거는 아니다.
- 이번 단계의 새 C/Rust 비교 합계 48,208회가 통과했다. Rust 전체 48개, Python 24개, formatting과 warning-denied Clippy가 통과했다. 기존 carry/wave/SLA/layout/library와 역사적 artifact 재현도 통과했다.
- `register_fir_reproduce.py`는 source·803-byte package·3 output 해시를 검사하고 native CLI 정상 상태 44개와 거부 3개를 독립 계산과 비교한다. CI가 고정 compiler commit으로 같은 gate를 실행한다.

모든 syntactic path의 raw field·selector·flag 전제를 효과 전 검사한다. Untaken branch도 전제에 포함하며 거부 시 상태를 보존한다. 이 preflight는 guest fault semantics가 아니다. Cyclic graph는 저장·진단할 수 있지만 실행/source backend는 거부한다. **검증은 자체 작성 명세 기반이며, 루프 실행·GPU CFG·메모리·실제 binary function lifting은 아직 미지원이다.** 이후의 순차 instruction body 상태·origin 연결은 아래에 기록한다.

## 순차 명령 상태·origin 연결 — 2026-10-04

Native 구현은 Fission [`16f84f47e`](https://github.com/fission-systems/Fission/commit/16f84f47e0cb53278fddde2522dfbe581fce5ddf)다.

`FirSequence`는 하나의 immutable `.fslc` body pool과 instruction instance를 연결한다. 각 instance는 canonical instruction index, 명령별 주소·입력 window 내 offset·byte length·원본 bytes/fields를 보존한다. Input-window/package SHA-256과 body의 spec evidence를 통해 출처를 연결한다. 값 ID는 body invocation 내부 범위이고 순서 있는 logical register/flag 상태만 다음 instance에 전달한다. 별도 IR을 추가하거나 op를 평탄화·복제하지 않는다.

`.fslseq` v1은 기존 `.fslc`와 명시한 input window를 담는 96-byte header의 실행 계획이다. 로딩 시 길이·EOF·해시를 확인하고 constructor로 명령 선택과 origin을 다시 유도한다. 기존 `.fslc` byte layout과 이전 잠금 artifact는 유지된다. Base address와 exact bank ABI는 caller supplied이고, input hash는 whole-file hash가 아니다. Package hash도 원본 `.fsl` source hash가 아니며 authenticity나 주소 매핑의 증명이 아니다.

선택된 모든 scalar body와 selector를 효과 전 검증한다. Reference/C/Rust wrapper는 임시 상태에 순차 실행하고 전부 성공했을 때만 원래 상태에 commit한다. 이 transaction은 guest fault ordering·CPU atomic operation·concurrent memory semantics가 아니다. 현재 primitive는 dynamic guest fault가 없으며 late failure 경로를 guest exception 지원 증거로 세지 않는다. Register·flag bank는 각각 최대 4,096 slot이고 exact size가 계약이다. Empty bank도 사용하지 않는 body에서 명시적으로 허용한다.

[실험/lock](../experiments/fir/sequence/README.md):

- 자체 작성한 두 scalar 명령 window의 carry 전달은 reference/u128 oracle 1,060개에서 일치했다.
- Scalar sequence의 5개 폭 × 2개 alias 배치 × 132행은 C/Rust O0/O2 5,280회 비교가 통과했다. 32비트 이외의 폭은 synthetic primitive 검사다.
- 세 register CFG body 연결의 256개 정상·3개 실패 입력은 1,036회 비교, 명시적 zero bank 2개는 8회 비교가 통과했다. 새 재컴파일 비교 합계는 6,324회다.
- Rust 전체 53개, Python 27개, formatting과 warning-denied Clippy가 통과했다. Envelope 절단·해시/bytes 변조·주소 overflow·늦은 unsupported word·bank/selector·cycle/stack 거부와 4,096-step 한계를 포함한다. Endianness transport도 합성 계약으로 확인했으며 GFX900 big endian 지원을 뜻하지 않는다.
- 재현기는 7,687-byte scalar envelope와 911-byte register envelope를 Python에서 독립 확인하고 6개 출력 artifact, CLI 정상 상태 112개·실패 4개를 비교한다. 이전 structure/conversion hash와 historical/SLA/layout/ABI/library artifact도 동일하게 재현됐다.

이 단계는 명시적으로 공급한 window의 **순차 실행**이다. FIR block terminator는 instruction body 안에서만 분기하며 return 후 다음 word를 실행한다. Guest PC·명령 사이 branch target·함수 entry/return을 복원한 것이 아니다. **검증은 자체 작성 명세/window 기반이고, 루프 실행·GPU CFG·메모리·실제 binary function lifting은 여전히 미지원이다.** 다음은 inter-instruction branch/PC 계약과 loader-backed byte origin을 연결하는 단계다. Sequence native Cranelift JIT/AOT·CUDA/PTX, variable-width/mixed profile도 미지원이다.

## 자체 x86 scalar window와 FIR 출력 — 2026-10-11

Native 구현은 Fission [`55905c397`](https://github.com/fission-systems/Fission/commit/55905c3975bc362d4121d0e11b7f60248fc555b9)에 반영하고 실험 브랜치에 푸시했다.
사용자 요청에 따라 x86 16/32/64비트를 자체 명세로 이관하는 경로를 시작했다.
초기 연결에 사용했던 `iced-x86`는 제거했다. Native manifest/lock에는 외부 decoder
의존성을 추가하지 않으며 기존 workspace loader를 optional `x86` feature로 사용한다.
SHA-256/Cranelift와 loader의 기존 파일 파싱 의존성까지 제거했다는 뜻은 아니다.

[실험과 재현 계약](../experiments/x86/README.md):

- Own `.fslx` 46개 규칙과 `.fsl` 63개 canonical FIR body를 `.fslxc` binary로 컴파일했다.
  Opcode/prefix/ModRM/SIB/immediate decoding은 Fission 소유이며 SLEIGH/P-code를 실행하지 않는다.
- 고정 x86 자산 78개를 해시로 기록했다. `ia.sinc`의 register prefix에서 legacy 1,380개,
  long-mode 1,440개 view를 이관하고 native parser로 읽었다. 다른 constructor/cspec/pspec/context는
  inventoried 상태이며 전체 자산을 자동 변환한 것은 아니다. Scalar 의미는 참고 자료를 바탕으로 작성했다.
- 기존 다른 AI의 generic Sub/And/Or/Xor 변경을 보존했다. 동일 FIR에 bounded little-endian
  scalar memory load를 추가해 near RET의 stack read·SP 증가·exit PC를 표현했다.
- Raw 16/32/64 window와 Clang이 생성한 ELF 32/64 span 두 개에서 FIR/C/Rust 15개 출력을 만들었다.
  공급한 상태 5개는 FIR reference 실행에서 RAX=12와 mode별 RET 결과를 냈다.
- C 5개와 Rust 5개 source는 warnings-as-errors로 컴파일했다. Native x86 feature build 및
  Clippy가 통과했다. 이번 로컬 작업에서 기존 unit suite는 재실행하지 않았다.
- `x86_reproduce.py`는 package·input·output lock을 비교하고 5개 reference 실행을 재생성한다.
  이는 self-derived artifact 재현이며 독립 ISA oracle 또는 생성된 코드의 runtime 동치 검증이 아니다.

새 경로는 caller가 지정한 file-backed executable span만 읽으며 source signature·ABI·locals를
복원하지 않는다. Direct branch는 window 내부 instruction start로 제한하며 예산으로 재방문을
제한한다. Stack memory는 readonly flat byte window이고 16비트 SS.base는 0이라는 계약이다.
Wrapper 실패 rollback은 CPU fault/atomicity 모델이 아니다. Memory operands/store, CALL/callee ABI,
indirect control, byte/high-byte register, SIMD/x87/AVX, full cspec/pspec/context는 아직 미지원이다.
실제 x86 hardware 실행과 full corpus coverage를 측정하지 않았으므로 전체 x86 디컴파일 완료로
주장하지 않는다. 이전 단계의 “메모리·함수 lifting 미지원” 기록은 해당 단계의 범위를 뜻하며,
현재 추가된 기능은 위의 명시적인 x86 window / RET memory 범위에 한정된다.

## 2026-10-11 — readonly x86 memory와 입력 근거 / 독립 실행 비교

[후속 실험](../experiments/x86/memory/README.md)은 기본 cdecl32 ADD와 SysV AMD64
pointer ADD/XOR의 세 compiled ELF를 고정했다. 46개 encoding rule을 유지하고,
optional FSL body pool을 63→126개로 늘렸다. Generic RegRm memory source가 기존
LEA 주소 reader와 canonical memory/read/arithmetic FIR body를 사용한다. 외부
instruction decoder와 새 dependency는 없으며 Cargo.lock 변경도 없다.

Canonical FIR의 derived abstract analysis가 entry ESP+4/+8와 entry RDI+0/+8 읽기
의존성을 추적하고 원본 bytes/address/FIR operation/width를 남긴다. Convention은
unselected, source prototype/type/argument count는 unknown이다. Unknown branch는
거부한다. 전체 ABI 복구로 해석하지 않는다.

로컬 관찰:

- Full x86-feature nextest 61 passed / 0 skipped; 새 기계적 검사 3개 포함.
- 세 ELF 768 FIR 상태가 independent arithmetic/state 계산과 일치.
- 동일 FIR의 C/Rust O0/O2 executable 비교 3,072회 통과.
- 원본 64-bit ADD/XOR bytes의 Rosetta 실행 512회: result와 defined arithmetic flags 일치.
  ARM64 macOS에서 원본 i386 실행은 하지 않았다. Linux x86 CI는 세 span을 실행하도록 연결했다.
- 실제 compiled SLA + canonical P-code evaluator 비교: ADD 각각 AF 96/256 차이,
  다른 flags/registers/exit 차이 0. XOR undefined AF 256개는 제외하며 나머지 차이 0.
- 초기 63-body artifact 재현도 15개 출력 / reference 실행 5개 / source compile 10개 유지.
- FSL strict Clippy/format 통과. Baseline build와 CI-equivalent Clippy 통과.
  Unqualified strict baseline Clippy는 기존 solver/emulator style/complexity lint에서 실패;
  해당 libraries 변경은 없다.

AF 차이는 기존 x86 `resultflags`의 AF 미구현 사례이며 P-code 표현력 한계는 아니다.
FIR의 richer evidence가 분석 정확도를 높이는지에 대한 controlled ablation은 아직
수행하지 않았다. [정확성 평가 설계](fir-evidence-and-accuracy.md)는 현재와 계획을 구분한다.

Native compiler: `dc665c7c9341e76587ceb968849f604083245949`, 실험 브랜치만 변경.
Research CI는 이 compiler commit을 고정해 package/output/evidence 재현, C/Rust 실행,
original32/64 adapters와 실제 SLA baseline 비교를 실행한다. CI 결과는 각 실행의
artifact와 exact commit에서 확인해야 한다. 로컬 보고서는 Rosetta 측정이며 Linux
native 실행으로 이름을 바꾸지 않는다.

추가 CI 관찰: [Linux 실행 38100633006](https://github.com/fission-systems/fission-research/actions/runs/38100633006)의
x86 semantic-comparison artifact를 보관했다. Compiler `dc665c7c9`, Ubuntu clang 18.1.3,
Rust 1.98.1, Linux x86_64에서 original32/64 bytes 각각 256회, 총 768회 result/defined
flags 비교가 통과했다. FIR 상태 768개와 C/Rust 3,072회도 통과하고, legacy ADD의 AF
차이 96개씩 / XOR AF 256개 제외가 재현됐다. 이 artifact의 통과와 전체 workflow의
상태는 구분한다. [고정 Linux 보고서](../experiments/x86/memory/validation-linux-ci-38100633006.json).

Memory는 readonly flat window이고 segment bases=0이다. Store/stack frame/CALL,
ABI allocation, general guest CFG joins, faults/ordering 및 전체 x86 자산은 아직 미지원이다.
이번 세 leaf 관찰은 전체 함수 동치 증명이나 일반 디컴파일 품질 측정이 아니다.

## 2026-10-11 — ordered memory store와 실제 stack frame

[Stateful x86 실험](../experiments/x86/stateful/README.md)은 generic `memory.store.le`
canonical FIR 효과와 명시적인 readonly/mutable window 권한을 추가했다. `.fslc` v11,
op tag 22이며 이전 package/artifact는 유지한다. Decoder library/dependency/Cargo.lock
변경은 없다. 48 rules / 141 bodies: MOV register→memory 9개와 unprefixed register
PUSH/POP 6개를 readonly pool에 추가했다. Stack 효과도 FSL body가 소유한다.
구현 pin은 `8211a05610204670a4f5542298d8a4e0d9fe5983`이다. 16비트 stack은 현대
IA-32 기준이며 8086 PUSH SP를 포함하지 않는다. Stack address width=mode/SS.base=0
계약과 별도 Intel SDM 출처·PDF hash를 FSL evidence에 남겼다.

`execute_decoded_memory`와 `X86Program::execute_mut`는 state/memory를 성공 때만
commit한다. Mutable window는 최대 1 MiB. C/Rust 출력은 동일 길이 disjoint scratch를
받고 실패 시 caller state/memory/exit를 보존한다. Scratch는 unspecified이며 이 wrapper
transaction은 CPU fault ordering/atomicity를 뜻하지 않는다.

Derived memory analysis는 exact same-address/same-width store forwarding과 같은 modular
root의 disjoint range를 추적한다. Partial/unknown alias는 external-read와 possible-store
의존성을 함께 보존하는 overapproximation이다. Frame64의 RBP 후보가 남을 수 있으며
임의 pointer/stack disjointness나 source prototype을 가정하지 않는다.

로컬 관찰:

- Full x86-feature nextest 66 passed / 0 skipped. 추가 focused guard/alias 검사는 별도 실행.
- Clang/LLD 22.1.8의 O0 cdecl32 EBP frame, O0 AMD64 pointer spill/reload, O2 AMD64 store:
  768 FIR 상태가 independent arithmetic/register/160-byte memory 계산과 일치.
- C/Rust O0/O2: success 3,072 + 실제 write 이후 budget failure rollback 3,072 = 6,144회.
- Rosetta64 original-byte execution 512회: result, six defined flags, RBP 보존, SP balance,
  외부 two-word memory 효과 일치. Original32는 로컬에서 미실행이며 Linux CI에 연결한다.
- 실제 SLA/canonical evaluator: 각 fixture 256회 GPR/exit/전체 modeled memory 차이 0;
  AF 차이는 각각 96개, 다른 flags 차이 0. Existing specification 누락이지 IR 우위 증거는 아니다.
- Strict FSL Clippy는 feature on/off에서 통과. Baseline은 CI-equivalent style/complexity
  허용 조건에서 통과했다. Existing library lint debt는 변경하지 않는다.

원격 관찰: [Fission CI 38130023456](https://github.com/fission-systems/Fission/actions/runs/38130023456),
native `8211a0561` success. [Research CI 38130097795](https://github.com/fission-systems/fission-research/actions/runs/38130097795),
연구 `c718c31` success. 후자는 original32/64 bytes 총 768회와 FIR 768 상태,
C/Rust 6,144회 및 같은 baseline 차이를 관찰했다. Linux 보고서는 실험 폴더에 보관했다.
연구 `623a806`은 oracle64의 RBP operand constraint/call alignment 및 source/executable
hash를 보완하고 local 검사를 다시 통과했다.
[CI 38130695902](https://github.com/fission-systems/fission-research/actions/runs/38130695902)도
연구 `623a806`에서 success이며 보완 후 Linux original 768회, FIR 768 상태,
C/Rust 6,144회와 같은 baseline 차이를 보관했다. Source lock/module/adapter executable
hash를 확인했으며 두 CI 스냅샷을 구분한다.

Memory immediate는 displacement와 literal의 별도 binding이 없어 거부한다. CALL/LEAVE,
일반 ABI allocation, recovered CFG merge/loop 및 faults/MMU/ordering는 아직 미지원이다.
실험은 세 supplied spans에 한정되며 full x86 migration이나 whole-function equivalence
증명이 아니다. Hardware의 all-register/stack memory snapshot 비교도 아직 없다.

## 남은 문제와 다음 구현

1. 원시 selector를 아키텍처별 레지스터·상수·특수 레지스터로 해석하고 유효 범위를 검증한다.
2. EXEC 쓰기·VCC 연산·분기와 lane 상태의 상호작용을 명시적으로 확장한다. 현재는 입력 EXEC를 읽고 wrapping add를 수행하는 범위다.
3. GFX900 scalar move와 기존 GPU 네 규칙·SOP2 32개 규칙의 미지원 의미를 단계별로 연결한다. 별도 실행 프로파일은 scalar add/carry와 wave64 vector add이며 원래 encoding-only 프로파일은 계속 `unsupported`다.
4. 조건부 확장 워드, 분산 필드, 압축 인코딩과 가변 길이를 지원한다. 현재 프로파일은 고정폭이며 최대 256개 규칙을 담는다.
5. AMD 세대별 규칙을 구분하고, NVIDIA sm_80·Intel Xe는 고정 참고 소스를 기반으로 별도 slice를 만든다. 현재 이들의 바이너리 지원을 주장하지 않는다.
6. CFG·메모리 공간·kernel ABI·동기화·컨테이너 정보를 연결한 뒤 전체 커널의 동작 보존 재컴파일을 평가한다.
7. 초기 register layout과 eBPF ABI linking을 GPU lane bank·kernel ABI로 확장하고, `cspec` 거부 목록의 group·join·stack storage·allocation rule을 지원한다. 최초 SLA bound-add registry를 context·다른 ConstructTpl 연산으로 확장한다.

## 2026-10-11 — independent x86 displacement/literal bindings

[New optional v2 pool](../experiments/x86/immediate/README.md) preserves old v1
packages and adds a seventh normalized operand field. 48 rules / 150 FIR bodies
include nine authored MOV immediate-store bodies. Canonical FIR remains v11;
no new semantic primitive, runtime decoder library or architecture arithmetic
executor was added. The shared operand/package binding changed, so this is not
claimed as entirely specification-only expansion.

Three actual Clang O2 AMD64 ELF spans write 16/32/64-bit literals at RDI+8 after
computing the old two-word sum. Local FIR 768 states, C/Rust O0/O2 successful and
rollback comparisons 6,144, and Rosetta64 original-byte cases 768 agree. The
actual SLA/canonical evaluator agrees on GPR/exit/160-byte memory and five flags;
AF differs96/256 per fixture due to the reference spec omission. These are
bounded observables, not a whole-function equivalence proof or IR superiority.

Native tests cover malformed/downgraded schemas, independent values, SIB,
IP-relative addressing, negative displacement, 16/32/64 modes, prefixes and late
rollback. Python tests cover partial-store oracle and historical generation.
Original packages/projections and stateful validation remain reproducible.
CALL/callee ABI, memory ALU destinations, byte/high-byte registers, guest fault
model and complete recovered CFG/type/x86 migration remain incomplete.

Native continuation commit: `867dae1fa0f278e87f6dc3e8244ca4fd307cced5` on the experimental branch.
Full x86 nextest **71 passed/0 skipped**, Python **29**, strict FSL Clippy
with/without x86 and formatting passed. Native product main is unchanged.

## 2026-10-11 — checked source output backend

Native `cc02f3be760e43153ccb212d3640d45905e3b8c6` connects existing C/Rust renderers through borrowed canonical
FIR `OutputBackend` plans. In-process registry, explicit dialect/runtime/memory/
context admission, structured refusals, requirements and artifact bundles are
implemented. x86 symbol origins retain addresses/raw bytes/offset/length.
Statement source maps and dynamic plugins are not implemented. Existing CUDA/PTX
outputs are not registered; Go/Python/Java support remains future work.

Full x86 native suite: **77 passed / 0 skipped**. Six backend tests also passed
after adding offset/length assertions. Strict Clippy with/without x86 and fmt
passed; Python **31**. Six bundles reproduce unchanged source bytes and 18 new
metadata goldens; six standalone compilations and seven refusal checks pass.
Compilation and execution-equivalence fields in generated plans remain
`not-performed`; observed validations belong to separate reports.

[The maturity comparison](fsl-fir-maturity-comparison.md) identifies general
CALL/ABI/CFG/type recovery and full ISA coverage as the largest gap to the
existing product. No percentage maturity, speed or FIR accuracy superiority
is claimed. [Backend evidence](../experiments/output/backend-contract/README.md)
records the bounded regression and compiler pin: 768 FIR states, 6,144 C/Rust
success/rollback comparisons and 768 Rosetta original-byte cases passed again
with the clean native snapshot. The same legacy AF omission remains; no IR
superiority claim. Remote CI is checked separately.

## 2026-10-11 — Go output backend

Native `97366a84157afe163236a99e309fcd4fbfb8e2ae` registers Go 1.25 over the existing borrowed canonical FIR plans.
Shared contract admission supports integer/stack, acyclic scalar CFG, wave
mask/broadcast and bound x86 windows. No new semantic IR, package version or
external decoder/library dependency. Generated Go uses uint64 plus width masks,
simultaneous block parameter assignment and explicit ordered effects. x86 uses
private snapshots and success-only state/memory/exit commit. Safe Go output-bank
aliases and exit-pointer aliases refuse; concurrent access and unsafe host
aliases remain outside the contract. Heap exhaustion is not a guest status.

Native full x86 nextest **80 passed / 0 skipped**, strict Clippy on/off and fmt
passed; research Python **35**. Six locked actual frame/store/immediate ELF spans:
**6,144 Go** default/optimization-disabled full modeled state/byte/rollback
comparisons and **12,288 C/Rust** O0/O2 comparisons on the same inputs passed.
**18,426 Go** synthetic domain comparisons cover widths/carry, register alias,
stack/branch/conversion and VGPR/SGPR broadcast wave64. **12** Linux amd64/386
host archive compilations are compile-only evidence. Six windows and ten domain
source artifacts are locked. Previous C/Rust plans/sources and refusal checks
reproduce; the currently unregistered backend check now uses Python. Historical
Go refusal was observed at the previous pin and is not rewritten.

[Go experiment](../experiments/output/go-backend/README.md) records clean local
provenance and CI reproduction. This gate does not execute original machine
bytes; the separate prior original/FIR/SLA gates remain in CI. Source prototypes,
complete ABI/CFG/x86 migration, semantic-body loops, guest faults/concurrency,
GPU hardware, Go FirSequence and full Python/JVM/WASM frontend/output support
are not established. No performance or IR-superiority claim.

## 2026-10-16 — asset-independent owned ELF route

Goal clarified: the eventual complete decompilation route must use FSL/FIR and
require no SLEIGH/SLA. Native `bbf6a1992bba2a32aa4a0499ee59c03fdc76b222` adds `decompile-owned`, embedding the owned
x86 v2 rules/FIR and returning C/Rust/Go bundles with portable package, diagnostic
FIR, origins, build recipe and explicit route/validation reports. Unsupported
input refuses without fallback. Existing output bytes and contracts remain.

Found a hidden dependency in the previous file route: ELF architecture selection
queried Ghidra opinion/ldefs despite owned instruction semantics. New opt-in
LoaderPipeline/ELF policy validates raw machine/class/endian facts, leaves ABI
unselected and produces no legacy LoadSpec. Existing map/relocation/symbol code
is reused. Default product loader selection remains unchanged.

Local: nine source/package/FIR artifacts agree with existing locks and compile;
11 refusal checks pass from copied executable/inputs with empty resource roots.
This is not a local filesystem jail. FSL full x86 suite **82**, loader suite
**165**, Python **38**, strict FSL Clippy on/off and formatting passed. Loader
metadata and pipeline focused tests passed after the constant/error propagation
cleanup; downstream decompiler/CLI checks pass.

[Experiment and limits](../experiments/pipeline/owned-elf/README.md) describes the
new dedicated Linux source-only build and chroot/file-trace gate. Remote results
are tracked separately. General function discovery/CALL/ABI/CFG/type recovery,
full x86/other formats and whole Python/JVM/WASM methods remain incomplete. No
decompiler accuracy, speed or IR-superiority claim. Previous Go native CI
38141160429 and research CI38141467008 were rechecked and passed.
