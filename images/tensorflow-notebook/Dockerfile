# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
ARG REGISTRY=quay.io
ARG OWNER=jupyter
ARG BASE_IMAGE=$REGISTRY/$OWNER/scipy-notebook
FROM $BASE_IMAGE

LABEL maintainer="Jupyter Project <jupyter@googlegroups.com>"

# Fix: https://github.com/hadolint/hadolint/wiki/DL4006
# Fix: https://github.com/koalaman/shellcheck/wiki/SC3014
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Stable TensorFlow does not publish Python 3.14 wheels yet, so use nightly by default.
# Override these args once stable TensorFlow catches up.
ARG TENSORFLOW_PACKAGE=tf-nightly
ARG TENSORFLOW_CPU_PACKAGE=tf-nightly-cpu
RUN mamba install --yes \
    'jupyter-server-proxy' && \
    mamba clean --all -f -y && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

# Install tensorflow with pip, on x86_64 use the CPU-only wheel.
RUN [[ $(uname -m) = x86_64 ]] && TF_PACKAGE="${TENSORFLOW_CPU_PACKAGE}" || TF_PACKAGE="${TENSORFLOW_PACKAGE}" && \
    pip install -v --no-cache-dir --pre \
    "${TF_PACKAGE}" && \
    fix-permissions "${CONDA_DIR}" && \
    fix-permissions "/home/${NB_USER}"

COPY --chown="${NB_UID}:${NB_GID}" cuda/20tensorboard-proxy-env.sh /usr/local/bin/before-notebook.d/
