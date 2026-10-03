# FSL / FIR 연구 구조

## 무엇을 다시 만드는가

SLEIGH는 명령어 비트열을 디코드하고 이를 P-code 의미로 바꾸는 언어와 컴파일 산출물을 제공한다. 연구 목표는 문법을 그대로 복제하는 데서 끝나지 않는다. FSL은 여러 종류의 인코딩과 실행 도메인을 기술하는 저작·컴파일 언어이고, FIR은 그 의미를 분석기와 AI가 조회하고 변환할 수 있게 보존하는 표현이어야 한다. [공식 Sleigh 설명](https://ghidra.re/ghidra_docs/languages/html/sleigh.html)은 SLEIGH의 패턴/의미 기술을, [언어 인덱스](https://ghidra.re/ghidra_docs/languages/index.html)는 언어 정의 구성을 설명한다.

### FSL 언어와 컴파일러

초기 공통 코어가 다룰 후보:

- 바이트/비트 필드와 endian, 정렬, 가변 길이 인코딩
- 컨텍스트 조건, 모드, 접두어, 상태 의존성
- 디코드 패턴의 우선순위와 겹침/모호성 검사
- 피연산자 추출, 주소 지정, pretty-print 템플릿
- 의미 블록, 재사용 가능한 매크로, 예외·제어 흐름 효과
- 프로파일 버전, 기능(feature), ABI/호출 규약 연결

CPU 명령어와 JVM 명령어는 공통 패턴 컴파일러를 일부 공유할 수 있지만 같은 실행 모델은 아니다. [JVM class-file 명세](https://docs.oracle.com/javase/specs/jvms/se26/html/jvms-4.html)는 상수 풀과 메서드 코드/예외 메타데이터를 정의하고, [JVM 명령어 명세](https://docs.oracle.com/javase/specs/jvms/se26/html/jvms-6.html)는 operand stack과 예외 효과를 포함한다. [CPython `dis` 문서](https://docs.python.org/3/library/dis.html)는 bytecode가 CPython 구현 세부사항이고 버전마다 바뀔 수 있다고 명시한다. Python의 스택 기반 평가와 런타임 객체 효과를 CPU 레지스터 명령으로 억지 환원하지 않는다. GPU는 [PTX 가상 ISA](https://docs.nvidia.com/cuda/cuda-programming-guide/01-introduction/cuda-platform.html)와 [NVIDIA cubin/SASS](https://docs.nvidia.com/cuda/cuda-binary-utilities/), [AMD의 기계 판독형 ISA 정의](https://gpuopen.com/machine-readable-isa/)를 서로 다른 층으로 기록하고 연결한다.

### FIR 의미 층

FIR의 초안은 세부 도메인을 보존하는 typed operation과 effect를 가진다.

- 정수/부동소수점/벡터 비트 폭과 signedness
- 레지스터, 메모리, I/O, VM operand stack, GPU lane/shared/global memory
- 분기와 호출뿐 아니라 예외, trap, 동기화, 원자성, barrier
- 주소 계산과 데이터 계산의 차이, 정의되지 않거나 구현 의존인 동작
- 원본 패턴·의미 조각으로 역추적하는 provenance

2026-10-01 결정에 따라 의미의 소유자는 단일 FIR이다. NIR/HIR처럼 별도 의미 IR 단계로 분리하지 않는다. 도메인별 typed operation과 ordered effect를 FIR에 보존하고, 출력 계층은 같은 FIR을 소비한다. 디코드 계획과 출력용 자료는 컴파일 산출물·projection이며 별도 의미 소유자가 아니다.

2026-10-03에 FIR의 역할을 **Fission이 소유하는 독립 중간 의미론**으로 명시했다. 타입·상태 전이·효과·trap/예외·변환 조건을 자체 계약으로 정의한다. SLEIGH/SLA/P-code는 이관 입력이며, P-code를 거쳐야 하는 실행·분석 경로는 목표 아키텍처에 요구하지 않는다. 현재 구현과 앞으로의 요구사항은 [FIR 의미론 계약](fir-semantic-contract.md)에서 구분한다.

FIR은 C나 하나의 호환 IR로 직접 출력하는 표현이 아니라 의미 코어다. C/Rust source, stack-VM IR, 기존 분석 IR, graph, AI evidence packet은 각자 projection adapter가 소비한다. 각 adapter는 보존 범위, 전제, 손실, unsupported 의미, provenance 전달 방식을 선언해야 한다. JVM `iadd` 한 명령으로 이 경계를 시험한 산출물은 [다중 projection 실험](fir-multiple-projections.md)에 있다. 이 예시는 전체 Java decompilation이나 실제 P-code adapter가 아니다.

### 패턴 지식베이스

패턴 DB는 opcode 문자열 사전이 아니라 근거를 가진 주장들의 그래프/관계형 모델로 시작한다. 각 레코드는 다음을 가질 수 있다.

- 도메인/ISA/VM 구현, 아키텍처와 버전 범위
- 바이트/비트 패턴, 필드 및 컨텍스트 제약
- 추출된 피연산자와 렌더링 규칙
- FIR 의미 조각, effect, 호출/예외 정보
- 출처 종류와 위치: 공식 명세, `.slaspec`, `.sla`, 실측, 수작업 추론
- 입력 파일 SHA-256, 도구/컴파일러 버전, 근거 링크
- 검증 상태: 관찰, 재현, 차등 검증, 확정, 반례 발견
- 값의 범위: 보장, ABI 의존, 구현 의존, 추정, 미상
- 인코딩/의미의 동치군과 알려진 변형

AI가 이 DB를 사용할 때는 정답뿐 아니라 근거와 불확실성도 함께 받을 수 있어야 한다. 근거가 없는 유사도 추정은 공식 의미와 섞지 않는다.

레코드 식별자와 조회 방식의 초안은 [`pattern-database.md`](pattern-database.md)에 있다.

## 현재 FSL/FIR 연구 진행

이 문서의 아래 Python vertical slice는 초기 실험 기록이다. 현재 Rust `fission-fsl`은 별도 Fission PR에서 텍스트 FSL과 바이너리 `.fslc`를 구현한다. 단일 FIR 실행 출력과 GFX900 고정폭 인코딩 확장을 포함한 최신 범위는 [진행 현황](research-status.md)을 참조한다. 초기 TOML/JSON 형식을 새 컴파일러의 소스·런타임 형식으로 취급하지 않는다.

메인 Fission의 Notion 계획은 FSL/FIR의 채택 전에 작고 측정 가능한 품질 개선을 먼저 확인하라고 권고한다. 이 저장소는 별도 연구 프로젝트이므로 GPU, VM, SLA, FSL 컴파일러를 병행해 아이디어의 표현력과 실패 지점을 넓게 탐색한다. 다만 이 프로젝트의 산출물은 메인 Fission 이식 근거나 FSL/FIR 성공 증명으로 취급하지 않는다. 이 구분과 원문 근거는 [Notion 연구 컨텍스트](notion-fsl-fir-context.md)에 있다.

현재 vertical slice 두 개를 연결했다. GFX900에서는 authored FSL subset → compiled profile → pattern-driven decoder를, JVM에서는 무레지스터 FSL profile의 `iadd` (0x60) → 8-bit fixed-width decoder → 여러 FIR projection을 만든다. 공통 decoder는 profile에서 word width와 endian을 읽지만, JVM 가변 길이 명령 및 class-file framing은 아직 지원하지 않는다. SGPR/VGPR register class와 scalar-source selector 표는 선언형 range/case 데이터로 컴파일되며 generic decoder가 소비한다. 다음 설계 판단은 bitfield 조합과 상대 주소 계산, JVM 가변 길이/확장 워드를 같은 package model로 표현할 수 있는지에 달려 있다. [FSL 컴파일러 노트](fsl-first-compiler-slice.md)는 현재 transform vocabulary와 증거 한계를 기록한다.

## 도메인 진행 순서

| 단계 | 도메인 | 연구 이유 | 별도 모델이 필요한 지점 |
|---|---|---|---|
| 0 | 기존 SLEIGH 대상 ISA | 문법과 SLA 결과를 대조하고 CPU 공통 코어 검증 | 기존 포맷의 호환/변환 경계 |
| 1 | JVM bytecode | `iadd` 단일 opcode slice가 있으며, 나머지 명령어는 바이트코드지만 상수 풀·검증·예외 메타데이터와 강하게 결합 | classfile 버전, variable-length instruction, operand stack, verifier 타입, exception table |
| 2 | CPython bytecode | 버전 변화와 구현 의존 동작을 추적하며 바이트코드 도메인 확장 | CPython 버전별 opcode, inline cache, stack effect, 객체/호출 의미 |
| 3 | GPU 가상 ISA + 실제 ISA | SIMT와 메모리 계층이 FIR 표현에 주는 압력을 확인 | warp/wavefront, lane mask, barrier, memory ordering, target SM |

이 표는 도메인 구분을 위한 지도이지 고정된 구현 순서가 아니다. 현재는 공식 ISA 자료, LLVM toolchain, ROCm/KFD 소스 경로를 함께 따라갈 수 있어 GPU 정적 slice를 먼저 만들었다. JVM은 VM stack semantics를, `.sla`/`.slaspec` 대조는 기존 SLEIGH의 정보 손실과 재사용 구조를 연구한다. GPU에서는 PTX를 일반 CPU ISA처럼 부르면 안 되고, 가상 ISA·실제 디바이스 ISA·런타임/드라이버 계층을 각각 연결해야 한다.

## 검증 계획

1. **형식 복원**: 동일한 `.slaspec`과 `.sla`에서 패턴, 피연산자, 의미를 각각 추출해 관계를 맞춘다.
2. **동일 입력 디코드**: 공식 Ghidra 결과 또는 승인된 기준 구현과 임의/유효 바이트열 디코드를 대조한다.
3. **의미 차등 검증**: 짧은 명령 시퀀스를 에뮬레이터 또는 공식 실행 의미와 비교한다. 비결정·구현 의존 영역은 별도 분류한다.
4. **표현력 측정**: FSL에서 직접 표현된 비율, 외부 플러그인/escape 필요율, 모호성, unsupported 효과 수를 보고한다.
5. **AI 실험**: 같은 base model에 동일한 과제를 주고 FSL/FIR 패턴 근거를 제공한 경우와 제공하지 않은 경우를 비교한다. 정확도뿐 아니라 근거 일치율과 잘못된 확신도 기록한다.
