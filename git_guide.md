# Chapter. GitHub 협업 가이드

## 1. Git과 GitHub 이해하기

* Git이란?
* GitHub란?
* Git과 GitHub의 차이
* 협업 흐름 이해
* Local / Remote Repository
* Commit, Branch, Merge 개념

---

## 2. Git 설치

### Windows

### macOS

Git 설치 확인

```bash
git --version
```

Git 최초 설정

```bash
git config --global user.name "홍길동"
git config --global user.email "hong@example.com"

git config --list
```

---

## 3. GitHub Repository 생성

* Repository 생성
* Public / Private 차이
* README 생성
* .gitignore 생성
* License

Repository 구조

```
smu-ai-agent/
├── README.md
├── requirements.txt
├── app.py
├── agent/
├── tools/
├── prompts/
├── data/
└── docs/
```

---

## 4. Collaborator 초대

GitHub 화면 캡처 위치

```
Settings
    ↓
Collaborators
    ↓
Add People
```

권한 종류

* Read
* Triage
* Write
* Maintain
* Admin

실습에서는 Write 권한 부여

---

## 5. 프로젝트 Clone

HTTPS

```bash
git clone https://github.com/username/project.git
```

SSH

```bash
git clone git@github.com:username/project.git
```

이동

```bash
cd project
```

원격 저장소 확인

```bash
git remote -v
```

---

## 6. Branch 전략

왜 Branch를 사용하는가?

main에서는 작업하지 않는 이유

브랜치 생성

```bash
git checkout -b feature/rag
```

또는

```bash
git switch -c feature/rag
```

브랜치 목록

```bash
git branch
```

원격 포함

```bash
git branch -a
```

브랜치 이동

```bash
git switch feature/rag
```

삭제

```bash
git branch -d feature/rag
```

---

## 7. 개발 시작

현재 상태 확인

```bash
git status
```

수정 파일 확인

```bash
git diff
```

추적 시작

```bash
git add app.py
```

전체 추가

```bash
git add .
```

---

## 8. Commit

커밋

```bash
git commit -m "feat: Add PDF Retriever"
```

로그 보기

```bash
git log
```

한 줄 보기

```bash
git log --oneline
```

최근 Commit 수정

```bash
git commit --amend
```

---

## 9. Push

처음 Push

```bash
git push -u origin feature/rag
```

이후

```bash
git push
```

원격 Branch 확인

```bash
git branch -r
```

---

## 10. Pull Request

GitHub 화면 설명

Compare & Pull Request

PR 작성법

좋은 제목

```
feat: Implement PDF Retriever
```

좋은 내용

```
## 변경 내용

- PDF Retriever 구현
- Chroma 연결
- 테스트 완료

## 확인 사항

- 정상 동작 확인 부탁드립니다.
```

---

## 11. Code Review

Review

Comment

Approve

Request Changes

리뷰 예시

```
변수명을 조금 더 명확하게 수정하면 좋겠습니다.

예외처리를 추가해주세요.

중복 코드를 함수로 분리하면 좋겠습니다.
```

---

## 12. Merge

Merge 방법

* Create Merge Commit
* Squash Merge
* Rebase Merge

교육에서는

Create Merge Commit 추천

---

## 13. 최신 코드 가져오기

Main 이동

```bash
git switch main
```

최신 가져오기

```bash
git pull origin main
```

작업 브랜치 이동

```bash
git switch feature/rag
```

main 반영

```bash
git merge main
```

또는

```bash
git rebase main
```

---

## 14. Conflict 해결

충돌 예시

```text
<<<<<<< HEAD
print("A")
=======
print("B")
>>>>>>> main
```

수정 후

```bash
git add .

git commit
```

---

## 15. 프로젝트 종료 후 Branch 삭제

로컬 삭제

```bash
git branch -d feature/rag
```

원격 삭제

```bash
git push origin --delete feature/rag
```

---

# GitHub Desktop 사용법 (선택)

* Clone
* Commit
* Push
* Pull
* Branch
* PR

---

# .gitignore 작성

예시

```gitignore
__pycache__/
*.pyc

.env
.env.*

.venv/
venv/

.idea/
.vscode/

*.log

.DS_Store
```

---

# AI Agent 프로젝트 권장 Branch 전략

```
main
│
├── feature/agent
├── feature/rag
├── feature/tool
├── feature/ui
├── feature/docs
└── feature/test
```

---

# Commit Convention

```
feat:

fix:

docs:

refactor:

style:

test:

perf:

chore:
```

---

# 실제 협업 예시

```
팀장
│
├── Repository 생성
│
├── Collaborator 초대
│
└── README 작성

↓

팀원A

feature/tool

↓

Push

↓

PR

↓

Merge

↓

팀원B

git pull

↓

feature/rag

↓

Push

↓

PR

↓

Merge

↓

최종 발표
```

---

## 부록. Git 명령어 치트시트

| 작업          | 명령어                             |
| ----------- | ------------------------------- |
| 저장소 복제      | `git clone <URL>`               |
| 현재 상태 확인    | `git status`                    |
| 변경 내용 확인    | `git diff`                      |
| 파일 스테이징     | `git add <파일명>`                 |
| 전체 스테이징     | `git add .`                     |
| 커밋          | `git commit -m "메시지"`           |
| 원격 저장소 업로드  | `git push`                      |
| 최신 코드 가져오기  | `git pull origin main`          |
| 브랜치 생성 및 이동 | `git switch -c feature/기능명`     |
| 브랜치 이동      | `git switch 브랜치명`               |
| 브랜치 목록      | `git branch`                    |
| 원격 브랜치 목록   | `git branch -r`                 |
| 브랜치 병합      | `git merge main`                |
| 커밋 기록 확인    | `git log --oneline`             |
| 로컬 브랜치 삭제   | `git branch -d 브랜치명`            |
| 원격 브랜치 삭제   | `git push origin --delete 브랜치명` |

