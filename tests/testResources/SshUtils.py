import subprocess

from tests.testResources.VirtMngmt import VirtMngmt


class SshUtils(object):
    user = "tuser"

    @classmethod
    def doSsh(cls, command: str):
        return subprocess.run(
            ["ssh", cls.user + "@" + VirtMngmt.getTestVmIp(), command],
            capture_output=True,
            check=False
        )

    @classmethod
    def assertSsh(cls, worked: bool):
        result = cls.doSsh("echo worked")

        if worked:
            assert result.returncode == 0
            assert str(result.stdout).find("worked") != -1
        else:
            assert result.returncode != 0
            assert str(result.stdout).find("worked") == -1

    @classmethod
    def setTestServerSshPolicy(cls, policy: str):
        VirtMngmt.runCmdOnTestVm(["update-crypto-policies", "--set", policy])
        VirtMngmt.runCmdOnTestVm(["systemctl", "restart", "sshd.service"])
