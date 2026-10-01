# JVM SE 26 `iadd` projection slice

This slice is one synthetic byte (`0x60`) decoded as the Java SE 26 JVM `iadd` opcode. The profile source cites the [Oracle JVMS instruction definition](https://docs.oracle.com/javase/specs/jvms/se26/html/jvms-6.html#jvms-6.5.iadd). The input is not taken from a real `.class` method and is not run by a JVM.

## Reproduce

From the repository root:

```sh
python3 tools/fslc_probe.py specs/vm/jvm-se26-iadd.fsl --output data/patterns/jvm-se26-iadd.json
python3 tools/fsl_decode_probe.py experiments/jvm/java-se-26/iadd.bin \
  --patterns data/patterns/jvm-se26-iadd.json \
  --output experiments/jvm/java-se-26/iadd.decode.json
python3 tools/fir_projection_probe.py experiments/jvm/java-se-26/iadd.decode.json \
  --output experiments/jvm/java-se-26/iadd.projections.json
```

The decode record preserves opcode identity and the pattern's spec-derived effect candidate. The projection record includes a canonical FIR candidate and seven views: bytecode listing, C, Rust, stack IR, sequential IR candidate, analysis graph, and AI evidence packet. C/Rust snippets express the 32-bit result bit pattern only. No class-file parser, bytecode verifier, CFG builder, JVM, C compiler, or Rust compiler is part of this experiment.

## Artifact hashes

| Artifact | SHA-256 |
|---|---|
| `jvm-se26-iadd.fsl` | `2d6727abcc5fd7eeb084ca9838aab53bc7dfce487aa582464472d4c26dc91c63` |
| `jvm-se26-iadd.json` | `5a95707f76db0278c3ef24bf990b625aeb568df6f799e55614b5a5b14db7dc9d` |
| `iadd.bin` | `8d33f520a3c4cef80d2453aef81b612bfe1cb44c8b2025630ad38662763f13d3` |
| `iadd.decode.json` | `1d99364ca319066298069166614f4d9d5e7d05071b6604a1da05b41f2fbde5c8` |
| `iadd.projections.json` | `9dcbc34b92c27ac619b84725ade4b435c17490492a4cdd31e8765ed801b9d12a` |

The architecture and projection rationale is in [`docs/fir-multiple-projections.md`](../../../docs/fir-multiple-projections.md).
