# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.
"""Kubeflow Notebooks / Workspaces container-image contract.

https://www.kubeflow.org/docs/components/notebooks/container-images/ requires
an image to serve HTTP on 8888 under NB_PREFIX, send
`Access-Control-Allow-Origin: *`, and start as jovyan (uid 1000) with an empty
volume mounted at /home/jovyan. The Workspaces controller also polls
`<prefix>/api/status` without a token for `last_activity`. The pod runs with
every capability dropped and no privilege escalation, under fsGroup 100.

These tests live under base-notebook, so every image built on it runs them.
"""

import logging

import pytest  # type: ignore
import requests

from tests.utils.tracked_container import TrackedContainer

LOGGER = logging.getLogger(__name__)

NB_PREFIX = "/workspace/kubeflow-user/my-workspace/jupyterlab"
ORIGIN = "https://kubeflow.example.com"


@pytest.mark.parametrize(
    "user",
    [
        # jovyan, as the Kubeflow contract specifies.
        None,
        # Another uid in group users (fsGroup 100): home is group-writable.
        "4242:100",
        # Another uid outside group users: home is not writable, so the
        # before-notebook hook falls back to a home under /tmp.
        "4242:4242",
    ],
)
def test_kubeflow_contract(
    container: TrackedContainer,
    http_client: requests.Session,
    free_host_port: int,
    user: str | None,
) -> None:
    """Image should meet the Kubeflow Notebooks container-image contract."""
    container.run_detached(
        environment=[f"NB_PREFIX={NB_PREFIX}"],
        ports={"8888/tcp": free_host_port},
        # An empty home volume, owned the way fsGroup 100 leaves it.
        tmpfs={"/home/jovyan": "mode=2775,uid=1000,gid=100"},
        cap_drop=["ALL"],
        security_opt=["no-new-privileges"],
        **({"user": user} if user else {}),
    )
    base = f"http://localhost:{free_host_port}{NB_PREFIX}"

    status = http_client.get(f"{base}/api/status")
    status.raise_for_status()
    assert "last_activity" in status.json()

    lab = http_client.get(f"{base}/lab", headers={"Origin": ORIGIN})
    lab.raise_for_status()
    assert "login_submit" not in lab.text

    api = http_client.get(f"{base}/api", headers={"Origin": ORIGIN})
    api.raise_for_status()
    assert api.headers.get("Access-Control-Allow-Origin") in ("*", ORIGIN)

    logs = container.get_logs()
    LOGGER.debug(logs)
    assert "ERROR" not in logs


def test_token_auth_without_nb_prefix(
    container: TrackedContainer, http_client: requests.Session, free_host_port: int
) -> None:
    """Outside Kubeflow (no NB_PREFIX) the server should still require a token."""
    container.run_detached(ports={"8888/tcp": free_host_port})
    resp = http_client.get(f"http://localhost:{free_host_port}/api/status")
    assert resp.status_code == 403, resp.status_code
