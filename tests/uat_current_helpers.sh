#!/bin/bash
set -euo pipefail

BASE_URL="${BASE_URL:-http://127.0.0.1:5001/api}"

RESULTS_DIR="${RESULTS_DIR:-tests/test-results}"
RUN_ID="${RUN_ID:-$(date +%Y%m%d_%H%M%S)}"
LOG_FILE="$RESULTS_DIR/uat_current_$RUN_ID.log"

mkdir -p "$RESULTS_DIR"

preflight_backend() {
  local root_url="$BASE_URL"
  if [[ "$root_url" == */api ]]; then
    root_url="${root_url%/api}"
  fi

  local health_url="$root_url/health"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$health_url" 2>/dev/null || echo "000")

  if [ "$code" != "200" ]; then
    echo "ERROR: Backend not reachable at $BASE_URL" | tee -a "$LOG_FILE" >&2
    echo "- Expected health endpoint: $health_url" | tee -a "$LOG_FILE" >&2
    echo "- Got HTTP: $code" | tee -a "$LOG_FILE" >&2
    echo "- Start backend (example): source backend/venv/bin/activate && python backend/app.py" | tee -a "$LOG_FILE" >&2
    echo "- Or override BASE_URL, e.g.: BASE_URL=http://127.0.0.1:5001/api bash tests/uat_current_tests.sh" | tee -a "$LOG_FILE" >&2
    exit 2
  fi
}

TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0
WARNED_TESTS=0

require_cmd() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd python3

pass_test() {
  local test_id="$1"
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  PASSED_TESTS=$((PASSED_TESTS + 1))
  echo "PASS: $test_id" | tee -a "$LOG_FILE"
}

fail_test() {
  local test_id="$1"
  local reason="$2"
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  FAILED_TESTS=$((FAILED_TESTS + 1))
  echo "FAIL: $test_id - $reason" | tee -a "$LOG_FILE"
}

warn_test() {
  local test_id="$1"
  local reason="$2"
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  WARNED_TESTS=$((WARNED_TESTS + 1))
  echo "WARN: $test_id - $reason" | tee -a "$LOG_FILE"
}

print_section() {
  local title="$1"
  echo "" | tee -a "$LOG_FILE"
  echo "=== $title ===" | tee -a "$LOG_FILE"
}

api_call() {
  local method="$1"
  local endpoint="$2"
  local data="$3"
  local token="$4"

  local temp_file
  temp_file=$(mktemp)

  if [ -n "$token" ]; then
    if [ "$method" = "GET" ] || [ "$method" = "DELETE" ]; then
      curl -s -w "\n%{http_code}" -X "$method" \
        "$BASE_URL$endpoint" \
        -H "Authorization: Bearer $token" >"$temp_file" 2>/dev/null
    else
      curl -s -w "\n%{http_code}" -X "$method" \
        "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $token" \
        -d "$data" >"$temp_file" 2>/dev/null
    fi
  else
    if [ "$method" = "GET" ] || [ "$method" = "DELETE" ]; then
      curl -s -w "\n%{http_code}" -X "$method" \
        "$BASE_URL$endpoint" >"$temp_file" 2>/dev/null
    else
      curl -s -w "\n%{http_code}" -X "$method" \
        "$BASE_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data" >"$temp_file" 2>/dev/null
    fi
  fi

  local http_code
  local body
  http_code=$(tail -n 1 "$temp_file")
  body=$(sed '$d' "$temp_file")
  rm -f "$temp_file"

  echo "$body"
  echo "$http_code"
}

get_http_code() {
  echo "$1" | tail -n 1
}

get_body() {
  echo "$1" | sed '$d'
}

json_get() {
  local json="$1"
  local selector="$2"

  python3 -c "import json, re, sys
selector = sys.argv[1]
try:
    data = json.load(sys.stdin)
except Exception:
    print('')
    raise SystemExit(0)

cur = data
for part in selector.split('.'):
    if not part:
        continue
    m = re.match(r'^(?P<key>[A-Za-z0-9_]+)(\\[(?P<idx>\\d+)\\])?$', part)
    if not m:
        cur = None
        break
    key = m.group('key')
    idx = m.group('idx')
    if isinstance(cur, dict):
        cur = cur.get(key)
    else:
        cur = None
        break
    if idx is not None:
        if isinstance(cur, list):
            i = int(idx)
            cur = cur[i] if 0 <= i < len(cur) else None
        else:
            cur = None
            break

if cur is None:
    print('')
elif isinstance(cur, (dict, list)):
    print(json.dumps(cur))
else:
    print(cur)
" "$selector" <<<"$json" 2>/dev/null
}

print_summary() {
  echo "" | tee -a "$LOG_FILE"
  echo "=== SUMMARY ===" | tee -a "$LOG_FILE"
  echo "Total:  $TOTAL_TESTS" | tee -a "$LOG_FILE"
  echo "Passed: $PASSED_TESTS" | tee -a "$LOG_FILE"
  echo "Failed: $FAILED_TESTS" | tee -a "$LOG_FILE"
  echo "Warned: $WARNED_TESTS" | tee -a "$LOG_FILE"
  echo "Log:    $LOG_FILE" | tee -a "$LOG_FILE"

  if [ "$FAILED_TESTS" -eq 0 ]; then
    return 0
  fi
  return 1
}

export -f pass_test fail_test warn_test print_section
export -f api_call get_http_code get_body json_get print_summary preflight_backend
export BASE_URL RESULTS_DIR RUN_ID LOG_FILE
