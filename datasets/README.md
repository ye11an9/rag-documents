# 데이터셋 준비

이 디렉터리에 사용 권한이 있는 보안 관련 PDF를 직접 넣으세요. PDF 파일은 라이선스와 저장소 용량을 고려해 Git에 커밋하지 않습니다.

인식하는 파일명 예시는 다음과 같습니다.

- `CVE_Program_Guide.pdf`
- `CWE_Top_25.pdf`
- `CVSS_v4.0_Specification.pdf`
- `NIST_Vulnerability_Disclosure_Guidance.pdf`
- `1346_CWE-*.pdf`처럼 숫자로 시작하는 CWE 자료
- 이름에 `cybersecurity`, `vulnerability`, `owasp`, `취약점`이 포함된 PDF

다음 천안시 실습 문서는 `datasets/`에 있더라도 인덱싱하지 않습니다.

- `2026 달라지는 천안 새로운 변화.pdf`
- `2026 주요업무계획.pdf`

동일한 CWE 관계도를 색상이나 분류만 달리해 만든 `_with_`, `_in_`, `_colored`, `_colors`, `_red`, `cats_only`, `abstraction` 파생본도 중복 검색을 막기 위해 제외합니다. 가능하면 원본 규격·지침 PDF와 독립 CWE 문서를 사용하세요.

PDF가 스캔 이미지뿐이라 텍스트 레이어가 없으면 해당 페이지는 건너뜁니다. 먼저 OCR을 적용한 뒤 다시 실행하세요.
