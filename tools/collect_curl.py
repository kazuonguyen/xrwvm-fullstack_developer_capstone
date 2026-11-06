"""Collect actual cURL output from the running application, without inventing results."""
from pathlib import Path
import json
import os
import shlex
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence'
BASE = os.environ.get('EVIDENCE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
USER = os.environ.get('DEMO_USER_PASSWORD')
if not USER:
    raise SystemExit('Set DEMO_USER_PASSWORD to the actual demo account password.')
OUT.mkdir(exist_ok=True)


def curl(args):
    cmd = ['curl', '--fail-with-body', '-sS', *args]
    result = subprocess.run(cmd, text=True, capture_output=True, check=True)
    return cmd, result.stdout


def save(name, cmd, output):
    text = '$ ' + shlex.join(cmd) + '\n' + output.rstrip() + '\n'
    (OUT / (name + '.txt')).write_text(text)
    print(name + ': captured successfully')


with tempfile.TemporaryDirectory() as tmp:
    cookies = str(Path(tmp) / 'demo.cookies')
    _, session = curl(['-c', cookies, BASE + '/djangoapp/session'])
    token = json.loads(session)['csrfToken']
    cmd, result = curl(['-b', cookies, '-c', cookies, '-H', 'Content-Type: application/json',
        '-H', 'X-CSRFToken: ' + token, '-d', json.dumps({'userName': 'demo_user', 'password': USER}), BASE + '/djangoapp/login'])
    authenticated = json.loads(result)
    assert authenticated['status'] == 200
    # CSRF values are ephemeral tokens, not evidence of the application behavior.
    save('loginuser', cmd, result)
    cmd, result = curl(['-b', cookies, '-H', 'X-CSRFToken: ' + authenticated['csrfToken'], '-X', 'POST', BASE + '/djangoapp/logout'])
    assert json.loads(result)['status'] == 200
    save('logoutuser', cmd, result)
for name, endpoint in [
    ('getdealerreviews', '/djangoapp/reviews/dealer/15'),
    ('getalldealers', '/djangoapp/get_dealers'),
    ('getdealerbyid', '/djangoapp/dealer/8'),
    ('getdealersbyState', '/djangoapp/get_dealers/Kansas'),
    ('getallcarmakes', '/djangoapp/get_cars'),
    ('analyzereview', '/djangoapp/analyze/Fantastic%20services'),
]:
    cmd, result = curl([BASE + endpoint])
    json.loads(result)
    save(name, cmd, result)
