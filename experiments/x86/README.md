# 자체 x86 디코드와 단일 FIR 출력 — 2026-10-11

이 문서는 최초 63-body 단계의 고정 artifact와 관찰을 보존한다. 같은 날의
[readonly memory / 입력 근거 / 실행 비교 후속 단계](memory/README.md)는
126-body 선택 pool과 세 compiled ELF의 실제 C/Rust 실행 비교를 추가했다.
아래 최초 단계의 미지원 항목은 그 단계의 범위다.

목표는 x86 16/32/64비트 자산을 FSL/FIR로 옮기고 디컴파일 출력을 만드는 것이다.
현재는 **선택한 scalar 명령 window**에서 이 경로를 연결했다. 전체 x86 이관이나
기존 제품 디컴파일러 교체 완료를 뜻하지 않는다.

## 소유와 형식

외부 instruction decoder 라이브러리는 사용하지 않는다. `iced-x86`, Capstone,
Zydis 의존성 없이 Fission이 opcode·prefix·ModRM·SIB·immediate reader를 소유한다.
기존 workspace의 loader와 FIR 컴파일러/출력기는 재사용한다. 기존 loader의 파일
파싱 의존성, SHA-256 및 Cranelift까지 제거한 무의존 workspace라는 뜻은 아니다.

```text
scalar.fslx (encoding rules) + scalar-bodies.fsl (canonical semantics)
  → offline compiler → scalar.fslxc (compiled rules + .fslc body pool)
  → owned decoder → instances with original bytes / address / body reference
  → same FIR → reference execution / FIR diagnostic / C / Rust
```

`.fslx`와 `.fsl`은 텍스트 소스이며 `.fslxc`는 바이너리 패키지다. JSON은 잠금·
인벤토리·실험 보고서에만 쓰인다. Runtime은 SLEIGH/SLA/P-code를 호출하지 않는다.
정규화된 128비트 operand token은 내부 body binding이며 원래 x86 인코딩이 아니다.
Variable-length instance container가 기존 FIR body pool을 참조한다. 별도 의미 IR은 없다.

## 현재 범위

| 항목 | 구현 / 한계 |
|---|---|
| 인코딩 | 46개 규칙; MOV/ADD/SUB/CMP/AND/OR/XOR/TEST/LEA/NOP/JMP/JE/JNE/near RET |
| FIR | 63개 authored body; 16/32/64비트 register·immediate, LEA 주소 계산, flag 효과 |
| Prefix / addressing | 제한된 66/67/REX, register ModRM, LEA용 16비트 주소·SIB·RIP-relative |
| 상태 | GPR 16개 + zero slot, CF/PF/ZF/SF/OF/AF 및 각각의 known bit |
| 메모리 | near RET의 명시적인 bounded little-endian stack read; readonly flat byte window |
| 제어 | supplied window 내부 direct branch와 예산으로 제한한 재방문; 전체 window 사전 admission |
| 출력 | 실행 상태 인자를 받는 C/Rust 함수; source prototype·local variable·calling ABI 미복구 |
| Loader | caller가 지정한 executable file-backed span, relocation overlap 거부, 원본 파일/byte hash |
| Legacy layout | 1,380 register view, long-mode 1,440 view; overlapping offsets 보존 |
| 기존 자산 | x86 폴더 78개 파일 해시 인벤토리; `ia.sinc` register prefix 이외는 이관 미완료 |

`tools/x86_migrate.py`는 고정 비교 입력의 register 선언을 변환하고 scalar 명세를
작성한다. 전체 SLEIGH constructor/template을 자동 번역하는 도구는 아니다.
인코딩/효과 참고는 [고정 ia.sinc](https://github.com/fission-systems/Fission/blob/96fc71f75cecdee305faf9497561c577a8955468/utils/sleigh-specs/languages/x86/ia.sinc)와
[Intel SDM](https://www.intel.com/content/www/us/en/developer/articles/technical/intel-sdm.html)이다.
원문에서 미구현인 AF도 ADD/SUB/CMP body에 표현했다. Logic 연산의 undefined AF는
값을 확정하지 않고 known bit를 지운다. SDM은 pinned oracle artifact가 아니며
명세에 의한 실행만으로 실제 ISA 동치가 검증되지는 않는다.

## 상태 / 반환 계약

GPR 순서는 `RAX,RCX,RDX,RBX,RSP,RBP,RSI,RDI,R8..R15,zero`다. 16비트 쓰기는
상위 bit를 보존하고 32비트 쓰기는 logical slot 상위를 지운다. Legacy 모드의 상위
slot bits는 이 실험의 transport 상태이며 full architectural state snapshot이 아니다.
Flag 배열은 `CF,PF,ZF,SF,OF,AF,known_CF,...,known_AF`다. 입력 known bits는 모두
1이어야 한다. 출력 unknown AF placeholder는 관찰하지 않아야 한다.

RET도 FIR로 stack read·SP increment·next PC write를 수행한다. Memory base와 bytes는
caller가 제공한다. 16비트 RET은 flat `SS.base=0` 계약이며 segment/stack-address-mode,
MMU, faults, privilege, concurrency 의미는 구현하지 않았다.

Wrapper는 temporary state로 실행하고 RET 성공 때만 caller state와 exit PC에 commit한다.
Admission/주소/메모리/예산 실패는 상태를 보존한다. 이는 CPU fault ordering이나 atomic
instruction 의미가 아니다. C caller storage는 유효하고 서로 겹치지 않아야 한다.

## 재현

Native 구현은 Fission `codex/fsl-jvm-iadd-parity`의 `crates/fission-fsl`이다.

```sh
cargo build --locked -p fission-fsl --features x86 --bins
```

연구 저장소에서:

```sh
python3 tools/x86_migrate.py --fission-root Fission --output-dir artifacts/x86-specs
python3 tools/x86_reproduce.py \
  --fsl-x86 /path/to/Fission/target/debug/fsl-x86 \
  --cc clang --rustc 'rustup run stable rustc'
```

`reproduction.lock.json`은 source/ELF/package/output 해시를 고정한다. 재현기는 같은
패키지, FIR/C/Rust 15개 출력, reference 실행 5개를 다시 만들고 잠금과 비교한다.
Compiler 옵션을 주면 C/Rust 각각 5개 소스를 warning-denied로 컴파일한다.
CI는 compiler commit을 고정하고 같은 재현을 실행한다. 이 gate는 self-derived artifact
재생성 검사이며 독립 ISA oracle 또는 재컴파일된 출력의 runtime parity 검사는 아니다.

`fixtures/add32.elf`와 `add64.elf`는 Clang/LLD 22.1.8이 source fixture에서 만든 작은
고정 ELF다. Compiler command는 lock에 있다. 32비트 source는 **regparm(2)**로 EAX/EDX를
사용하며 default cdecl 증거가 아니다. 64비트 source는 SysV AMD64의 RDI/RSI를 사용한다.
두 span은 `0x401000`의 `01d0c3`와 `488d0437c3`다. Host가 ARM64이므로 original x86
ELF를 hardware에서 실행한 것이 아니다. 공급한 register/stack 상태를 FIR로 실행했다.

## 이번 관찰과 다음 단위

- Package compile: 46 rules / 63 bodies.
- Layout source parse: 1,380 / 1,440 views.
- Raw 16/32/64 window와 ELF 32/64 span의 FIR reference 결과: 5개 모두 RAX=12,
  SP가 해당 mode의 near RET 폭만큼 증가하고 supplied stack의 return PC를 사용했다.
- 생성한 C 5개 / Rust 5개 source가 warning-denied compilation을 통과했다.
- Native x86 feature build와 Clippy가 통과했다. 이번 로컬 작업에서 기존 unit suite를
  재실행하지 않았다. 위 결과는 broad regression acceptance나 전체 함수 동치 증거가 아니다.

다음은 ordinary memory operand·stack frame·CALL/ABI·indirect control, byte/high-byte
registers, shift/ADC/SBB/MUL/DIV, x87/SIMD/AVX, segment/fault model과 cspec/pspec/context
이관이다. 독립 인코딩 corpus 비교와 실제 x86 실행 oracle, emitted-source runtime 비교를
연결한 뒤 지원 범위를 늘린다. 디코드 데이터를 추가하는 변경과 generic primitive 변경을
구분해 기록해야 한다. GPU/JVM 기능 완료나 전체 x86 지원으로 확대 해석하지 않는다.
