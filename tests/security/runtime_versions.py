"""GitHub-only inventory/assertions for the candidate or exact published image.

No connections, database mutations or host files are involved. Native-library
versions are reported separately because pip-audit does not audit their CVEs.
"""

import importlib.metadata
import json
import shutil
import ssl
import subprocess
import sys
from pathlib import Path

import psycopg2
from packaging.version import Version

report = {
    "python": sys.version.split()[0],
    "system_openssl": ssl.OPENSSL_VERSION,
    "driver": importlib.metadata.version("psycopg2-binary"),
    "driver_libpq": psycopg2.__libpq_version__,
    "pip": importlib.metadata.version("pip"),
    "requests_certifi": importlib.metadata.version("certifi"),
}

from pip._vendor import certifi as pip_certifi  # noqa: E402

report["pip_vendored_certifi"] = pip_certifi.__version__
native_directory = Path(psycopg2.__file__).resolve().parent.parent / "psycopg2_binary.libs"
mapped_libraries = sorted(
    {
        line.split()[-1]
        for line in Path("/proc/self/maps").read_text().splitlines()
        if any(name in line for name in ("/libpq", "/libssl", "/libcrypto"))
    }
)
report["driver_native_library_mode"] = "system"
report["mapped_native_libraries"] = mapped_libraries
report["distribution_native_packages"] = subprocess.check_output(
    ["dpkg-query", "-W", "-f=${Package}=${Version}\n", "libpq5", "libssl3"], text=True
).splitlines()
report["compiler"] = shutil.which("gcc")
print(json.dumps(report, indent=2), flush=True)

assert sys.version_info[:2] == (3, 13), "Unreviewed Python minor version"
assert sys.version_info[:3] >= (3, 13, 17), "Python security release is missing"
assert Version(report["driver"]) >= Version("2.9.13"), "Database driver update is missing"
assert 150019 <= report["driver_libpq"] < 160000, "Unreviewed/old Debian libpq version"
assert not native_directory.exists(), "Private driver native libraries remain installed"
assert any("/libpq.so" in path for path in mapped_libraries), "System libpq not loaded"
assert all(".libs/" not in path for path in mapped_libraries), "Private crypto library loaded"
assert report["compiler"] is None, "Build compiler was left in the runtime image"
assert Version(report["pip"]) >= Version("26.2.2"), "pip certificate-trust update is missing"
assert Version(report["pip_vendored_certifi"]) >= Version("2026.10.19"), "Old pip CA bundle"
assert Version(report["requests_certifi"]) >= Version("2026.10.19"), "Old requests CA bundle"
print("PASS: reviewed runtime and certificate-trust versions are installed.")
