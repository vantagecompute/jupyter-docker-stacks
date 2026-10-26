# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
# mypy: disable-error-code="name-defined"
# pyright: reportUndefinedVariable=false
import os
import stat
import subprocess
from pathlib import Path

from jupyter_core.paths import jupyter_data_dir

c = get_config()  # noqa: F821
# Listen on all interfaces (ipv4 and ipv6)
c.ServerApp.ip = ""
c.ServerApp.open_browser = False

# to output both image/svg+xml and application/pdf plot formats in the notebook file
c.InlineBackend.figure_formats = {"png", "jpeg", "svg", "pdf"}

# https://github.com/jupyter/notebook/issues/3130
c.FileContentsManager.delete_to_trash = False

# Generate a self-signed certificate
OPENSSL_CONFIG = """\
[req]
distinguished_name = req_distinguished_name
[req_distinguished_name]
"""
if "GEN_CERT" in os.environ:
    dir_name = Path(jupyter_data_dir())
    dir_name.mkdir(parents=True, exist_ok=True)
    pem_file = dir_name / "notebook.pem"

    # Generate an openssl.cnf file to set the distinguished name
    cnf_file = Path(os.getenv("CONDA_DIR", "/usr/lib")) / "ssl/openssl.cnf"
    if not cnf_file.exists():
        cnf_file.write_text(OPENSSL_CONFIG)

    # Generate a certificate if one doesn't exist on a disk
    subprocess.check_call(
        [
            "openssl",
            "req",
            "-new",
            "-newkey=rsa:2048",
            "-days=365",
            "-nodes",
            "-x509",
            "-subj=/C=XX/ST=XX/L=XX/O=generated/CN=generated",
            f"-keyout={pem_file}",
            f"-out={pem_file}",
        ]
    )
    # Restrict access to the file
    pem_file.chmod(stat.S_IRUSR | stat.S_IWUSR)
    c.ServerApp.certfile = str(pem_file)

# Change default umask for all subprocesses of the Server if set in the environment
if "NB_UMASK" in os.environ:
    os.umask(int(os.environ["NB_UMASK"], 8))

# Kubeflow Notebooks / Workspaces: the controller sets NB_PREFIX to the URL path
# the workspace is proxied under and expects the image to meet the contract in
# https://www.kubeflow.org/docs/components/notebooks/container-images/ :
# serve under that path, send `Access-Control-Allow-Origin: *` (the dashboard
# embeds the workspace in an iframe) and answer `<prefix>/api/status` without a
# token (the Workspaces controller polls it for `last_activity` to cull idle
# workspaces). Authentication is done in front of the pod by the Kubeflow
# gateway, so Jupyter's own token is turned off. Nothing here applies when
# NB_PREFIX is unset, so a plain `docker run` keeps token auth.
if nb_prefix := os.environ.get("NB_PREFIX"):
    # Jupyter joins base_url and routes ("lab", "api") directly, so it must end
    # in exactly one "/"; Kubeflow sends the prefix without one.
    c.ServerApp.base_url = nb_prefix.rstrip("/") + "/"
    c.IdentityProvider.token = ""
    c.ServerApp.allow_origin = "*"
    c.ServerApp.allow_remote_access = True
    c.ServerApp.authenticate_prometheus = False
    # Open in the user's home, which is the workspace volume. The
    # before-notebook.d/20kubeflow-home.sh hook moves HOME under /tmp when the
    # container runs as a uid that cannot write it; keep the default then.
    home = os.environ.get("HOME", "")
    if home and not home.startswith("/tmp/"):
        c.ServerApp.root_dir = home
