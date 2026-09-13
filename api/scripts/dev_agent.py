import subprocess
import sys


def run(name: str, command: list[str]) -> bool:
    print(f"== {name} ==")
    result = subprocess.run(command)
    return result.returncode == 0


def main() -> int:
    checks = [
        ("lint", [sys.executable, "-m", "ruff", "check", "app", "tests"]),
        ("tests", [sys.executable, "-m", "pytest", "-q"]),
    ]

    failures = [name for name, command in checks if not run(name, command)]

    if failures:
        print(f"failed: {', '.join(failures)}")
        return 1

    print("all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
