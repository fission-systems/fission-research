# FIR 의미 코어와 다중 projection 실험

## 설계 질문

FIR을 C 출력용 IR로 만들면 Rust, 분석용 그래프, 기존 디컴파일러 IR, AI 근거 응답을 위해 각기 다른 FIR을 만들게 된다. 여기서는 FIR을 하나의 목표 언어가 아니라 **의미와 효과를 보존하는 정규 코어**로 두고, 소비자가 필요한 projection을 별도 어댑터로 만드는 가설을 시험한다.

```text
FSL 패턴 + 출처
       ↓
FIR 의미 후보: 타입 · operand stack · 효과 · 불확실성 · provenance
       ├── 바이트코드 listing
       ├── C / Rust source 후보
       ├── 분석 IR 후보
       ├── dataflow/effect graph
       └── AI 근거 패킷
```

FIR 코어와 projection은 다른 계약이다. 각 projection은 지원 범위, 보존한 사실, 가정, 잃은 사실, 검증 상태를 내보내야 한다. 한 projection의 실패나 손실이 다른 projection의 의미를 바꾸면 안 된다. provenance나 uncertainty를 코드 문법에 넣을 수 없으면 출력 패키지의 sidecar로 남긴다.

## 한 명령으로 한 시험

[`specs/vm/jvm-se26-iadd.fsl`](../specs/vm/jvm-se26-iadd.fsl)은 Oracle JVMS Java SE 26의 한 바이트 opcode `iadd` (0x60)만 기술한다. 명세는 두 `int` 값을 operand stack에서 꺼내 합의 하위 32비트를 다시 넣고, 이 명령 자체는 run-time exception을 던지지 않는다고 규정한다. [`iadd` 명세](https://docs.oracle.com/javase/specs/jvms/se26/html/jvms-6.html#jvms-6.5.iadd)와 [명령어 stack diagram 설명](https://docs.oracle.com/javase/specs/jvms/se26/html/jvms-6.html#jvms-6.4)를 참고한다.

[`experiments/jvm/java-se-26/iadd.projections.json`](../experiments/jvm/java-se-26/iadd.projections.json)은 같은 디코드 및 FIR 후보에서 아래 결과들을 만든다.

| Projection | 표현 | 이 slice가 보존하는 범위 |
|---|---|---|
| Bytecode listing | `iadd`, opcode `0x60`, 원본 바이트 | 단일 명령의 identity |
| C source | `uint32_t` 덧셈 | 32-bit 결과 비트 패턴. Java signed 비교/표시 의미는 생성하지 않음 |
| Rust source | `u32::wrapping_add` | 32-bit 결과 비트 패턴 |
| Stack IR | 입력 두 개와 pop 2 / push 1 | 이 명령의 local operand-stack 전이 |
| Sequential IR candidate | `INT_ADD` 및 명시적 stack 전이 | 산술과 local stack effect. 실제 Ghidra P-code encoding은 아님 |
| Analysis graph | 입력·연산·결과 노드와 edge | 현재 모델이 기술한 dataflow와 stack effect |
| AI evidence packet | claim, 전제, 명세 출처, 입력/profile 해시 | 모델이 claim과 근거 및 범위를 함께 볼 수 있는 상태 |

C와 Rust 예시는 **전체 JVM 프로그램의 decompilation이 아니다**. 단일 연산의 비트 결과를 각 언어에서 어떻게 표현할지 보여주는 source projection 후보이다. C에서는 signed overflow에 의존하지 않도록 `uint32_t`를 사용한다. Sequential IR은 이름이 비슷한 기존 IR과 혼동하지 않게 “P-code-like research projection”으로 표시한다.

## 재현

```sh
python3 tools/fslc_probe.py specs/vm/jvm-se26-iadd.fsl --output data/patterns/jvm-se26-iadd.json
python3 tools/fsl_decode_probe.py experiments/jvm/java-se-26/iadd.bin \
  --patterns data/patterns/jvm-se26-iadd.json \
  --output experiments/jvm/java-se-26/iadd.decode.json
python3 tools/fir_projection_probe.py experiments/jvm/java-se-26/iadd.decode.json \
  --output experiments/jvm/java-se-26/iadd.projections.json
```

`iadd.bin`은 opcode 0x60 하나만 가진 **synthetic byte fixture**다. 이 실행은 profile compiler와 decoder의 실제 산출물 생성 경로를 보여줄 뿐 JVM verifier, `.class` parser, JVM 실행기, C/Rust compiler를 실행하지 않는다. JVM instruction은 일반적으로 가변 길이이므로 이번 fixed-width 8-bit slice를 전체 JVM decoder 지원으로 보면 안 된다.

## 결과에서 확인할 의미 경계

- `canonical_fir_candidate`는 스택 입력, 결과 타입, wrapping 규칙, 예외 효과, verifier 전제, provenance를 함께 유지한다.
- C/Rust projection은 결과의 32-bit bit pattern만 보존한다고 명시한다. stack frame과 Java signed-level 관례까지 복원한다고 주장하지 않는다.
- 분석/순차 IR은 implicit stack을 명시적인 SSA형 입력으로 바꾸지만, 원래 bytecode identity를 대체하지 않는다.
- AI packet은 근거와 제한을 함께 묶는다. 디코더가 pattern source ID를 package source catalog에 연결해 URL, 출처 종류, revision을 결과에 넣는다. primary specification 링크는 provenance이지, 이 구현의 독립 실행 검증이 아니다.
- 각 상태 문자열은 현재 probe의 실험 계약이다. 여러 opcode와 반례로 측정하기 전까지 안정된 FIR 표준이나 losslessness proof가 아니다.

## 다음 연구 질문

1. Projection descriptor를 별도 스키마로 만들고, `exact`, `scoped`, `lossy`, `unsupported` 보존 상태와 사라지는 사실을 기계 판독 가능하게 할 것인가?
2. CPU/GPU의 register 및 memory effect와 VM operand stack을 같은 FIR effect algebra에서 복원 비용 없이 유지할 수 있는가?
3. Java, C, Rust, LLVM IR, 기존 P-code 계열의 출력은 source generation인지, 분석 adapter인지, 둘 다인지 명확한 target capability 모델이 필요한가?
4. 여러 명령의 CFG와 stack merge를 추가했을 때 provenance와 verifier 타입을 각 projection까지 추적할 수 있는가?
