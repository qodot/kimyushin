# 김유신의 주식 종목 고르기

## 설치

먼저 python 3.11을 [이곳](https://www.python.org/downloads/)에서 설치한 후 poetry를 [이곳](https://python-poetry.org/docs/#installation)에서 설치한다.

다음 명령어를 입력해서 사용하는 라이브러리 등의 의존 패키지를 설치한다.

```sh
poetry install
```

다음 명령어로 스크립트를 실행한다.

```sh
poetry run python main.py 20230808 # 원하는 날짜 입력
```

실행 결과는 `results` 폴더에 csv 파일로 저장되어 있다.
