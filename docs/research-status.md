# FSL/FIR 연구 진행 현황

기준일: 2026-10-01. 이 문서는 설계 결정, 구현 위치, 기존 관찰 결과와 미지원 범위를 구분한다. 2026-10-01 재현·SOP2 확장 작업에서 아래 범위의 실험을 다시 실행했다.

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
- GPU `unsupported` 의미의 평가기·C/Rust 출력·JIT·AOT 거부와 상태 불변을 확인했다. GPU 실행 의미를 구현한 것은 아니다.
- 연구 CI는 기존 artifact 재현과 SOP2/FIR 검증을 별도 job으로 실행한다. 원격 실행 결과는 GitHub Actions에서 확인한다.

자세한 범위·출처·해시는 [SOP2 실험](../experiments/gpu/gfx900-sop2/README.md), 재현 방법은 [자동 재현](reproduction.md)을 참조한다. LLVM opcode 참고 자료와 LLVM 실행 oracle은 계보를 공유하므로, 그 일치만으로 vendor 명세 독립 검증이나 GPU 실행 동치를 주장하지 않는다.

## 남은 문제와 다음 구현

1. 원시 selector를 아키텍처별 레지스터·상수·특수 레지스터로 해석하고 유효 범위를 검증한다.
2. register read/write, 플래그, EXEC 및 lane 상태를 단일 FIR의 명시적 효과로 추가한다.
3. GFX900 scalar move와 EXEC 기반 vector add부터 기준 상태 모델을 연결한다. 현재 기존 GPU 네 규칙과 새 SOP2 32개 규칙의 실행 의미는 모두 `unsupported`다.
4. 조건부 확장 워드, 분산 필드, 압축 인코딩과 가변 길이를 지원한다. 현재 프로파일은 고정폭이며 최대 256개 규칙을 담는다.
5. AMD 세대별 규칙을 구분하고, NVIDIA sm_80·Intel Xe는 고정 참고 소스를 기반으로 별도 slice를 만든다. 현재 이들의 바이너리 지원을 주장하지 않는다.
6. CFG·메모리 공간·kernel ABI·동기화·컨테이너 정보를 연결한 뒤 전체 커널의 동작 보존 재컴파일을 평가한다.
