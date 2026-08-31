import subprocess

from tests.testResources.VirtMngmt import VirtMngmt


class SshUtils(object):
    user = "tuser"

    @classmethod
    def doSsh(cls, command: str, args:list[str] = []):
        return subprocess.run(
            ["ssh", *args, cls.user + "@" + VirtMngmt.getTestVmIp(), command],
            capture_output=True,
            check=False
        )

    @classmethod
    def assertSsh(cls, worked: bool, sshArgs: list[str] = []):
        result = cls.doSsh("echo worked", args=sshArgs)

        print("SSH result stdout:", result.stdout)
        print("SSH result stderr:", result.stderr)

        if worked:
            assert result.returncode == 0
            assert str(result.stdout).find("worked") != -1
        else:
            assert result.returncode != 0
            assert str(result.stdout).find("worked") == -1

    @classmethod
    def setTestServerCryptoPolicy(cls, policy: str):
        print("Setting testServerCryptoPolicy to " + policy)
        VirtMngmt.runCmdOnTestVm(["update-crypto-policies", "--set", policy])
        VirtMngmt.runCmdOnTestVm(["systemctl", "restart", "sshd.service"])
        VirtMngmt.runCmdOnTestVm(["update-crypto-policies", "--show"])
