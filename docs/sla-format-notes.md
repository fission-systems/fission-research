# SLA 바이너리 포렌식 노트

Date: 2026-09-30

## 확인된 외피

검사한 Ghidra 컴파일 산출물은 다음 외피를 가진다.

1. 첫 세 바이트는 ASCII `sla`이다.
2. 네 번째 바이트는 포맷 버전이다. 로컬 스냅샷에서 관찰한 값은 `4`다.
3. 나머지는 zlib 스트림이다.
4. 압축을 푼 페이로드는 텍스트 XML이 아니라 숫자 element/attribute ID 기반의 packed 트리다.

Ghidra 12.0.4 공식 [`SlaFormat.java`](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.0.4_build/Ghidra/Framework/SoftwareModeling/src/main/java/ghidra/pcode/utils/SlaFormat.java)는 v4를 압축 및 packed 파일 형식으로 설명한다. 같은 릴리스의 [`PackedDecode.java`](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.0.4_build/Ghidra/Framework/SoftwareModeling/src/main/java/ghidra/program/model/pcode/PackedDecode.java) / [`PackedEncode.java`](https://github.com/NationalSecurityAgency/ghidra/blob/Ghidra_12.0.4_build/Ghidra/Framework/SoftwareModeling/src/main/java/ghidra/program/model/pcode/PackedEncode.java)는 토큰 헤더와 타입 코드의 기준 정의다. 프로브의 외피와 토큰 해석은 이 구현과 대조했다. 포맷 테이블은 버전 관리 대상으로 두며, v4가 아닌 SLA는 현재 읽지 않도록 실패 처리한다.

2026-09-30 기준 미러에 있는 SLA 133개를 프로브로 전부 읽었다. 모두 v4이며 parse error는 없었다. 전체 통계와 각 입력 SHA-256은 [`SLA corpus scan`](../notes/sla-corpus-scan-2026-09-30.md)에 기록했다.

## Packed 트리에서 역추적할 항목

기본 헤더의 상위 2비트가 element 시작, element 종료, attribute를 구분한다. 나머지 헤더 비트에는 ID 일부가 오며, 확장 비트가 있으면 추가 ID 바이트를 읽는다. Attribute 값은 타입 코드와 길이를 가지며, 정수와 문자열 길이는 7-bit group으로 인코딩된다. 특수 주소 공간은 값 바이트 없이 타입 코드의 하위 니블에 식별자를 담는다. element/attribute ID의 **의미 이름**은 별도 포맷 상수 테이블을 대조해야 얻을 수 있다.

프로브는 처음에는 ID를 이름으로 오해하지 않고 원시 숫자 형태와 집계만 보존한다. 이후 공식 소스 테이블을 출처 정보와 함께 스키마로 옮긴다.

## 지금부터 만들 프로브

[`../tools/sla_probe.py`](../tools/sla_probe.py)는 다음을 출력한다.

- 파일 및 압축 해제 페이로드 SHA-256, 버전, 압축/평문 크기
- root element ID, node 수, 최대 깊이
- element ID·attribute ID·attribute 타입 빈도
- UTF-8 문자열 개수/최대 길이
- 필요할 때 numeric ID를 그대로 둔 JSON 트리

입력 크기, 압축 해제 크기, 중첩 깊이를 제한해 잘못된 산출물이 연구 도구를 과도하게 소모하지 않게 한다. 알려지지 않은 타입이나 트렁케이션은 조용히 건너뛰지 않고 실패로 표시한다.

## 미해결 질문

- 포맷 버전별 element/attribute schema와 호환 경계는 무엇인가?
- 디버그 XML 출력 모드는 같은 구조를 어떻게 표현하는가?
- source file/line, context, token, constructor, decision tree, ConstructTpl의 연결 키는 무엇인가?
- `.slaspec`에서 `.sla` 컴파일 중 어떤 정보가 정규화·확장·삭제되는가?
- 매크로 확장 이후 원본 소스와 컴파일 생성 의미 조각을 어떻게 연결하는가?
- 검증 규칙과 실제 컴파일러 동작 사이의 차이를 어떻게 추적할 것인가?

## 1차 측정에서 제외

SLA 페이로드를 성공적으로 파싱하는 것만으로 기계어 의미를 완전히 복원했다고 보지 않는다. 도메인 의미, 예외, 구현 의존 동작, 비트 필드의 endian 규칙을 별도로 검증해야 한다.
