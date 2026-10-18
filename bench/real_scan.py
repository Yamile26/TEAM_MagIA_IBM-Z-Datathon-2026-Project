import subprocess, time, json, collections, pathlib, sys
sys.path.insert(0, "../scanner")
from scan import scan

repos = {"requests": "https://github.com/psf/requests",
         "paramiko": "https://github.com/paramiko/paramiko"}
base = pathlib.Path.home() / "real_repos"
base.mkdir(exist_ok=True)
for name, url in repos.items():
    dest = base / name
    if not dest.exists():
        subprocess.run(["git", "clone", "--depth", "1", "-q", url, str(dest)], check=True)
    files = [p for p in dest.rglob("*") if p.is_file() and p.suffix in {".py", ".conf", ".js", ".java"}]
    t = time.time()
    found = scan(str(dest))
    dt = time.time() - t
    c = collections.Counter(x["algorithm"] for x in found)
    print(f"{name}: {len(files)} files scanned in {dt:.2f} s, {len(found)} candidates {dict(c)}")
    json.dump(found, open(f"real_{name}.json", "w"))
