# 자체 자산 체계와 구조를 보존하는 단일 FIR

결정일: 2026-10-03. 목표는 기존 자산의 기능을 자체 계약으로 대체하는 것이다. 전체 자산 이관이나 새로운 제어 흐름 구현 완료를 뜻하지 않는다.

## 자산별 소유 경계

고정 Fission 입력 `96fc71f75cecdee305faf9497561c577a8955468`의 `utils/`를 해시 인벤토리로 기록했다. [전체 목록](../experiments/migration/asset-replacement/legacy-assets.json)의 `inventoried-only`는 이관 완료 상태가 아니다.

| 기존 자산 | 파일 수 | 자체 표현 | 현재 이관 범위 |
|---|---:|---|---|
| `.slaspec` / `.sinc` | 146 / 204 | 텍스트 `.fsl`, 향후 모듈·context·operand 규칙 | eBPF ADD64 register leaf |
| `.sla` | 133 | 검증된 encoding + FIR을 가진 `.fslc` | 직접 SLA ADD64 slice와 layout |
| `.cspec` | 110 | `.fslabi`: 데이터 모델, 호출·저장 계약 | 두 ABI metadata; 실제 allocator 미지원 |
| `.pspec` | 83 | `.fslregs`와 processor policy | layout은 source/SLA에서 일부 이관; pspec policy 미지원 |
| `.ldefs` | 51 | 자체 profile manifest: ISA/version/endian/layout/ABI/package 선택 | 설계; parser 미구현 |
| `.fpk` | 261 | 데이터 종류별 자체 schema, 함수 후보는 `.fslib` → `.fsldb` | C library 64-bit corpus 한 파일 |

FPK는 이미 Fission의 자체 컨테이너다. 기존 구현의 sorted text block 압축 형식은 함수, 타입, ordinal 등 payload의 의미를 정의하지 않는다. 따라서 확장자만 바꾸는 대신 각 payload의 의미 계약을 만든다. Go 타입, 구조체, FID matching, ordinal에는 별도 schema와 이관 검증이 필요하다. 모든 FPK를 함수 서명으로 해석하지 않는다.

참고 입력은 offline importer에서만 사용한다. 현재 `.fslc` loader와 새 `.fsldb` reader는 SLEIGH/SLA/FPK를 호출하지 않는다. 제품의 기존 loader·decompiler 경로를 전부 교체한 상태는 아니다. 원본 자산 삭제는 모든 소비자의 자체 자산 전환과 이관 증거가 갖춰진 이후 단계다.

향후 profile manifest는 패키지 해시·schema version·아키텍처 범위·명시적 지원 capability·layout/ABI/catalog 참조를 결합한다. 이름만 같은 profile이나 ABI를 자동 선택하지 않는다. signature의 type spelling을 FIR의 확정 타입으로 자동 승격하지 않는다. 라이선스·원본 출처·변환 기록도 corpus별로 보존해야 한다. SHA-256은 변경 검출용이며 라이선스나 신뢰성의 증명이 아니다.

## P-code 평탄화 문제를 다루는 방법

Ghidra의 raw P-code는 명령 하나를 varnode와 저수준 연산열로 번역한다. branch를 표현하고 graph 단계에서는 SSA 등의 분석 연산도 추가한다. 그러므로 문제를 “P-code에는 CFG가 없다”로 정의하지 않는다. 우리가 피하려는 것은 명령의 의미 경계, 타입, lane/VM/memory 도메인과 효과를 먼저 연산열로 풀고 이후 소비자가 재추측하는 경로다. [Ghidra P-code reference](https://ghidra.re/ghidra_docs/languages/html/pcoderef.html), [SLEIGH manual](https://ghidra.re/ghidra_docs/languages/html/sleigh.html).

채택할 단일 FIR의 구조 계약은 다음과 같다. **아래 구조는 설계이며, 현재 `FirOp`의 단일 명령 연산열에는 아직 구현되지 않았다.**

| 구성 요소 | 보존할 의미와 검증 조건 |
|---|---|
| Function / entry | 입력 상태·ABI 전제·결과와 실행 범위. 주소와 소스 언어를 동일시하지 않음 |
| Block | 명시적 parameter와 successor argument. 값의 정의·dominance·타입 검증 |
| Terminator | branch / conditional branch / return / trap / invoke의 명시적 대상과 결과 |
| Semantic region | 한 명령, predication, lane 실행 등 의미 경계. 입력·출력·효과 계약을 가진 연산의 body |
| Domain operation | bitvector 계산, VM stack, register view, memory space, lane mask, atomic, barrier, exception 등 자체 연산 |
| State / effect | domain별 상태 값과 순서 dependency. alias가 가능하면 분리를 증명하거나 순서를 유지 |
| Origin / evidence | 원본 bytes·주소·instruction span, spec/version, 출처, 변환·검증 기록 |

Block·region은 같은 FIR의 구성 요소다. 다른 상위 IR로 의미를 다시 소유하지 않는다. region은 재컴파일 backend가 원래 domain을 처리할 수 있으면 직접 사용하고, 필요한 경우 계약을 보존하는 같은 FIR 내부의 명시적 변환으로 펼친다. JIT/AOT 편의를 위한 lowering은 전체 분석 소비자의 필수 진입점이 아니다.

각 domain의 상태는 그 연산이 선언한 읽기·쓰기·관찰 범위를 가진다. 독립 domain의 효과를 병렬화하려면 alias와 동기화 제약을 확인해야 한다. GPU barrier를 단순 함수 호출로 출력하거나 invoke의 예외 edge를 지워서는 안 된다. 미지원 backend는 거부한다.

`if`, loop, CUDA kernel 등의 원본 구조가 바이너리에 그대로 남아 있다는 보장은 없다. recoverable CFG 사실을 보존하고, irreducible flow는 그래프로 남긴다. 분석이 추론한 loop/if view는 같은 FIR 위의 파생 사실이며, 사실 여부를 검증하지 못한 구조를 실행 의미로 덮어쓰지 않는다.

```text
FSL / offline legacy importer
        ↓
단일 FIR: block + typed domain op + region + ordered effects + origin
        ├→ 분석 / 구조 view / 근거 packet
        ├→ C / Rust / CUDA C++ / PTX
        └→ target lowering → 명령 선택 / register allocation / encode / ABI
```

## 다음 구현과 수용 기준

1. `.fslc`에 block parameter·terminator를 추가한다. 기존 단일 명령 패키지는 하나의 entry block으로 읽는다. 즉시값·비교·분기를 같은 FIR의 reference/C/Rust 경로에서 검증한다.
2. 두 successor와 state join 사례에서 branch argument 타입·dominance·register alias·효과 순서를 검사한다. 기존 carry/lane/stack 의미는 회귀 비교한다.
3. predication/lane region에서 비활성 lane 보존과 scalar 효과 1회 실행을 확인한다. reconvergence와 barrier는 계약·검증이 갖춰진 후 지원한다.
4. source/SLA 이관기를 그 구조 계약으로 확장하고, 미지원 constructor의 거부 사유를 유지한다. P-code opcode 복제나 독립 의미론 없는 opaque opcode는 대체 완료로 세지 않는다.
5. profile manifest와 각 corpus family를 연결한 뒤 실제 decompiler routing을 전환한다. 자체 artifact만 설치한 실행과 기존 corpus 비교를 제품 전환의 gate로 둔다.

현재 구현 증거는 [연구 현황](research-status.md)과 [FPK 이관 실험](../experiments/migration/asset-replacement/README.md)에 기록한다.
