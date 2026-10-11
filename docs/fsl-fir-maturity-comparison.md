# SLEIGH/NIR/HIR 대비 FSL/FIR 성숙도 — 2026-10-11

## 평가 기준

현재 실험 브랜치의 코드 경로와 보관한 실행 증거를 비교했다. 제품 전체
benchmark를 이번 단계에서 다시 측정한 결과는 아니다. 성숙도를 백분율이나
완성까지 걸리는 기간으로 환산할 근거는 없다.

| 영역 | 기존 Fission SLEIGH / NIR / HIR | 자체 FSL / FIR | 현재 격차 |
|---|---|---|---|
| ISA 자산 | 다수 SLEIGH/SLA, context와 operand/template 처리 경로 | x86 v2 48 encoding rules / 150 폭별 body, GPU·eBPF·JVM의 작은 slice | 전체 명령·prefix·context·예외 이관에서 매우 큼 |
| 의미 표현 | P-code lifting과 이후 NIR/HIR 분석·표현 | 단일 typed FIR, ordered register/flag/memory/lane effects, block 인자·분기 | FIR의 새 철학을 시험할 기반은 있으나 넓은 의미 coverage가 없음 |
| 함수 분석 | CFG, normalization, structuring, 타입·call fact 전달 경로 | caller 지정 x86 spans, entry dependency·store/alias 후보와 명시적 상태 | 일반 CALL/ABI/CFG·타입 복구가 가장 큰 격차 |
| 디컴파일 출력 | 제품 CLI의 C 지향 함수 출력 경로 | 제한된 계약의 C/Rust/Go 상태 실행 코드; stack FIR CUDA/PTX reference | 일반 소스 함수·프로젝트 재구성 수준에 못 미침 |
| 출력 확장 | 기존 renderer와 제품 경로 | C/Rust/Go 공통 backend plan/bundle/registry | 확장 계약을 도입했지만 Go의 제한된 실행 출력을 검증했으며 Python/Java는 미구현 |
| 통합 | loader→facts→decompiler와 테스트·benchmark 인프라 | 실험 crate/CLI에서 기존 loader를 재사용 | 제품 기본 경로 전환·자산 전체 대체는 미완료 |
| 정확성 증거 | 기존 테스트/평가 경로가 있으나 모든 함수 동치 보장은 없음 | 제한된 state/byte/재컴파일/original 실행 비교와 실패 시 상태 보존 | 실험의 엄밀함과 제품 범위는 별개; 광범위 비교가 더 필요 |

## 소스 근거

Fission 실험 브랜치의 다음 소유자들을 읽었다.

- `crates/fission-sleigh/src/compiler/sla/`: packed 형식, symbol/template 처리.
- `crates/fission-pcode/src/midend/mod.rs`: builder→normalize→structuring→render.
- `crates/fission-pcode/src/midend/cspec/`: register/ABI metadata 적용 경로.
- `crates/fission-decompiler/src/facts/facts.rs`: NIR type context와 call prototype,
  parameter/effect facts, HIR build 연결.
- `crates/fission-fsl/src/{package,semantics,state,x86,recovery,backend}.rs`:
  현재 자체 명세·FIR·명시적 window 실행·후보 복구·출력 admission.

구체적인 native pin과 실행 횟수는 [현재 진행 기록](research-status.md) 및
[backend 재현 기록](../experiments/output/backend-contract/README.md)에 보관한다.
기존 자료 133개 SLA의 구조 파싱은 133개 ISA의 의미 이관 성공을 뜻하지 않는다.
150개 body도 150개 서로 다른 x86 mnemonic을 뜻하지 않는다.

## 정확성 우선 방향의 의미

FIR에서 flag/메모리/예외/lane의 계약과 provenance를 명시하면 누락·잘못된
추론을 발견하고 출력 admission을 제한하기 쉬워진다는 가설을 검증한다.
P-code도 상태·주소 공간·분기 등을 표현할 수 있고 이후 SSA/CFG 분석이 가능하다.
기존 x86 baseline의 AF 차이는 참고 명세의 효과 누락이 원인이므로
P-code의 표현 한계나 FIR 자체의 우월성으로 해석하지 않는다.

현재 FSL/FIR은 **선택한 명령과 상태 계약을 실행 검증하는 프로토타입**이다.
기존 경로는 **더 넓은 자산과 함수 분석을 제품으로 연결한 구현**이다.
다음 수용 기준은 지원 이름의 수보다 실제 명령 coverage, CALL/ABI/CFG와
메모리 효과 복구, 독립 oracle, 원본 실행 및 출력별 재컴파일 비교여야 한다.
