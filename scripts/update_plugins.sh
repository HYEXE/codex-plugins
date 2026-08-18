#!/usr/bin/env bash
set -euo pipefail

marketplace="${CODEX_WORKFLOWS_MARKETPLACE:-codex-workflows-kr}"
codex_bin="${CODEX_BIN:-codex}"
dry_run=false
plugins=("prompt-compiler" "uiux-advisor")

usage() {
  cat <<'EOF'
Codex Plugins의 Git marketplace snapshot을 갱신하고 플러그인을 다시 설치합니다.

사용법:
  update_plugins.sh [--dry-run] [--marketplace NAME] [--codex-bin PATH]

옵션:
  --dry-run           실행할 명령만 출력합니다.
  --marketplace NAME  marketplace 이름을 지정합니다.
  --codex-bin PATH    codex 실행 파일 또는 명령을 지정합니다.
  -h, --help          도움말을 표시합니다.

환경 변수:
  CODEX_WORKFLOWS_MARKETPLACE
  CODEX_BIN
EOF
}

while (($# > 0)); do
  case "$1" in
    --dry-run)
      dry_run=true
      shift
      ;;
    --marketplace)
      if (($# < 2)); then
        printf '오류: --marketplace에는 값이 필요합니다.\n' >&2
        exit 2
      fi
      marketplace="$2"
      shift 2
      ;;
    --codex-bin)
      if (($# < 2)); then
        printf '오류: --codex-bin에는 값이 필요합니다.\n' >&2
        exit 2
      fi
      codex_bin="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      printf '오류: 알 수 없는 옵션: %s\n' "$1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ -z "$marketplace" || -z "$codex_bin" ]]; then
  printf '오류: marketplace와 codex 실행 경로는 비어 있을 수 없습니다.\n' >&2
  exit 2
fi

if [[ "$dry_run" == false ]] && ! command -v "$codex_bin" >/dev/null 2>&1; then
  printf '오류: Codex CLI를 찾을 수 없습니다: %s\n' "$codex_bin" >&2
  printf 'CODEX_BIN 또는 --codex-bin으로 실행 경로를 지정하세요.\n' >&2
  exit 1
fi

run_codex() {
  local args=("$@")
  printf '+ %q' "$codex_bin"
  printf ' %q' "${args[@]}"
  printf '\n'
  if [[ "$dry_run" == false ]]; then
    "$codex_bin" "${args[@]}"
  fi
}

run_codex plugin marketplace upgrade "$marketplace"
for plugin in "${plugins[@]}"; do
  run_codex plugin add "${plugin}@${marketplace}"
done

if [[ "$dry_run" == true ]]; then
  printf 'Dry run 완료: 실제 marketplace와 플러그인은 변경되지 않았습니다.\n'
else
  printf '업데이트 완료: Codex를 재시작하거나 새 작업을 열어 변경 사항을 불러오세요.\n'
fi
