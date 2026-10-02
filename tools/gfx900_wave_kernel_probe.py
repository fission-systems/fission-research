#!/usr/bin/env python3
"""Extract two supported instruction rows from LLVM-compiled GPU kernels.

This does not decode or execute whole kernels. All other instructions remain
outside the selected FSL profile. Execution observations are synthetic states.
"""
import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import tempfile

from gpu_elf_probe import inspect, checked_slice, ProbeError
from gfx900_sop2_validate import run
from gfx900_wave_validate import ROOT, PROFILE


def validate(fslc, llc, objdump, work):
    source = ROOT/"experiments/gpu/gfx900-wave64/kernel-slices.ll"
    obj = work/"kernels.o"
    run([llc,"-mtriple=amdgcn-amd-amdhsa","-mcpu=gfx900","-filetype=obj",source,"-o",obj])
    disasm = run([objdump,"-d","--mcpu=gfx900",obj])
    elf = inspect(obj, include_text=False)
    sections = [s for s in elf["sections"] if s["name"]==".text"]
    if len(sections)!=1:
        raise ValueError("expected one executable text section")
    section=sections[0]
    payload=checked_slice(obj.read_bytes(),section["offset"],section["size"],"kernel text")
    package=work/"wave.fslc"
    run([fslc,"compile",ROOT/"specs/gpu/amdgcn/gfx900-vadd-u32-wave64.fsl",package])
    rows=[]
    kernel=None
    for line in disasm.splitlines():
        name=re.search(r"^[0-9a-fA-F]+ <([^>]+)>:",line)
        if name:
            kernel=name[1]
        matched=re.search(r"v_add_u32_e32 v(\d+), ([sv])(\d+), v(\d+)\s*//\s*([0-9a-fA-F]+):\s*([0-9a-fA-F]{8})\s*$",line)
        if not matched:
            continue
        dst, bank, src0, src1, address, listing_word=matched.groups()
        dst,src0,src1=int(dst),int(src0),int(src1)
        offset=int(address,16)-int(section["address"],16)
        raw=checked_slice(payload,offset,4,"vadd instruction")
        if raw != int(listing_word,16).to_bytes(4,"little"):
            raise ValueError("disassembler listing differs from object bytes")
        decoded=run([fslc,"decode-bytes",package,PROFILE,raw.hex()])
        fields={k:int(v) for k,v in re.findall(r"^  (\w+)=(\d+) ",decoded,re.M)}
        if fields!={"source0":src0+(256 if bank=="v" else 0),"source1":src1,"destination":dst}:
            raise ValueError("FSL fields differ from compiled kernel disassembly")
        count=max(dst,src1,src0 if bank=="v" else 0)+1
        for mask in [0, (1<<64)-1, 1<<63]:
            registers=[0x100000000+i for i in range(max(src0+1,1))]
            flags=[1,0]
            lanes=[0x100000000+17+i for i in range(count*64)]
            expected=list(lanes)
            for lane in range(64):
                if mask & (1<<lane):
                    left=registers[src0] if bank=="s" else lanes[src0*64+lane]
                    expected[dst*64+lane]=(left%(1<<32)+lanes[src1*64+lane]%(1<<32))%(1<<32)
            csv=lambda values: ",".join(map(str,values))
            out=run([fslc,"execute-wave",package,PROFILE,raw.hex(),"64",hex(mask),csv(registers),csv(flags),csv(lanes)])
            wanted=f"status=Success lanes=64 exec=0x{mask:x} registers={registers} flags={flags} lane_registers={expected}\n"
            if out!=wanted:
                raise ValueError("synthetic state for compiled instruction differs")
        rows.append({"kernel":kernel,"text_offset":offset,"bytes":raw.hex(),"fields":fields,"reference_cli_states":3})
    if len(rows)!=2 or {r["kernel"] for r in rows}!={"wave_add_vector","wave_add_scalar"}:
        raise ValueError("expected one supported row from each compiled kernel")
    return {"status":"passed", "profile":PROFILE,
            "source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "object_sha256":hashlib.sha256(obj.read_bytes()).hexdigest(),
            "text_sha256":hashlib.sha256(payload).hexdigest(),"rows":rows,
            "llc_version":run([llc,"--version"]).splitlines()[0],
            "objdump_version":run([objdump,"--version"]).splitlines()[0],
            "scope":"Two instruction rows only; synthetic reference CLI states, no whole-kernel or hardware execution"}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fslc",required=True,type=pathlib.Path)
    parser.add_argument("--llvm-llc",default="llc")
    parser.add_argument("--llvm-objdump",default="llvm-objdump")
    parser.add_argument("--report",type=pathlib.Path,default=ROOT/"artifacts/gfx900-wave-kernel.json")
    args=parser.parse_args()
    report={"status":"failed"}
    try:
        with tempfile.TemporaryDirectory(prefix="fission-wave-kernel-") as directory:
            report=validate(args.fslc.resolve(),args.llvm_llc,args.llvm_objdump,pathlib.Path(directory))
    except (OSError,ValueError,ProbeError,subprocess.SubprocessError) as exc:
        report["error"]=str(exc)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(report,indent=2))
    return 0 if report["status"]=="passed" else 1


if __name__=="__main__":
    raise SystemExit(main())
