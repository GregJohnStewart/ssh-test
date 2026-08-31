import base64
import json
import logging
import random
import string
import time

import libvirt
import libvirt_qemu

class VirtMngmt(object):
    libvirt_uri="qemu:///system"
    domainName = "ssh-test"
    snapshotName = "test_snapshot-"+ ''.join(random.choices(string.ascii_letters, k=5))

    logger = logging.getLogger("VirtMngmt")
    connection = None
    domain = None
    snapshot = None

    @classmethod
    def setUp(cls):
        cls.logger.info("Setting up Virt connection.")
        cls.connection = libvirt.open(cls.libvirt_uri)
        if not cls.connection:
            raise SystemExit("Failed to open connection to qemu.")
        print("Virt host info: " + str(cls.connection.getHostname()))
        print("Virt connection info: " + str(cls.connection.getInfo()))

        cls.domain = cls.connection.lookupByName(cls.domainName)
        if not cls.domain:
            raise SystemExit("Failed to open domain with name: " + cls.domainName)
        print("Domain info: \n\tName: " + cls.domain.name() + "\n\tID: " + str(cls.domain.ID())+ "\n\tUUID: " + cls.domain.UUIDString())

        if cls.testVmIsRunning():
            cls.stopTestVm()

        try:
            cls.domain.snapshotLookupByName(cls.snapshotName)
        except libvirt.libvirtError as e:
            if e.get_error_message().find("Domain snapshot not found") != -1:
                print("Creating snapshot...")
                cls.domain.snapshotCreateXML(
                    f"""
                    <domainsnapshot>
                        <name>{cls.snapshotName}</name>
                        <description>Snapshot taken at the beginning of a test run to go back to.</description>
                    </domainsnapshot>
                    """,
                    libvirt.VIR_DOMAIN_SNAPSHOT_CREATE_VALIDATE
                )
            else:
                print("ERROR")
                raise e
        cls.snapshot = cls.domain.snapshotLookupByName(cls.snapshotName)

        cls.startTestVm()
        cls.runCmdOnTestVm(["/bin/whoami"])

    @classmethod
    def tearDown(cls):
        cls.logger.info("Tearing down Virt connection.")

        cls.stopTestVm()
        cls.domain.snapshotLookupByName(cls.snapshotName).delete()

    @classmethod
    def runCmdOnTestVm(cls, cmd_args: list[str], throwOnNonzero: bool = True) -> dict:
        print("Sending args: " + str(cmd_args[1:]))
        exec_payload = {
            "execute": "guest-exec",
            "arguments": {
                "path": cmd_args[0],
                "arg": cmd_args[1:],
                "capture-output": True
            }
        }

        response_str = libvirt_qemu.qemuAgentCommand(cls.domain, json.dumps(exec_payload), 60, 0)
        response = json.loads(response_str)
        pid = response['return']['pid']
        print(f"Command started with PID: {pid}")

        status_payload = {
            "execute": "guest-exec-status",
            "arguments": {"pid": pid}
        }
        output = {
            "exitCode": None,
            "stdout": None,
            "stderr": None
        }
        while True:
            status_str = libvirt_qemu.qemuAgentCommand(cls.domain, json.dumps(status_payload), 60, 0)
            status_res = json.loads(status_str)['return']

            if status_res['exited']:
                output["exitCode"] = status_res.get('exitcode', -1)
                print(f"Process exited with code: {output["exitCode"]}")

                if 'out-data' in status_res:
                    output["stdout"] = base64.b64decode(status_res['out-data']).decode('utf-8')
                    print(f"STDOUT:\n{output["stdout"]}")

                if 'err-data' in status_res:
                    output["stderr"] = base64.b64decode(status_res['err-data']).decode('utf-8')
                    print(f"STDERR:\n{output["stderr"]}")
                break

            time.sleep(0.5)

        if throwOnNonzero and output["exitCode"] != 0:
            raise SystemExit("Command exited with non-zero exit code.")

        return output


    @classmethod
    def testVmIsRunning(cls) -> bool:
        try:
            state, reason = cls.domain.state()
            print("State: " + str(state) + " / " + str(libvirt.VIR_DOMAIN_RUNNING))
            return state == libvirt.VIR_DOMAIN_RUNNING and cls.domain.isActive() and cls.runCmdOnTestVm(["/bin/bash", "-c", "echo started"])["exitCode"] == 0
        except libvirt.libvirtError as e:
            if e.get_error_message().find("Guest agent is not responding") != -1:
                return False
    @classmethod
    def testVmIsShutdown(cls) -> bool:
        if cls.domain.isActive():
            return False
        state, reason = cls.domain.state()
        return state == libvirt.VIR_DOMAIN_SHUTOFF


    @classmethod
    def startTestVm(cls):
        if cls.testVmIsRunning():
            return
        cls.domain.create()
        while not cls.testVmIsRunning():
            time.sleep(0.5)

    @classmethod
    def stopTestVm(cls):
        if cls.testVmIsShutdown():
            return
        cls.domain.shutdown()

        time.sleep(1)

        while not cls.testVmIsShutdown():
            time.sleep(0.5)
        print("Shut down VM.")

    @classmethod
    def resetTestVm(cls):
        cls.stopTestVm()

        result = cls.domain.revertToSnapshot(cls.snapshot, 0)

        if result == 0:
            print("Successfully reverted VM to snapshot.")
        else:
            raise SystemExit("Failed to revert VM to snapshot.")

        cls.startTestVm()

    @classmethod
    def getTestVmIp(cls)->str:
        if not cls.testVmIsRunning():
            raise SystemExit("VM is not running.")

        result = cls.runCmdOnTestVm(["ip", "route", "get", "1.1.1.1"])
        result = result["stdout"].split(" ")[6]

        return result

    @classmethod
    def setFileContents(cls, file:str, contents:str):
        if not cls.testVmIsRunning():
            raise SystemExit("VM is not running.")
        cls.runCmdOnTestVm(["touch", file])
        cls.runCmdOnTestVm(["/bin/bash", "-c", "echo " + contents, " > ", file])
