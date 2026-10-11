# FIR의 정보 보존과 정확성 평가

결정: 2026-10-11. 단일 FIR을 의미 소유자로 두며 정확성을 우선한다.
풍부한 annotation만으로 정확도가 높아진다고 가정하지 않는다.

## 복구의 근거와 한계

Binary의 exact encoding, instruction mode/context, partial register effects,
defined/undefined state, memory address, control edge를 잃지 않고 분석에 연결한다.
Loader가 제공하는 sections/relocations/symbols와 DWARF, signature 후보, ABI
metadata도 각 출처와 적용 범위를 유지한다. 모순되는 후보는 기록하고 권위 있는
의미로 합치지 않는다. Instruction semantics와 heuristic prototype은 다른 증거다.

원래 source type/prototype이 binary만으로 유일하게 결정되는 경우는 보장되지 않는다.
정확성 목표는 관찰 가능한 machine behavior를 보존하는 것이다. Unknown은 unknown으로
남기고, 지원하지 않는 실행 의미는 오류로 거부한다. 임의 pointer/signedness/argument
count를 만들어 예쁜 출력을 얻는 방식은 검증 계약으로 인정하지 않는다.

## 현재와 설계 요구사항

| 항목 | 현재 구현 | 다음 요구사항 |
|---|---|---|
| 원본 근거 | x86 raw bytes/address/span/input·package hash/spec evidence | relocation/symbol/DWARF의 통합 query와 충돌 추적 |
| 구조 | typed FIR block arguments/branches; bounded body execution | recovered guest CFG joins/loops와 domain regions |
| 상태 | register/flag/lane effects, x86 six known bits | first-class definedness, ordered effect identities |
| 메모리 | bounded readonly/mutable flat byte window, ordered store, conservative forwarding/alias evidence | address spaces, guest ordering/atomic/barrier/fault contracts |
| ABI | metadata linking, 제한된 stack frame/spill 복구와 input dependency 후보 | call/return, convention allocation 및 검증 |
| 출력 | 동일 FIR에서 explicit-state C/Rust 및 제한된 GPU 출력 | 더 많은 executable backend와 runtime 계약 |

현재 FIR의 flat memory가 P-code의 space ID보다 풍부하다고 주장하지 않는다.
계획 중인 효과·fault·address-space 표현도 구현된 것처럼 계산하지 않는다.

## 비교 실험

[P-code 연산 정의](https://ghidra.re/ghidra_docs/languages/html/pcodedescription.html)는
memory/control/계산을 표현한다. 기존 SLA의 AF 누락은 IR의 표현력 한계가 아니다.
FIR metadata와 구조의 효과를 보려면 같은 input corpus와 독립 oracle에서:

1. 현재 SLA/P-code 구현의 실제 결과를 측정한다.
2. 같은 semantic coverage를 가진 FIR과 비교한다.
3. FIR의 origin/context/definedness/structure 정보를 한 종류씩 제거한 분석과 비교한다.
4. Decode, known semantic coverage, recovery precision, executable equivalence, refusal을
   각각 집계한다. Unsupported와 undefined를 정답으로 계산하지 않는다.
5. 차이를 instruction specification, evaluator, analysis heuristic, projection 별로 좁힌다.

3번 controlled ablation과 동일 coverage의 일반 함수 비교는 아직 수행하지 않았다.
[세 leaf 실행 실험](../experiments/x86/memory/README.md)은 1번과 제한된 2번의 시작이다.
후속 [store·stack frame 실험](../experiments/x86/stateful/README.md)도 같은 두 단계의
제한된 실행 비교다. Store-forwarding/alias 후보가 source-level ABI 복구의 정확도를
얼마나 바꾸는지는 아직 별도로 측정하지 않았다.
현재 관찰로는 AF 명세 누락을 찾았고 undefined AF를 정확도에서 제외했다는 주장만 한다.
FIR/P-code 전체 아키텍처의 우열이나 전체 x86 migration 성공을 주장하지 않는다.
