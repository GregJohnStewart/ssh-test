import logging
import subprocess

import pytest

from tests.testResources.SshUtils import SshUtils
from tests.testResources.VirtMngmt import VirtMngmt


class TestSSHPolicies(object):
    sha1Args = ["-o", "KexAlgorithms=diffie-hellman-group14-sha1", "-o", "HostKeyAlgorithms=ssh-rsa", "-o", "MACs=hmac-sha1"]

    def setPolicy(self, policy:str):
        return

    def test_unchanged_ssh(self):
        SshUtils.assertSsh(True)

    def test_default_policy_allowed(self):
        SshUtils.setTestServerCryptoPolicy("DEFAULT")
        SshUtils.assertSsh(True)

    def test_default_policy_not_allowed_sha1(self):
        SshUtils.setTestServerCryptoPolicy("DEFAULT")
        SshUtils.assertSsh(False, self.sha1Args)

    def test_legacy_policy_allowed(self):
        SshUtils.setTestServerCryptoPolicy("LEGACY")

        SshUtils.assertSsh(True)

    def test_legacy_policy_allowed_sha1(self):
        SshUtils.setTestServerCryptoPolicy("LEGACY")
        SshUtils.assertSsh(True, self.sha1Args)

