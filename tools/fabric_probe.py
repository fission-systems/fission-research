#!/usr/bin/env python3
"""Bounded authored FIR/HDL experiment. Never program hardware or produce bitstreams."""

import argparse
from fractions import Fraction
import hashlib
import itertools
import json
import math
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = ROOT / "experiments/fabric/initial-slices"
MASK64 = (1 << 64) - 1


def digest(data):
    return hashlib.sha256(data).hexdigest()


def run(argv, cwd=None, timeout=180):
    completed = subprocess.run(
        list(map(str, argv)), cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    if completed.returncode:
        raise RuntimeError(
            f"{argv[0]} failed ({completed.returncode}): {completed.stderr[-3000:]} {completed.stdout[-1000:]}"
        )
    return completed.stdout


def oracle(name, raw):
    if name == "fpga_add":
        return [(raw[0] + raw[1]) & 255]
    if name == "dsp_sat_add":
        return [min((raw[0] & 255) + (raw[1] & 255), 255)]
    if name == "tensor_dot2":
        a, b, c, d = [v & 255 for v in raw]
        return [a * c + b * d]
    if name == "asic_mac":
        return [((raw[0] & 65535) * (raw[1] & 65535) + (raw[2] & 65535)) & 65535]
    if name == "lif_step":
        v, current = [x & 255 for x in raw]
        pre = (3 * v) // 4 + current
        return [0 if pre >= 100 else pre, int(pre >= 100)]
    if name == "pim_bank_xor":
        return [(raw[0] ^ raw[1]) & 0xFFFFFFFF]
    if name == "rc_euler_step":
        return [(3 * (raw[0] & 65535) + (raw[1] & 65535)) // 4]
    if name == "dataflow_diamond":
        a, b = [x & 65535 for x in raw]
        return [((a + b) * (a - b)) & 65535]
    if name.startswith("primitive_"):
        _, operation, bits = name.split("_")
        bits = int(bits)
        mask = (1 << bits) - 1
        a, b = [x & mask for x in raw]
        if operation == "mul":
            return [(a * b) & mask]
        if b >= bits:
            return [0]
        return [((a << b) & mask) if operation == "shl" else a >> b]
    if name == "signed_view":
        a = raw[0] & 255
        signed = a if a < 128 else a - 256
        return [signed & 65535, int(signed < 0)]
    raise ValueError(name)


def rows_for(name, arity):
    if name in ["fpga_add", "dsp_sat_add"]:
        return [list(pair) for pair in itertools.product(range(256), repeat=2)]
    boundary = [
        0,
        1,
        3,
        7,
        8,
        31,
        32,
        63,
        64,
        65,
        99,
        100,
        127,
        128,
        255,
        256,
        65535,
        65536,
        1 << 63,
        MASK64,
    ]
    rows = [[v] * arity for v in boundary]
    if arity == 2:
        rows += [list(pair) for pair in itertools.product(boundary, repeat=2)]
    rng = random.Random(0xF51F15 + sum(name.encode()))
    rows += [[rng.getrandbits(64) for _ in range(arity)] for _ in range(2048)]
    if name in ["lif_step", "rc_euler_step"]:
        state = 0
        for tick in range(128):
            current = (
                [0, 10, 50, 100, 255][tick % 5]
                if name == "lif_step"
                else (65535 if tick < 64 else 0)
            )
            rows.append([state, current])
            state = oracle(name, [state, current])[0]
    return rows


def extra_source():
    profiles = []
    names = []
    for bits in [1, 8, 16, 32, 64]:
        for operation, spelling in [
            ("mul", "mul.wrap"),
            ("shl", "shl"),
            ("lshr", "lshr"),
        ]:
            name = f"primitive_{operation}_{bits}"
            opcode = 32 + len(profiles)
            profiles.append(
                f'instruction {name} {{ opcode {opcode}; mnemonic "{name}"; evidence "self-authored" "synthetic" "fabric-v1" "Primitive width and shift boundary qualification"; semantics {{ %b:u{bits}=stack.pop; %a:u{bits}=stack.pop; %v:u{bits}=u{bits}.{spelling} %a,%b; stack.push %v; }} }}'
            )
            names.append((name, opcode, 2))
    profiles.append(
        'instruction signed_view { opcode 64; mnemonic "signed.view"; evidence "self-authored" "synthetic" "fabric-v1" "Signed conversion and comparison qualification"; semantics { %a:i8=stack.pop; %wide:i16=int.sext %a; %zero:i16=int.const 0; %less:u1=int.slt %wide,%zero; stack.push %wide; stack.push %less; } }'
    )
    names.append(("signed_view", 64, 1))
    return (
        "language fabric.qualification { byte_order little; address_unit byte; "
        + "\n".join(profiles)
        + "\n}",
        names,
    )


def write_vectors(directory, name, rows):
    expected = [oracle(name, row) for row in rows]
    (directory / "input.csv").write_text(
        "".join(",".join(map(str, row)) + "\n" for row in rows)
    )
    (directory / "inputs.hex").write_text(
        "".join(f"{v:016x}\n" for row in rows for v in row)
    )
    (directory / "expected.hex").write_text(
        "".join(f"{v:016x}\n" for row in expected for v in row)
    )
    with (directory / "vectors.bin").open("wb") as stream:
        for inputs, outputs in zip(rows, expected):
            for value in inputs + outputs:
                stream.write(struct.pack("<Q", value))
    return expected


def testbench(symbol, inputs, outputs, rows):
    signals = "\n".join(
        [f"reg [63:0] in{i};" for i in range(inputs)]
        + [f"wire [63:0] out{i};" for i in range(outputs)]
    )
    ports = ",".join(
        [f".in{i}(in{i})" for i in range(inputs)]
        + [f".out{i}(out{i})" for i in range(outputs)]
    )
    load = " ".join(f"in{i}=stim[index*{inputs}+{i}];" for i in range(inputs))
    checks = "\n".join(
        f'if (out{i} !== expected[index*{outputs}+{i}]) $fatal(1,"row=%0d output={i} got=%h expected=%h",index,out{i},expected[index*{outputs}+{i}]);'
        for i in range(outputs)
    )
    return f"""module tb;
{signals}
{symbol} dut({ports});
reg [63:0] stim[0:{inputs * rows - 1}]; reg [63:0] expected[0:{outputs * rows - 1}]; integer index;
initial begin
$readmemh("inputs.hex",stim); $readmemh("expected.hex",expected);
for(index=0;index<{rows};index=index+1) begin {load} #1; {checks} end
$display("PASS rows={rows}"); $finish;
end
endmodule
"""


def host_qualification(directory, inputs, outputs, clang, rustc):
    (directory / "host.c").write_text(f"""#include <stdio.h>
#include <string.h>
#include "projection.c"
int main(void) {{ FILE *f=fopen("vectors.bin","rb"); if(!f)return 9; unsigned rows=0; uint64_t input[{inputs}], expected[{outputs}];
while(fread(input,sizeof(uint64_t),{inputs},f)=={inputs}) {{ if(fread(expected,sizeof(uint64_t),{outputs},f)!={outputs})return 8; uint64_t stack[64]={{0}}; memcpy(stack,input,sizeof(input)); size_t depth={inputs};
if(fsl_execute(stack,&depth,64)!=0 || depth!={outputs} || memcmp(stack,expected,sizeof(expected)))return 7; rows++; }} fclose(f); printf("PASS rows=%u\\n",rows); return 0; }}
""")
    (directory / "host.rs").write_text(f"""include!("projection.rs");
fn main() {{ let bytes=std::fs::read("vectors.bin").unwrap(); let size=8*({inputs}+{outputs}); assert_eq!(bytes.len()%size,0);
for row in bytes.chunks_exact(size) {{ let mut stack=[0u64;64]; for i in 0..{inputs} {{stack[i]=u64::from_le_bytes(row[8*i..8*i+8].try_into().unwrap());}} let mut depth={inputs}; assert_eq!(fsl_execute(&mut stack,&mut depth),0); assert_eq!(depth,{outputs});
for i in 0..{outputs} {{let p=8*({inputs}+i); assert_eq!(stack[i],u64::from_le_bytes(row[p..p+8].try_into().unwrap()));}} }} println!("PASS rows={{}}",bytes.len()/size); }}
""")
    checks = 0
    for optimization in [0, 2]:
        run(
            [
                clang,
                f"-O{optimization}",
                "-fsanitize=undefined",
                "-fno-sanitize-recover=all",
                "host.c",
                "-o",
                f"host-c-{optimization}",
            ],
            cwd=directory,
        )
        run([directory / f"host-c-{optimization}"], cwd=directory)
        run(
            [
                rustc,
                "--edition=2021",
                "-Awarnings",
                "-C",
                f"opt-level={optimization}",
                "host.rs",
                "-o",
                f"host-rust-{optimization}",
            ],
            cwd=directory,
        )
        run([directory / f"host-rust-{optimization}"], cwd=directory)
        checks += 2
    return checks


def probe_kernel(cli, package, name, opcode, rows, directory, args, synthesize):
    directory.mkdir()
    expected = write_vectors(directory, name, rows)
    metadata = json.loads(
        run([cli, "emit-fabric", package, name, "fsl_" + name, directory / "design.v"])
    )
    run(
        [
            cli,
            "emit-dataflow",
            package,
            name,
            "fsl_" + name,
            directory / "dependencies.dot",
        ]
    )
    run(
        [
            cli,
            "run-fabric",
            package,
            name,
            directory / "input.csv",
            directory / "reference.csv",
        ]
    )
    got = [
        [int(v) for v in line.split(",")]
        for line in (directory / "reference.csv").read_text().splitlines()
    ]
    if got != expected:
        raise ValueError(name + " FIR/reference oracle mismatch")
    inputs, outputs = metadata["input_slots"], metadata["output_slots"]
    if inputs != len(rows[0]) or outputs != len(expected[0]):
        raise ValueError("Port extent mismatch")
    (directory / "tb.v").write_text(
        testbench("fsl_" + name, inputs, outputs, len(rows))
    )
    run(
        [args.iverilog, "-g2005-sv", "-s", "tb", "-o", "rtl.vvp", "design.v", "tb.v"],
        cwd=directory,
    )
    run([args.vvp, "rtl.vvp"], cwd=directory)
    for language, suffix in [("c", "c"), ("rust", "rs")]:
        run(
            [
                cli,
                "emit",
                package,
                f"0x{opcode:02x}",
                language,
                directory / ("projection." + suffix),
            ]
        )
    host_builds = host_qualification(directory, inputs, outputs, args.clang, args.rustc)
    cells = None
    if synthesize:
        script = f"read_verilog design.v; synth -top fsl_{name} -noabc; check -assert; tee -o synthesis-stat.json stat -json; write_verilog -noattr netlist.v"
        log = run([args.yosys, "-p", script], cwd=directory)
        (directory / "synthesis.log").write_text(log)
        statistics = json.loads((directory / "synthesis-stat.json").read_text())
        modules = statistics["modules"]
        cells = sum(m.get("num_cells", 0) for m in modules.values())
        run(
            [
                args.iverilog,
                "-g2005-sv",
                "-s",
                "tb",
                "-o",
                "netlist.vvp",
                "netlist.v",
                "tb.v",
            ],
            cwd=directory,
        )
        run([args.vvp, "netlist.vvp"], cwd=directory)
    print(
        json.dumps(
            {
                "kernel": name,
                "cases": len(rows),
                "generic_synthesis": synthesize,
                "status": "matched",
            }
        ),
        flush=True,
    )
    return {
        "kernel": name,
        "cases": len(rows),
        "input_slots": inputs,
        "output_slots": outputs,
        "fir_oracle": "matched",
        "rtl_oracle": "matched",
        "host_builds": host_builds,
        "host_executions": len(rows) * host_builds,
        "generic_synthesis": synthesize,
        "synthesized_netlist_oracle": "matched" if synthesize else "not-performed",
        "generic_cells": cells,
        "target_hardware_execution": False,
        "files": {
            f.name: digest(f.read_bytes())
            for f in directory.iterdir()
            if f.name
            in [
                "design.v",
                "dependencies.dot",
                "input.csv",
                "reference.csv",
                "netlist.v",
                "synthesis-stat.json",
                "projection.c",
                "projection.rs",
                "tb.v",
            ]
        },
    }


def refusal_probes(cli, root):
    bodies = [
        "quantum.h 0;",
        "block entry() { %v:u8=int.const 1; stack.push %v; return; }",
        "%a:u64=stack.pop; %v:u8=memory.load.le %a; stack.push %v;",
        "%v:u1=flag.read 0; flag.write 0,%v;",
    ]
    checks = 0
    for index, body in enumerate(bodies):
        source = root / f"refuse-{index}.fsl"
        package = root / f"refuse-{index}.fslc"
        output = root / f"refuse-{index}.v"
        source.write_text(
            'language refuse { byte_order little; address_unit byte; instruction reject { opcode 1; mnemonic "reject"; evidence "self" "synthetic" "v1" "Refusal boundary"; semantics { '
            + body
            + " } } }"
        )
        run([cli, "compile", source, package])
        output.write_text("preserve-this-file")
        result = subprocess.run(
            [
                str(cli),
                "emit-fabric",
                str(package),
                "reject",
                "fsl_refuse",
                str(output),
            ],
            capture_output=True,
        )
        if result.returncode == 0 or output.read_text() != "preserve-this-file":
            raise ValueError("Unsupported effect emitted HDL")
        checks += 1
    return checks


def analog_comparison():
    quantized = 0
    euler = Fraction(0)
    maximum_quantization = Fraction(0)
    maximum_continuous = 0.0
    for tick in range(1, 65):
        quantized = (3 * quantized + 65535) // 4
        euler = (3 * euler + 65535) / 4
        maximum_quantization = max(maximum_quantization, euler - quantized)
        exact = 65535 * (1 - math.exp(-tick / 4))
        maximum_continuous = max(maximum_continuous, abs(float(euler) - exact) / 256)
    if not 0 <= maximum_quantization < 4:
        raise ValueError("Discrete quantization envelope failed")
    return {
        "model": "tau*dx/dt=u-x; dt=1ms tau=4ms; step 0 to 65535/256 volt",
        "steps": 64,
        "maximum_quantization_error_codes": float(maximum_quantization),
        "maximum_euler_vs_exact_step_voltage_error": maximum_continuous,
        "quantization_envelope_codes": 4,
        "continuous_equivalence": False,
        "hardware_execution": False,
        "scope": "Separate authored approximation experiment, not an analog solver or device measurement",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    for name in ["iverilog", "vvp", "yosys", "clang", "rustc"]:
        parser.add_argument("--" + name, default=shutil.which(name))
    parser.add_argument(
        "--report", type=Path, default=ROOT / "artifacts/fabric-probe.json"
    )
    parser.add_argument("--work", type=Path)
    args = parser.parse_args()
    if sys.byteorder != "little":
        raise ValueError("Host binary-vector harness currently requires little-endian")
    for name in ["iverilog", "vvp", "yosys", "clang", "rustc"]:
        value = getattr(args, name)
        if not value:
            raise ValueError("Required reference tool missing: " + name)
        setattr(args, name, str(Path(value).absolute()))
    cli = args.fslc.resolve()
    source = EXPERIMENT / "kernels.fsl"
    compiler_commit = run(
        ["git", "-C", args.compiler_root, "rev-parse", "HEAD"]
    ).strip()
    compiler_status = run(["git", "-C", args.compiler_root, "status", "--porcelain"])
    binary_hash = digest(cli.read_bytes())
    frozen_inputs = {
        path: digest(path.read_bytes())
        for path in [source, EXPERIMENT / "axes.toml", Path(__file__)]
    }
    root = (
        args.work.resolve()
        if args.work
        else Path(tempfile.mkdtemp(prefix="fission-fabric-"))
    )
    root.mkdir(exist_ok=True, parents=True)
    package = root / "kernels.fslc"
    run([cli, "compile", source, package])
    axes = tomllib.loads((EXPERIMENT / "axes.toml").read_text())["axis"]
    native_axes = json.loads(run([cli, "fabric-axes"]))["axes"]
    if {a["id"] for a in axes} != {a["id"] for a in native_axes}:
        raise ValueError("Axis registry mismatch")
    results = []
    for axis in axes:
        name = axis["kernel"]
        rows = rows_for(name, len(axis["inputs"]))
        results.append(
            probe_kernel(
                cli, package, name, axis["opcode"], rows, root / name, args, True
            )
        )
    extras, names = extra_source()
    extra = root / "qualification.fsl"
    extra.write_text(extras)
    extra_package = root / "qualification.fslc"
    run([cli, "compile", extra, extra_package])
    for name, opcode, arity in names:
        results.append(
            probe_kernel(
                cli,
                extra_package,
                name,
                opcode,
                rows_for(name, arity),
                root / name,
                args,
                False,
            )
        )
    refusals = refusal_probes(cli, root)
    if (
        run(["git", "-C", args.compiler_root, "rev-parse", "HEAD"]).strip()
        != compiler_commit
        or run(["git", "-C", args.compiler_root, "status", "--porcelain"])
        != compiler_status
        or digest(cli.read_bytes()) != binary_hash
        or any(
            digest(path.read_bytes()) != value for path, value in frozen_inputs.items()
        )
    ):
        raise ValueError("Compiler or experimental inputs changed during measurement")
    report = {
        "schema": "fission.fabric.probe.v1",
        "compiler_commit": compiler_commit,
        "compiler_dirty": bool(compiler_status.strip()),
        "compiler_executable_sha256": binary_hash,
        "source_sha256": digest(source.read_bytes()),
        "package_sha256": digest(package.read_bytes()),
        "probe_sha256": digest(Path(__file__).read_bytes()),
        "axes_sha256": digest((EXPERIMENT / "axes.toml").read_bytes()),
        "axes": native_axes,
        "tools": {
            "iverilog": run([args.iverilog, "-V"]).splitlines()[0],
            "yosys": run([args.yosys, "-V"]).strip(),
            "clang": run([args.clang, "--version"]).splitlines()[0],
            "rustc": run([args.rustc, "--version"]).strip(),
        },
        "results": results,
        "refusal_checks": refusals,
        "total_cases": sum(r["cases"] for r in results),
        "host_executions": sum(r["host_executions"] for r in results),
        "c_undefined_sanitizer": "fatal",
        "generic_synthesis_count": sum(r["generic_synthesis"] for r in results),
        "analog_approximation": analog_comparison(),
        "target_hardware_execution": False,
        "bitstreams_created": 0,
        "scope": "Authored bit-vector kernels, scalar elaborations and approximation/placement contracts; not vendor device support or decompiler quality evidence",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: report[k]
                for k in [
                    "total_cases",
                    "host_executions",
                    "generic_synthesis_count",
                    "refusal_checks",
                    "analog_approximation",
                    "target_hardware_execution",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
