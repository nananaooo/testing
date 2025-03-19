import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

# 설정 값
PROJECT_PATH = "/Users/gimminjae/Documents/testing"  # 프로젝트 경로
MODULE_NAME = "main"  # 테스트할 모듈명
TEST_OUTPUT_PATH = "/Users/gimminjae/Documents/testing/test_output"  # 테스트 케이스 출력 경로

# `pytest`의 절대 경로를 지정하는 방법
PYTEST_PATH = "/opt/anaconda3/envs/tf_env_310/bin/pytest"  # `pytest` 경로

class CodeChangeHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_run_time = 0  # 마지막 실행 시간을 저장하는 변수
        self.debounce_time = 1  # 저장 후 1초 대기
        self.test_running = False  # 테스트가 실행 중인지 확인

    def on_modified(self, event):
        current_time = time.time()  # 현재 시간

        # `test_output` 폴더 내 변경은 무시하고, main.py 파일만 수정된 경우 반응
        if TEST_OUTPUT_PATH in event.src_path:
            return
        if not event.src_path.endswith("main.py"):
            return

        # 파일이 수정된 직후, 테스트 실행 중이면 무시
        if event.src_path.endswith("main.py") and not self.test_running and current_time - self.last_run_time > self.debounce_time:
            print(f"\n🔄 파일 변경 감지: {event.src_path}")
            print("🚀 Pynguin으로 테스트 케이스 생성 중...")

            # `PYNGUIN_DANGER_AWARE` 환경 변수 설정
            os.environ['PYNGUIN_DANGER_AWARE'] = '1'  # 환경 변수 설정

            # Pynguin을 사용하여 테스트 케이스 생성
            subprocess.run(
                [
                    "pynguin", "--project-path", PROJECT_PATH, "--module-name", MODULE_NAME,
                    "--output-path", TEST_OUTPUT_PATH
                ]
            )

            print("✅ 테스트 케이스 생성 완료!")

            print("🚀 pytest 실행 중...")
            # `pytest`를 사용하여 테스트 실행 (경로를 명시적으로 지정)
            subprocess.run(
                [
                    PYTEST_PATH, TEST_OUTPUT_PATH  # `pytest` 경로를 명시적으로 지정
                ], env={"PYTHONPATH": PROJECT_PATH}  # 환경변수 설정
            )
            print("✅ 테스트 실행 완료!")

            # 마지막 실행 시간을 갱신하고, 테스트가 실행 중임을 설정
            self.last_run_time = current_time
            self.test_running = True  # 테스트 실행 중 상태로 설정

            # 테스트 완료 후 1초 대기 후 다시 실행할 수 있도록 설정
            time.sleep(1)
            self.test_running = False


if __name__ == "__main__":
    event_handler = CodeChangeHandler()
    observer = Observer()
    observer.schedule(event_handler, PROJECT_PATH, recursive=True)  # 전체 프로젝트 경로 감시

    print("👀 파일 변경 감지 중...")
    observer.start()

    try:
        while True:
            time.sleep(1)  # 1초마다 감시
    except KeyboardInterrupt:
        observer.stop()  # 강제 종료
    observer.join()
