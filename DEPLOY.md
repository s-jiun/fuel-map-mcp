# Kakao Cloud MCP 플랫폼 배포 가이드

## 필수 환경변수 설정

Kakao Cloud MCP 플랫폼에서 다음 환경변수를 반드시 설정해야 합니다:

### 필수 환경변수

```
KAKAO_REST_API_KEY=your_kakao_api_key
OPINET_API_KEY=your_opinet_api_key
```

### 선택 환경변수 (기본값 제공됨)

```
MCP_TRANSPORT=streamable-http
MCP_HOST=0.0.0.0
MCP_PORT=8000
```

## 배포 단계

1. **GitHub 연동**
   - Kakao Cloud MCP 플랫폼에서 이 저장소 연결
   - 브랜치: `develop` 또는 `main`

2. **환경변수 설정**
   - 플랫폼 UI에서 위의 필수 환경변수 입력
   - KAKAO_REST_API_KEY: [Kakao Developers](https://developers.kakao.com/)에서 발급
   - OPINET_API_KEY: [Opinet](https://www.opinet.co.kr/)에서 발급

3. **빌드 및 배포**
   - Dockerfile 기반 자동 빌드
   - 포트 8000 노출

## 문제 해결

### 환경변수 누락 오류
```
ValueError: KAKAO_REST_API_KEY environment variable is required.
```
→ 플랫폼에서 환경변수가 제대로 설정되었는지 확인

### 포트 접근 불가
→ `MCP_HOST=0.0.0.0`으로 설정되어 있는지 확인

### 빌드 실패
→ 로그에서 pyproj 또는 시스템 의존성 설치 오류 확인

## API 키 발급 방법

### Kakao REST API Key
1. https://developers.kakao.com/ 접속
2. 내 애플리케이션 > 앱 추가하기
3. 앱 설정 > 앱 키 > REST API 키 복사

### Opinet API Key
1. https://www.opinet.co.kr/ 접속
2. 회원가입 및 로그인
3. 오픈API > 인증키 신청
4. 발급된 키 복사