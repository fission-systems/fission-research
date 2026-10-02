# FSL/FIR 연구 진행 현황

기준일: 2026-10-02. 이 문서는 설계 결정, 구현 위치, 기존 관찰 결과와 미지원 범위를 구분한다. 각 실행 단계의 검증 범위를 별도로 기록한다.

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

## 남은 문제와 다음 구현

1. 원시 selector를 아키텍처별 레지스터·상수·특수 레지스터로 해석하고 유효 범위를 검증한다.
2. EXEC 쓰기·VCC 연산·분기와 lane 상태의 상호작용을 명시적으로 확장한다. 현재는 입력 EXEC를 읽고 wrapping add를 수행하는 범위다.
3. GFX900 scalar move와 기존 GPU 네 규칙·SOP2 32개 규칙의 미지원 의미를 단계별로 연결한다. 별도 실행 프로파일은 scalar add/carry와 wave64 vector add이며 원래 encoding-only 프로파일은 계속 `unsupported`다.
4. 조건부 확장 워드, 분산 필드, 압축 인코딩과 가변 길이를 지원한다. 현재 프로파일은 고정폭이며 최대 256개 규칙을 담는다.
5. AMD 세대별 규칙을 구분하고, NVIDIA sm_80·Intel Xe는 고정 참고 소스를 기반으로 별도 slice를 만든다. 현재 이들의 바이너리 지원을 주장하지 않는다.
6. CFG·메모리 공간·kernel ABI·동기화·컨테이너 정보를 연결한 뒤 전체 커널의 동작 보존 재컴파일을 평가한다.
7. FSL register layout과 ABI register linking을 구현하고, `cspec` 거부 목록에서 group·join·stack storage·allocation rule을 확장한다. 이후 SLA decision/context/ConstructTpl을 explicit unsupported registry와 함께 직접 이관한다.
