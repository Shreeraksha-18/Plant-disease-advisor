import statistics
import time
import uuid

import requests

import sys
BASE = sys.argv[1].rstrip("/")
IMAGE = "test_leaf.jpg"
N = 30


def pct(values, p):
    v = sorted(values)
    return v[min(len(v) - 1, round(p / 100 * (len(v) - 1)))]


def summary(name, ms, errors):
    print(f"{name:10} n={len(ms):3}  mean={statistics.mean(ms):7.1f}  median={statistics.median(ms):7.1f}  "
          f"p95={pct(ms, 95):7.1f}  min={min(ms):7.1f}  max={max(ms):7.1f}  errors={errors}")


s = requests.Session()
user = "lat_" + uuid.uuid4().hex[:8]
pw = "test12345"
assert s.post(f"{BASE}/auth/register", json={"username": user, "password": pw}).status_code == 201
token = s.post(f"{BASE}/auth/login", data={"username": user, "password": pw}).json()["access_token"]
H = {"Authorization": "Bearer " + token}
data = open(IMAGE, "rb").read()

# warm-up (not counted)
s.get(f"{BASE}/health")
s.post(f"{BASE}/predict", headers=H, files={"file": ("leaf.jpg", data, "image/jpeg")})

health, predict, errs_h, errs_p, ids = [], [], 0, 0, []
for _ in range(N):
    t = time.perf_counter()
    r = s.get(f"{BASE}/health")
    health.append((time.perf_counter() - t) * 1000)
    errs_h += r.status_code != 200

for _ in range(N):
    t = time.perf_counter()
    r = s.post(f"{BASE}/predict", headers=H, files={"file": ("leaf.jpg", data, "image/jpeg")})
    predict.append((time.perf_counter() - t) * 1000)
    if r.status_code == 200:
        ids.append(r.json()["record_id"])
    else:
        errs_p += 1

print("\nLatency in milliseconds, measured from this laptop through CloudFront:")
summary("/health", health, errs_h)
summary("/predict", predict, errs_p)

for i in ids:                      # clean up the test records (and their S3 photos)
    s.delete(f"{BASE}/predictions/{i}", headers=H)
print(f"\nDeleted {len(ids)} test records.")