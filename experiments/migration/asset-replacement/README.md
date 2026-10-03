# 자체 자산 인벤토리와 FPK 함수 후보 이관

2026-10-03. [자산·FIR 결정](../../../docs/owned-assets-and-structured-fir.md)을 따른다.

## 입력과 보존 범위

- 입력 commit: `96fc71f75cecdee305faf9497561c577a8955468`.
- [자산 목록](legacy-assets.json): 988개 파일의 path/size/SHA-256과 예정된 자체 표현. 이관 완료 목록이 아니다.
- [이관 lock](library-migration.json): `generic_clib_64_signatures.fpk` 한 파일의 **31,418개 후보, 15,455개 parameter**.
- 작성 형식: `.fslib` TOML schema 1. Runtime: `.fsldb` (`FSLD` v1), 자체 Rust reader.
- 전체 생성 corpus는 `artifacts/` 아래에 재생성하며 Git에 재배포하지 않는다. 제품 crate에는 자체 작성한 3-row fixture만 넣는다.

`symbol`, return type spelling, ordered parameter name/type spelling, empty/listed evidence, explicit/unknown variadic evidence를 보존한다. type spelling은 unresolved다. 매크로 이름이나 누락된 가변 인자 정보도 있으므로 함수 존재·호출 ABI·실행 의미를 추론하지 않는다. 소스에 `...`가 없으면 variadic은 false가 아닌 unknown이다.

FPK importer는 kind 1 / zlib row만 허용한다. payload hash, index/contiguous block bounds, exact stream end, decoded length, first key, global ordering/uniqueness, EOF와 record count를 검사한다. zstd/columnar/JSON/Go/type/ordinal 등 다른 payload는 거부한다. 라이선스 이관과 corpus별 타입 해석은 후속 단계다.

## 재현

```sh
python3 tools/asset_inventory.py --output artifacts/legacy-assets.json
cmp artifacts/legacy-assets.json experiments/migration/asset-replacement/legacy-assets.json
python3 tools/fsl_library_migrate.py
make library-migration-reproduce
python3 tools/library_migration_reproduce.py --fslc /path/to/fslc
fslc library-inspect artifacts/library-migration/clib64.fsldb
fslc library-query artifacts/library-migration/clib64.fsldb memcpy
```

자체 `.fslib`를 독립적으로 컴파일할 때:

```sh
python3 tools/fsl_library_migrate.py --library-source /path/to/library.fslib --output-dir artifacts/library
fslc library-inspect artifacts/library/library.fsldb
```

Python 재현은 전체 candidate 자료의 TOML parse round-trip, 바이너리와 source SHA-256, provenance/count와 고정 결과를 확인한다. Native 재현은 모든 31,418행의 parse와 `memcpy` / `malloc` / `printf` exact query를 확인한다. 이것은 제품의 `fission-signatures` loader를 교체하거나 binary에서 실제 함수 인식을 측정한 증거가 아니다.

## FSLD v1 binary

모든 정수는 little endian. string은 u32 byte length + control-free UTF-8, 최대 16,384 bytes. 패키지 최대 128 MiB.

```text
magic FSLD | u16 version=1 | u16 flags=0
source path:string | source sha256:string | source commit:string | grammar:string
u32 candidate count
repeat candidate count:
  symbol:string | return spelling:string
  u8 parameter form (0 declared-empty, 1 listed)
  u8 variadic evidence (0 unknown, 1 explicit)
  u32 parameter count
  repeat parameter count: name:string | type spelling:string
```

모든 행은 prototype candidate이고 type resolution은 unresolved다. 새 의미 종류는 schema/version 확장을 요구한다. symbol은 엄격히 증가하고 중복은 거부한다. parameter는 최대 1,024개다. declared-empty는 parameter와 explicit variadic을 허용하지 않는다. trailing bytes, unknown schema/flags/evidence는 거부한다. whole package integrity는 외부 lock/향후 profile manifest의 SHA-256으로 확인한다. 출처 hash field 자체가 패키지 인증을 제공하지 않는다.
