#!/bin/sh
# Use the PSF-recommended hash-pinned wheel before downloading CI dependencies.
# This updates only the disposable GitHub job's selected Python environment.
set -eu
python -m pip install 'pip @ https://files.pythonhosted.org/packages/3f/06/3e4420302363fbb71be3c7f35ce042f54bfca330e3e66b3a2e3c4cca579f/pip-26.2.2-py3-none-any.whl#sha256=fd7f4dfa8190e014013b9f08f3e973f4e4c26ffd179a204895533a7254813a70'
python -c 'import pip; from pip._vendor import certifi; assert pip.__version__ == "26.2.2"; assert certifi.__version__ == "2026.10.19"; print("CI pip/certificate bundle:", pip.__version__, certifi.__version__)'
