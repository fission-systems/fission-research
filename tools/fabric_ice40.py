#!/usr/bin/env python3
"""FIR fixture -> proved RTL -> iCE40 HX8K/CT256 bitstream, without programming.

External EDA tools and this experiment are not Fission runtime dependencies.
No board, electrical pin constraints, clocks or device runtime are implied.
"""

import argparse
import hashlib
import importlib.metadata
from importlib.resources import files
import json
from pathlib import Path
import re
import shutil
import subprocess
import tomllib

from fabric_probe import oracle, rows_for, testbench, write_vectors

ROOT = Path(__file__).resolve().parents[1]
INITIAL = ROOT / "experiments/fabric/initial-slices"
EXPERIMENT = ROOT / "experiments/fabric/ice40-hx8k"
PIN = "cb7b12f5c0c5c6790de58db3d0ef0de05e826d91"
PROVED = "SAT proof finished - no model found: SUCCESS!"
FAILED = "SAT proof finished - model found: FAIL!"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, cwd=None, timeout=120):
    p = subprocess.run(
        list(map(str, argv)), cwd=cwd, capture_output=True, text=True, timeout=timeout
    )
    if p.returncode:
        raise RuntimeError(
            f"{argv[0]} exited {p.returncode}: {(p.stdout + p.stderr)[-1800:]}"
        )
    return p.stdout + p.stderr


def widths(ports):
    result = []
    for port in ports:
        match = re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*:u([1-9][0-9]*)", port)
        if not match or not 1 <= int(match[1]) <= 64:
            raise ValueError(
                "Target fixture requires explicit unsigned 1..64-bit port widths"
            )
        result.append(int(match[1]))
    return result


def wrapper(name, ins, outs):
    ports = [f"input wire [{n - 1}:0] in{i}" for i, n in enumerate(ins)]
    ports += [f"output wire [{n - 1}:0] out{i}" for i, n in enumerate(outs)]
    wires = [f"wire [63:0] slot{i};" for i in range(len(outs))]
    bindings = [
        f".in{i}({{{64 - n}'d0,in{i}}})" if n < 64 else f".in{i}(in{i})"
        for i, n in enumerate(ins)
    ]
    bindings += [f".out{i}(slot{i})" for i in range(len(outs))]
    assigns = [f"assign out{i} = slot{i}[{n - 1}:0];" for i, n in enumerate(outs)]
    return (
        f"// Typed port adapter only; no workload semantics or state.\n"
        f"module fsl_target_{name}({','.join(ports)});\n"
        + "\n".join(wires)
        + f"\nfsl_{name} body({','.join(bindings)});\n"
        + "\n".join(assigns)
        + "\nendmodule\n"
    )


def typed_testbench(symbol, ins, outs, count):
    text = testbench(symbol, len(ins), len(outs), count)
    for i, bits in enumerate(ins):
        text = text.replace(f".in{i}(in{i})", f".in{i}(in{i}[{bits - 1}:0])")
    declarations = []
    for i, bits in enumerate(outs):
        text = text.replace(f".out{i}(out{i})", f".out{i}(hw{i})")
        declarations.append(f"wire [{bits - 1}:0] hw{i};")
        expression = f"{{{64 - bits}'d0,hw{i}}}" if bits < 64 else f"hw{i}"
        declarations.append(f"assign out{i} = {expression};")
    return text.replace(f"{symbol} dut", "\n".join(declarations) + f"\n{symbol} dut")


def prove(yosys, directory, inputs, gold, gate, label, expect_failure=False):
    script = (
        f"read_verilog {' '.join(inputs)}; "
        f"miter -equiv -make_assert -flatten {gold} {gate} miter; "
        "hierarchy -top miter; proc; opt; wreduce; opt; "
        "sat -verify -prove-asserts -set-def-inputs -timeout 15 "
        f"-show-inputs -show-outputs -dump_json {label}-counterexample.json"
    )
    (directory / f"{label}.ys").write_text(script + "\n")
    p = subprocess.run(
        [str(yosys), "-Q", "-T", f"{label}.ys"],
        cwd=directory,
        capture_output=True,
        text=True,
        timeout=45,
    )
    log = p.stdout + p.stderr
    (directory / f"{label}.log").write_text(log)
    if expect_failure:
        if (
            p.returncode == 0
            or FAILED not in log
            or not (directory / f"{label}-counterexample.json").is_file()
        ):
            raise ValueError(
                f"{label}: mutant was not rejected with a SAT counterexample"
            )
        return "counterexample"
    if p.returncode or PROVED not in log:
        raise ValueError(f"{label}: proof failed or timed out: {log[-1500:]}")
    return "proved_all_two_valued_inputs"


def tool_provenance():
    distributions = {}
    for name in ["yowasp-yosys", "yowasp-nextpnr-ice40", "yowasp-runtime", "wasmtime"]:
        dist = importlib.metadata.distribution(name)
        tracked = {}
        for member in dist.files or []:
            path = dist.locate_file(member)
            if (
                str(member).endswith(".wasm")
                or "license" in str(member).lower()
                or "share/ice40/" in str(member)
                and path.is_file()
            ):
                tracked[str(member)] = sha(path)
        distributions[name] = {
            "version": dist.version,
            "object_and_license_sha256": tracked,
        }
    return distributions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc", type=Path, required=True)
    parser.add_argument("--compiler-root", type=Path, required=True)
    parser.add_argument("--tool-dir", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    cli = args.fslc.resolve()
    compiler = args.compiler_root.resolve()
    # Yosys command files use relative fixed names; paths from callers never enter scripts.
    root = args.work.resolve()
    if root.exists():
        raise ValueError(
            "Use a fresh work directory; existing files are never overwritten"
        )
    revision = run(["git", "-C", compiler, "rev-parse", "HEAD"]).strip()
    if revision != PIN or run(["git", "-C", compiler, "status", "--porcelain"]).strip():
        raise ValueError("Expected the clean pinned experimental compiler")
    frozen = [
        Path(__file__),
        ROOT / "tools/fabric_probe.py",
        INITIAL / "axes.toml",
        INITIAL / "kernels.fsl",
        EXPERIMENT / "oracles.v",
        EXPERIMENT / "tool-requirements.lock.txt",
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in frozen}
    binary_hash = sha(cli)
    tool_dir = args.tool_dir.resolve()
    tools = {
        n: tool_dir / ("yowasp-" + n)
        for n in ["yosys", "nextpnr-ice40", "icepack", "iceunpack"]
    }
    for path in tools.values():
        if not path.is_file():
            raise ValueError(f"Missing external tool: {path}")
    iverilog, vvp = shutil.which("iverilog"), shutil.which("vvp")
    if not iverilog or not vvp:
        raise ValueError("Icarus Verilog / vvp required")
    cells = Path(str(files("yowasp_yosys").joinpath("share/ice40/cells_sim.v")))
    provenance = tool_provenance()
    root.mkdir(parents=True)
    package = root / "kernels.fslc"
    run([cli, "compile", INITIAL / "kernels.fsl", package])
    axes = tomllib.loads((INITIAL / "axes.toml").read_text())["axis"]
    results = []
    for axis in axes:
        name = axis["kernel"]
        if not re.fullmatch(r"[a-z][a-z0-9_]*", name):
            raise ValueError("Invalid fixture identifier")
        ins, outs = widths(axis["inputs"]), widths(axis["outputs"])
        directory = root / name
        directory.mkdir()
        emitted = json.loads(
            run(
                [
                    cli,
                    "emit-fabric",
                    package,
                    name,
                    "fsl_" + name,
                    directory / "design.v",
                ]
            )
        )
        if emitted["input_slots"] != len(ins) or emitted["output_slots"] != len(outs):
            raise ValueError("Typed adapter arity differs from canonical FIR")
        shutil.copyfile(EXPERIMENT / "oracles.v", directory / "oracles.v")
        proof = prove(
            tools["yosys"],
            directory,
            ["design.v", "oracles.v"],
            "fsl_" + name,
            "oracle_" + name,
            "oracle-proof",
        )
        # Corrupt one output bit; failure must be a counterexample, never a timeout.
        native = (directory / "design.v").read_text()
        mutant = native.replace(f"module fsl_{name}(", f"module mutant_{name}(")
        mutant, changes = re.subn(
            r"assign out0 = (.*);", r"assign out0 = (\1) ^ 64'd1;", mutant
        )
        if changes != 1:
            raise ValueError("Mutation boundary not found")
        (directory / "mutant.v").write_text(mutant)
        mutation = prove(
            tools["yosys"],
            directory,
            ["mutant.v", "oracles.v"],
            "mutant_" + name,
            "oracle_" + name,
            "mutation",
            True,
        )
        (directory / "adapter.v").write_text(wrapper(name, ins, outs))
        top = "fsl_target_" + name
        script = (
            f"read_verilog design.v adapter.v; synth_ice40 -device hx -top {top} "
            "-json mapped.json; check -assert; write_verilog -noattr mapped.v; "
            "tee -o mapped-stat.json stat -json"
        )
        (directory / "synthesis.ys").write_text(script + "\n")
        (directory / "synthesis.log").write_text(
            run([tools["yosys"], "-Q", "-T", "synthesis.ys"], directory)
        )
        mapped = json.loads((directory / "mapped.json").read_text())["modules"][top]
        if {cell["type"] for cell in mapped["cells"].values()} - {
            "$scopeinfo",
            "SB_LUT4",
            "SB_CARRY",
        }:
            raise ValueError(
                "Combinational target unexpectedly contains state or unsupported cells"
            )
        rows = rows_for(name, len(ins))
        write_vectors(directory, name, rows)
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
        expected_csv = "".join(
            ",".join(map(str, oracle(name, row))) + "\n" for row in rows
        )
        if (directory / "reference.csv").read_text() != expected_csv:
            raise ValueError("Native FIR differs from independent integer oracle")
        (directory / "tb.v").write_text(typed_testbench(top, ins, outs, len(rows)))
        run(
            [iverilog, "-g2012", "-s", "tb", "-o", "sim", cells, "mapped.v", "tb.v"],
            directory,
        )
        simulation = run([vvp, "sim"], directory)
        if f"PASS rows={len(rows)}" not in simulation:
            raise ValueError("Mapped simulation did not report the expected case count")
        (directory / "mapped-simulation.log").write_text(simulation)
        pnr_command = [
            tools["nextpnr-ice40"],
            "--hx8k",
            "--package",
            "ct256",
            "--json",
            "mapped.json",
            "--top",
            top,
            "--seed",
            "1",
            "--pcf-allow-unconstrained",
            "--asc",
            "design.asc",
            "--write",
            "routed.json",
            "--report",
            "pnr-report.json",
        ]
        (directory / "pnr.log").write_text(run(pnr_command, directory))
        run([tools["icepack"], "design.asc", "design.bin"], directory)
        run([tools["iceunpack"], "design.bin", "unpacked.asc"], directory)
        run([tools["icepack"], "unpacked.asc", "repacked.bin"], directory)
        if (directory / "design.bin").read_bytes() != (
            directory / "repacked.bin"
        ).read_bytes():
            raise ValueError("Packed configuration round-trip differs")
        pnr = json.loads((directory / "pnr-report.json").read_text())
        tracked = [
            "design.v",
            "adapter.v",
            "oracle-proof.ys",
            "oracle-proof.log",
            "mutation.log",
            "mutant.v",
            "mutation.ys",
            "mutation-counterexample.json",
            "synthesis.ys",
            "mapped.json",
            "mapped.v",
            "mapped-stat.json",
            "mapped-simulation.log",
            "pnr.log",
            "pnr-report.json",
            "routed.json",
            "design.asc",
            "design.bin",
            "input.csv",
            "reference.csv",
            "tb.v",
        ]
        result = {
            "kernel": name,
            "oracle_equivalence": proof,
            "mutation_control": mutation,
            "input_widths": ins,
            "output_widths": outs,
            "mapped_simulation_cases": len(rows),
            "device": "iCE40HX8K",
            "package": "CT256",
            "pnr_seed": 1,
            "utilization": pnr["utilization"],
            "bitstream_bytes": (directory / "design.bin").stat().st_size,
            "pack_unpack_repack": "byte_identical",
            "board_pin_constraints": False,
            "device_execution": False,
            "files": {n: sha(directory / n) for n in tracked},
        }
        results.append(result)
        print(
            json.dumps(
                {
                    k: result[k]
                    for k in [
                        "kernel",
                        "oracle_equivalence",
                        "mapped_simulation_cases",
                        "bitstream_bytes",
                    ]
                }
            ),
            flush=True,
        )
    if (
        run(["git", "-C", compiler, "rev-parse", "HEAD"]).strip() != revision
        or run(["git", "-C", compiler, "status", "--porcelain"]).strip()
        or sha(cli) != binary_hash
        or any(sha(ROOT / name) != value for name, value in hashes.items())
    ):
        raise ValueError("Compiler or inputs changed during measurement")
    report = {
        "schema": "fission.fabric.ice40.v1",
        "compiler_commit": revision,
        "compiler_dirty": False,
        "compiler_executable_sha256": binary_hash,
        "package_sha256": sha(package),
        "inputs": hashes,
        "tools": provenance,
        "versions": {
            "yosys": run([tools["yosys"], "-V"]).strip(),
            "nextpnr": run([tools["nextpnr-ice40"], "--version"]).strip(),
            "iverilog": run([iverilog, "-V"]).splitlines()[0],
        },
        "results": results,
        "proofs": len(results),
        "counterexample_controls": len(results),
        "bitstreams_created": len(results),
        "mapped_simulation_cases": sum(r["mapped_simulation_cases"] for r in results),
        "device_execution": False,
        "board_pin_constraints": False,
        "formal_scope": "Generated combinational RTL versus independently authored unsigned bit-vector fixture formulae; all two-valued 64-bit slot inputs; not a proof of the compiler, synthesis, routing, bitstream semantics, native binaries or continuous dynamics",
        "timing_scope": "No clocks or external I/O delay constraints; no system timing closure claim",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
