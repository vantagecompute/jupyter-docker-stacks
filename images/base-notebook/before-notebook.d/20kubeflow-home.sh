#!/bin/bash
# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

# Kubeflow Notebooks / Workspaces may run the container as a uid other than
# jovyan's (e.g. one resolved from LDAP by an admission webhook) with a home
# directory that uid cannot write. Jupyter then fails creating its runtime and
# config files, so fall back to a private home under /tmp. Only runs when
# NB_PREFIX is set, so plain `docker run` keeps the upstream behaviour.
if [[ -n "${NB_PREFIX:-}" && ! -w "${HOME:-/nonexistent}" ]]; then
    _kubeflow_home="/tmp/home-$(id -u)"
    _log_info "HOME ${HOME:-unset} is not writable by uid $(id -u), using ${_kubeflow_home}"
    mkdir -p "${_kubeflow_home}" && chmod 700 "${_kubeflow_home}"
    export HOME="${_kubeflow_home}"
    export XDG_RUNTIME_DIR="${HOME}/.runtime"
    mkdir -p "${XDG_RUNTIME_DIR}" && chmod 700 "${XDG_RUNTIME_DIR}"
    unset _kubeflow_home
fi
