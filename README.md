# Fission Research: FSL, FIR, and a semantic pattern corpus

이 저장소는 메인 Fission의 기능 개발 공간이 아니라, 여러 종류의 바이너리를 설명하고 의미를 복원하는 독립 연구 공간이다. 목표는 SLEIGH의 좋은 아이디어와 기존 `.slaspec` / `.sla` 생태계를 분석해 **FSL**(아키텍처·바이트코드 설명 언어), **FIR**(의미 보존 중간 표현), 그리고 출처가 추적되는 패턴 데이터베이스를 새로 설계하는 것이다.

현재는 형식과 경계를 측정하면서 작은 독립 프로토타입을 만든다. `Fission/`은 비교를 위한 읽기 전용 클론이고, 여기에 기능을 추가하지 않는다. Notion 원문과 메인 프로젝트의 증거 우선 지침은 [연구 컨텍스트 노트](docs/notion-fsl-fir-context.md)에 기록했다.

## 현재 방향과 구현 위치

### 연구 성숙도

| 항목 | 현재 구현 범위 |
|---|---|
| FSL 문법 / 컴파일러 | 실험 문법 / Rust 프로토타입; 초기 TOML 프로브와 구분 |
| FIR | 단일 의미 소유자 프로토타입; 실행 지원은 제한된 정수·스택 연산 |
| GFX900 디코드 | 네 명령의 고정폭 인코딩 slice |
| JVM 디코드 | `iadd` 한 opcode |
| GPU 실행 의미 | 미구현; 현재 FIR body는 `unsupported` |
| SLEIGH 대체 / Fission 통합 | 연구 목표; 실험 PR에서 개발 |
| 동작 보존 재컴파일 | 제한된 JVM 정수·스택 계약의 C·Rust 출력 |
| AI 평가 / semantic corpus 조회 | 계획·설계 단계 |

이 표의 지원 범위와 재현 결과는 [진행 현황](docs/research-status.md)에 기록한다. 새 ISA 규칙 수, 인코딩 검증, 실행 의미 검증은 별도로 보고한다.

2026-10-01 기준으로 **단일 FIR, 여러 출력 계층, 정확성·동작 보존 재컴파일 우선**을 채택한다. NIR/HIR 구분은 새 FIR 설계에 도입하지 않는다. 최종 목표는 Fission이 소유하는 FSL 명세·컴파일러·FIR로 SLEIGH 의존성을 제거하는 것이다.

실험 Rust 컴파일러 `fission-fsl`은 별도 Fission 브랜치 `codex/fsl-jvm-iadd-parity`의 [PR #176 — FSL/FIR 실험지원](https://github.com/fission-systems/Fission/pull/176)에서 개발한다. 이 연구 리포는 독립 Python 프로브, 역사적 명세·관찰 자료, 참고 소스 인벤토리와 연구 설계를 보관한다. Rust 컴파일러의 코드를 이 리포에 복제하지 않는다. 두 저장소의 현재 구현과 증거 범위는 [진행 현황](docs/research-status.md)에 정리했다.

| 경로 | 내용 |
|---|---|
| `tools/` | SLA·GPU ELF·AQL·FSL/FIR 독립 연구 프로브 |
| `specs/` | 이전 TOML 기반 FSL 실험 명세; 정식 Rust 문법과 구분 |
| `experiments/` | 자체 작성 샘플, 작은 바이너리 fixture, 관찰 결과와 재현 방법 |
| `data/` | 구조 인벤토리와 역사적 JSON 패턴 자료 |
| `docs/`, `notes/` | 설계, 출처 추적, 결과·미지원 범위 |
| `Vendor/` | 참고용 클론; Git에는 인덱스와 고정 버전·해시만 포함 |

비교용 Fission 클론이 필요한 경우:

```sh
git clone https://github.com/fission-systems/Fission.git Fission
git -C Fission checkout --detach 96fc71f75cecdee305faf9497561c577a8955468
```

이 커밋은 기존 SLA 연구 자료의 비교 스냅샷이다. 최신 Rust 컴파일러 실험은 위 PR에서 확인한다. GPU 참고 소스 복원 방법은 [Vendor 안내](Vendor/README.md)에 있다. 프로브는 Python 3.11 이상을 기준으로 하며, 실험 객체 재생성에는 각 README에 기록한 LLVM 도구가 필요하다.

## 핵심 가설

AI 기반 분석기의 경쟁력은 모델만으로 정해지지 않는다. 검증된 인코딩 규칙, 연산 의미, 플랫폼별 효과, 버전 정보, 그리고 각 지식의 출처·확실성을 쿼리 가능한 형태로 제공하면 모델이 더 정확하게 디코드하고 설명할 수 있다. 이 가설은 나중에 동일한 모델·바이너리에서 패턴 지식 사용 여부를 비교해 검증한다.

## 연구 축

- **FSL**: 비트 패턴, 컨텍스트, 피연산자, 표시 형식, 의미 블록, 아키텍처 제약을 기술하고 패키지로 컴파일한다.
- **FIR**: 의미·효과·provenance를 담는 정규 코어와, C/Rust 소스·분석 IR·그래프·AI 근거 패킷 같은 별도 projection을 구분한다. 각 projection의 보존 범위와 손실은 명시한다.
- **패턴 DB**: 디코드 패턴과 의미 템플릿에 아키텍처/버전 범위, 근거 출처, 검증 상태, 불확실성, 동치 관계를 연결한다.
- **프런트엔드**: 머신 ISA뿐 아니라 JVM 바이트코드, CPython 바이트코드, GPU 가상 ISA와 실제 GPU ISA를 별도 입력 계열로 다룬다.
- **평가**: 디코드 정확도, 의미 보존, 미지원 의미 감지, 라이선스/출처 재현성, AI 보조 분석 성능을 각각 측정한다.

## 시작 자료와 첫 실험

GPU용 FSL 확장을 위한 NVIDIA·AMD·Intel 참고 소스는 [`Vendor/`](Vendor/README.md)에 클론했다. 고정 커밋과 공식 AMD ISA XML 10개의 해시는 [`Vendor/references.lock.toml`](Vendor/references.lock.toml)에, 소스에서 확인한 요구사항과 다음 구현 순서는 [`docs/gpu-fsl-reference-design.md`](docs/gpu-fsl-reference-design.md)에 기록했다. 새 컴파일러는 텍스트 FSL과 바이너리 `.fslc`를 사용하며, 아래 TOML/JSON 실험 자료는 이전 프로브 형식이다.

`Fission/utils/sleigh-specs/`의 Ghidra 미러 소스와 컴파일된 SLA 스냅샷을 참고 자료로 조사한다. [`tools/sla_probe.py`](tools/sla_probe.py)는 `.sla`의 매직/버전/zlib 외피와 packed element 트리를 읽는다. GPU 경로는 [`docs/gpu-stack-research.md`](docs/gpu-stack-research.md)와 [`tools/gpu_elf_probe.py`](tools/gpu_elf_probe.py)에서 시작하며, LLVM으로 만든 AMDGPU ELF와 MessagePack 메타데이터 샘플을 [`experiments/gpu/amdgpu-gfx900/`](experiments/gpu/amdgpu-gfx900/)에 보관한다. 첫 FSL 원문 조각은 [`specs/gpu/amdgcn/gfx900-first.fsl`](specs/gpu/amdgcn/gfx900-first.fsl)이고, [`tools/fslc_probe.py`](tools/fslc_probe.py)가 이를 패키지로 컴파일한다. JVM 경로는 [`specs/vm/jvm-se26-iadd.fsl`](specs/vm/jvm-se26-iadd.fsl)의 단일 `iadd`를 사용해 무레지스터 프로파일과 8-bit fixed-width 디코드를 시도한다. [`tools/fsl_decode_probe.py`](tools/fsl_decode_probe.py)는 두 프로파일 계열이 공유하는 디코더이고, [`tools/fir_projection_probe.py`](tools/fir_projection_probe.py)는 하나의 JVM FIR 후보에서 여러 consumer 뷰를 만든다. 현재 단계와 구현 경계는 [`docs/fsl-first-compiler-slice.md`](docs/fsl-first-compiler-slice.md)에 있다. 다중 projection 설계와 실험은 [`docs/fir-multiple-projections.md`](docs/fir-multiple-projections.md)에 기록했다. HIP/HSA code object 선택에서 AQL dispatch와 Linux KFD queue setup까지 고정 소스에서 따라간 결과는 [`docs/amdgpu-runtime-trace.md`](docs/amdgpu-runtime-trace.md)에 있다. 독립 AQL packet probe는 [`tools/aql_dispatch_probe.py`](tools/aql_dispatch_probe.py)다.

초기 우선순위와 경계는 [`docs/research-architecture.md`](docs/research-architecture.md)를 본다. 초기에 모든 ISA를 지원하려고 하지 않고, 공통 디코드/의미 모델을 검증한 다음 서로 다른 도메인으로 확장한다.

## 자동 재현

`make test reproduce`는 고정 입력에서 기존 artifact 9개를 임시 디렉터리에 재생성하고 SHA-256을 비교한다. 준비 방법과 검증 범위는 [재현 문서](docs/reproduction.md)에 있다. GitHub Actions에서 같은 명령을 실행한다.

## 연구 원칙

1. 원본 `.slaspec`, `.sla`, 공식 문서, 자체 작성 규칙을 구분하고 해시·버전·라이선스를 기록한다.
2. `.sla`가 가진 사실과 소스에서 추론한 의미를 구분한다. 디코드 성공은 의미의 완전성을 뜻하지 않는다.
3. 모르는 의미를 임의로 일반 연산에 끼워 넣지 않고, 범위가 명시된 `unknown` 또는 `unsupported`로 보존한다.
4. 비교는 같은 입력과 같은 평가 기준에서 수행한다. 아키텍처별 결과와 기능별 미지원 항목을 평균 점수 하나로 감추지 않는다.
5. Fission 코드는 비교 대상이다. 새 도구는 이 저장소 안에서 독립적으로 구현하고, 가져온 데이터와 알고리즘의 출처를 기록한다.

## 현재 상태

- [x] 연구 범위를 메인 Fission 작업과 분리
- [x] 기존 SLA 외피 및 packed 트리 형식의 예비 분석
- [x] 독립 SLA 프로브로 133개 전부 파싱하고 구조 인벤토리 생성
- [x] GFX900 ISA 조각과 AMDGPU ELF kernel object 정적 probe 생성
- [x] ELF64 AMDGPU 컨테이너/심볼/note와 MessagePack metadata 독립 probe 작성
- [x] 첫 확장 도메인 실험으로 GPU 정적 경로를 선택 (초기 기준 대상은 AMDGPU GFX900)
- [x] HIP/HSA runtime부터 Linux AMDKFD queue setup과 사용자 공간 AQL dispatch까지 소스 경로 추적
- [x] 64-byte HSA AQL kernel-dispatch packet 독립 parser와 명시적 synthetic fixture 작성
- [ ] v4 packed 태그 전체를 공식 형식 상수와 대조해 스키마화
- [ ] FSL 최소 문법 초안
- [x] 제한형 FSL/TOML 원문 → 정적 검증된 패턴 패키지 → 데이터 기반 GFX900 디코드 수직 단면
- [x] GFX900 register class와 source-selector 범위/예외를 선언형으로 기술하고 generic decoder에서 사용
- [ ] bitfield 조합·상대 주소·확장 워드까지 FSL primitive를 넓혀 새로운 opcode에서 코드 수정 제거
- [x] 패턴 DB 스키마 초안
- [x] ROCclr/ROCr 소스에서 loaded kernel symbol → opaque kernel-object → AQL packet 경로를 추적하고 정적 GFX900 descriptor/argument metadata와 provenance 연결
- [ ] 실제 GPU에서 loaded address와 AQL packet을 캡처해 source-traced mapping 검증
- [x] FSL-pattern-profile 기반 GFX900 4-instruction decoder 첫 조각과 LLVM encoding/disassembly 교차 참조
- [x] JVM SE 26 `iadd` 한 opcode의 FSL profile, 8-bit fixed-width decode, FIR multi-projection 후보
- [ ] FSL 원문 문법/컴파일러 및 확장 워드까지 포함한 GFX9 decoder
- [ ] JVM·CPython 바이트코드 도메인에 같은 provenance/IR 접근 적용
