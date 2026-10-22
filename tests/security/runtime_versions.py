"""GitHub-only inventory/assertions for the candidate or exact published image.

No connections, database mutations or host files are involved. Native-library
versions are reported separately because pip-audit does not audit their CVEs.
"""

import ctypes
import importlib.metadata
import json
import ssl
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
native_crypto = sorted(native_directory.glob("libcrypto*.so*"))
if not native_crypto:
    raise RuntimeError("Cannot inspect the wheel's bundled OpenSSL library")
native_library = ctypes.CDLL(str(native_crypto[0]))
native_library.OpenSSL_version.argtypes = [ctypes.c_int]
native_library.OpenSSL_version.restype = ctypes.c_char_p
report["driver_bundled_openssl"] = native_library.OpenSSL_version(0).decode("ascii")
print(json.dumps(report, indent=2), flush=True)

assert sys.version_info[:2] == (3, 13), "Unreviewed Python minor version"
assert sys.version_info[:3] >= (3, 13, 17), "Python security release is missing"
assert Version(report["driver"]) >= Version("2.9.13"), "Database driver update is missing"
assert report["driver_libpq"] >= 170011, "Driver libpq security refresh is missing"
assert Version(report["pip"]) >= Version("26.2.2"), "pip certificate-trust update is missing"
assert Version(report["pip_vendored_certifi"]) >= Version("2026.10.19"), "Old pip CA bundle"
assert Version(report["requests_certifi"]) >= Version("2026.10.19"), "Old requests CA bundle"
print("PASS: reviewed runtime and certificate-trust versions are installed.")
