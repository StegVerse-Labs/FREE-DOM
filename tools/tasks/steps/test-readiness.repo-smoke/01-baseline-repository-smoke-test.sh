python - <<'PY'
from pathlib import Path
import json
import sys

root = Path('.')
failures = []

if not any((root / name).exists() for name in ('README.md', 'README.MD')):
    failures.append('missing README.md')

workflows = root / '.github' / 'workflows'
if workflows.exists():
    bad = sorted(p.name for p in workflows.glob('*.ym'))
    if bad:
        failures.append('workflow files must end in .yml or .yaml: ' + ', '.join(bad))

for path in sorted(root.rglob('*.json')):
    if any(part in {'.git', 'node_modules', '.venv', 'venv'} for part in path.parts):
        continue
    try:
        json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        failures.append(f'invalid JSON: {path}: {exc}')

tests = root / 'tests'
if tests.exists():
    print(f'tests directory detected: {tests}')
else:
    print('no tests directory detected; baseline smoke gate only')

if failures:
    print('TEST READINESS FAILED')
    for failure in failures:
        print(f'- {failure}')
    sys.exit(1)

print('TEST READINESS PASSED')
PY
