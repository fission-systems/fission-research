# Semantic pattern database: draft

## 설계 목표

이 DB는 opcode 설명 텍스트의 임베딩 모음이 아니다. 디코더가 바이트/비트열에서 후보를 결정론적으로 찾고, FIR 의미와 부가 근거를 AI가 조회할 수 있도록 구조화한 데이터다. 같은 사실을 출처별로 중복 저장하지 않고, 서로 다른 근거가 같은 패턴/의미를 지지하는 관계를 남긴다.

질의는 적어도 네 종류를 지원한다.

1. **정확 매치**: 아키텍처와 상태/모드를 지정해 바이트열을 디코드한다.
2. **조건 확인**: 특정 ISA/VM 버전에 어떤 opcode, operand, effect가 유효한지 조회한다.
3. **의미 검색**: 의미가 같은 명령·바이트코드 후보를 FIR 정규형으로 비교한다.
4. **근거 조회**: 필드와 의미 주장을 원본 spec 행, `.sla` 노드, 공식 매뉴얼, 실측 결과로 역추적한다.

## 1차 엔터티

| 엔터티 | 키가 표현하는 것 |
|---|---|
| `LanguageProfile` | ISA/VM/GPU ISA의 이름, 구현/모델, 버전, 모드, endian, 주소 크기 |
| `SourceArtifact` | 원본 경로, 버전/커밋, SHA-256, 라이선스, 생성 도구 버전 |
| `SourceLocation` | artifact 내부 파일/행/기호 또는 SLA element path와 raw node ID |
| `Pattern` | 조건과 인코딩 표현. 고정 비트, 필드, 컨텍스트, 가변 길이, 우선순위 |
| `OperandRule` | 비트/스택/상수 풀에서 operand를 뽑고 변환하는 규칙 |
| `SemanticTemplate` | FIR 영역/명령, 출력 타입, 상태 효과, 제어 흐름, 예외/불확정 효과 |
| `DisplayRule` | 어셈블리 또는 mnemonic 출력. 의미 레코드와 독립적으로 유지 |
| `Evidence` | 어떤 source artifact나 실험이 어느 claim을 뒷받침하는지, 검증 결과와 범위 |
| `Relation` | alias, subtable call, overlap, precedence, semantic equivalence, specialization |

## 식별자 원칙

원본 컴파일러의 symbol ID, 서브테이블 번호, constructor 순번은 가져온 산출물 내 연결에만 사용한다. 업데이트 후 이 값이 유지된다고 가정하지 않는다. 영속적인 `PatternId`는 다음을 조합해 만든다.

- normalized language/profile identity와 적용 버전 범위
- 정규화된 encoding predicate와 context predicate의 content hash
- 의미가 확인된 경우 normalized FIR semantic hash
- 구별이 필요한 원본 source location과 artifact digest

동일한 기계어 인코딩이 다른 모델에서 다른 의미를 가질 수 있으므로 encoding hash만으로 모든 아키텍처를 합치지 않는다. 다른 구현에서 의미 동치라고 결론 내린 경우에도 canonical record 하나로 덮지 않고 `equivalent_to` 관계와 근거를 유지한다.

## 사실과 해석 분리

각 claim은 `value`, `scope`, `evidence_ids`, `confidence_status`를 가진다.

- `observed`: 원본에서 읽었으나 독립 검증 전
- `reproduced`: 명세/컴파일러와 재현 가능하게 대조
- `differentially_verified`: 샘플/실행 결과와 차등 확인
- `inferred`: 간접 증거에서 얻은 해석
- `unknown` / `unsupported`: 의미가 미확정 또는 현재 분석 불가
- `contradicted`: 다른 근거/반례가 있어 해결 전

범위는 `guaranteed`, `profile-dependent`, `implementation-dependent`, `undefined`, `inferred`처럼 별도 축으로 둔다. “confidence” 하나로 보장 범위와 연구 진행 상태를 섞지 않는다.

## SLA 가져오기에서 요구되는 관계

SLA에서 최소한 아래 연결을 복원해야 FSL 레코드로 옮길 수 있다.

```text
language profile
  -> subtable symbol and name
      -> decision tree -> (subtable-local constructor index, encoding pattern)
      -> constructor slot -> display, operands, ConstructTpl, source location
```

특히 보존할 점은 (1) decision pair가 constructor 정의와 별도 하위 트리에 저장됨, (2) pair ID가 parent subtable 범위에서 해석됨, (3) 이름 테이블과 symbol body가 별도 기록될 수 있음, (4) 하위 subtable은 재사용 가능한 operand decoder일 수 있음, (5) `ConstructTpl`이 decode predicate 그 자체가 아니라 실행 의미라는 점이다. 각 joined edge에도 두 입력 node 경로와 hash를 저장해 가져오기 실수를 추적할 수 있게 한다.

## AI 소비 방식

AI 호출에 DB 전체를 통째로 넣지 않는다. 먼저 profile/bytes로 정확 패턴을 찾고, FIR/effect와 근거를 좁혀 보내며, 모호한 디코드 후보가 있으면 후보 목록·분기 조건·unknown 필드를 함께 준다. 의미 유사도 검색은 정확 디코드와 구분해 설명한다. 평가에서는 정확한 디코드 성공, 의미 일치, 인용 근거 정확성, 미지원 영역을 unsupported로 인식한 비율, 과도한 확신을 각각 보고한다.

## 첫 구현 데이터

[`specs/gpu/amdgcn/gfx900-first.fsl`](../specs/gpu/amdgcn/gfx900-first.fsl)은 첫 GFX900 4-pattern 패키지의 authored source다. [`tools/fslc_probe.py`](../tools/fslc_probe.py)는 참조, 필드 범위, 고정값, 제약, 변환 규칙, 패턴 겹침을 확인하고 원문 hash와 compiler 버전을 포함한 [`data/patterns/amdgpu-gfx900.json`](../data/patterns/amdgpu-gfx900.json)을 만든다. 공통 [`tools/fsl_decode_probe.py`](../tools/fsl_decode_probe.py)는 이 패키지의 operand descriptor로 `.text` fixture를 디코드하고, 기존 GFX9 CLI 경로 [`tools/gfx9_decode_probe.py`](../tools/gfx9_decode_probe.py)는 호환 진입점으로 남긴다. 무레지스터 JVM profile까지 패키지 형식과 디코더를 재사용한 실험은 [다중 FIR projection 노트](fir-multiple-projections.md)에 기록했다.

이것은 위 엔터티 모델의 완성 DB가 아니라, 원문에서 AI가 소비할 수 있는 패키지까지 provenance 경계를 유지하는 실험이다. 전체 인코딩 공간, 가변 길이/확장 워드, 관계 조회, 실행 가능한 FIR semantics는 아직 지원하지 않는다. Operand transforms 일부도 Python 코드에 남아 새 아키텍처를 데이터만으로 추가한다는 점을 입증하지 못했다. 결과와 구현 경계는 [첫 디코더 노트](gfx9-decoder-first-slice.md)와 [FSL compiler slice](fsl-first-compiler-slice.md)에서 확인한다.
