import logging
import subprocess

import pytest

from tests.testResources.SshUtils import SshUtils
from tests.testResources.VirtMngmt import VirtMngmt


class TestSSHPolicies(object):

    def setPolicy(self, policy:str):
        return

    def test_unchanged_ssh(self):
        SshUtils.assertSsh(True)

    def test_default_policy_allowed(self):
        SshUtils.setTestServerSshPolicy("DEFAULT")
        SshUtils.assertSsh(True)

    def test_legacy_policy_allowed(self):
        SshUtils.setTestServerSshPolicy("LEGACY")
        SshUtils.assertSsh(True)