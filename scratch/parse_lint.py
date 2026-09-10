import subprocess
import json

res = subprocess.run(['npm.cmd', 'run', 'lint', '--', '--format', 'json'], cwd='frontend', capture_output=True, text=True, encoding='utf-8', errors='ignore')
try:
    json_start = res.stdout.index('[')
    data = json.loads(res.stdout[json_start:])
    for item in data:
        err_c = item['errorCount']
        warn_c = item['warningCount']
        if err_c > 0 or warn_c > 0:
            short_path = item['filePath'].replace('\\', '/').split('/frontend/')[-1]
            print(f"{short_path} (Errors: {err_c}, Warnings: {warn_c}):")
            for m in item['messages']:
                print(f"  Line {m.get('line')}: [{m.get('ruleId')}] {m.get('message')}")
except Exception as e:
    print("Error parsing json:", e)
    print("Raw stdout:", res.stdout[:500])
    print("Raw stderr:", res.stderr[:500])
