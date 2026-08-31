# ssh-test

This is a test suite to test the cryptographic policies of OpenSSH server.

## Test Plan

Overall, the test plan is as follows. The tests are written using the Pytest framework, leveraging KVM/Libvirt as
the underlying system to have host(s) to test against. These technologies give us a solid base framework to work
off of, as well as an incredibly flexible and repeatable testing flow.

The test flow will follow these general steps:

 0. **Initial setup** - Setup of the host, initial state of the guest VM to test against. Done just once.
 1. **Run Tests** - Run the test suite with standard `pytest` commands. Target guest VM is managed directly by the test suite,
    with snapshots being used to ensure consistent state between test cases
 2. **Reports** - The Pytest framework outputs a test report, giving a clear picture of how the tests went, and any potential failures.

Rationale and further information below.

### Goals

The key goals of this test suite are as follows:

 1. **Reliability / Repeatability** - The tests should be repeatable
 2. **Automated** - The tests should run in an automated fashion, not requiring any excess input or setup between tests (beyond initial setup). 
 3. **Readability of Outputs** - Outputs of the tests should be clear and easy to visualize, drill down into any issues.
 4. **Ease of maintenance** - The tests themselves should be easy to write and understand. Adding test cases should be trivial.

### Test Cases

With the given prompt, the following test cases are implemented:

 - "Unchanged" configuration, to ensure "base" case can work
 - `DEFAULT` policy with allowed crypto algorithm (should work)
 - `DEFAULT` policy with forbidden crypto algorithm (sha1) (should not work)
 - `LEGACY` policy with allowed crypto algorithm (should work)
 - `LEGACY` policy with crypto algorithm that was forbidden under `DEFAULT` (should work)

Test cases are implemented as SSH calls to the test service with specific ssh commands to give.

### Technologies

This test suite leverages a few key technologies to facilitate them:

#### Python / Pytest

Python was chosen as the language of choice for these tests as it is much more developed
in its design. Plain bash leaves much to be desired, in syntax, available libraries and
frameworks, and in error handling. Python by nature solves all three of these issues.

#### Lbvirt/KVM

Libvirt was chosen as the platform to facilitate the host being tested. The reason for this
being we have direct control of every aspect of the host during test execution. Given a
fairly clean initial host, we can take snapshots and execute commands directly on the host
directly from our test suite.

#### Other

It should be noted that this test setup and instructions is built against Fedora 44.
For testing, the host was Fedora 44 Workstation, while the guest (the VM hosting the
OpenSSH instance being tested) is a Fedora 44 server instance.

### Technologies _not_ Chosen

Listed here are technologies which were potential options, but ultimately not chosen.

 - **Bash** - Bash as the implementation language was not chosen due to several factors:
   - Syntax; the bash syntax is (comparatively) complex and harder to read at a glance. What is basic in Python can be a hassle in Bash
   - Error handling; Errors can often go unnoticed in Bash, and can cause false positives in setup and actual test cases.
   - Test Frameworks; While there seem to be some unit test frameworks available, the popularity surrounding other
     tools makes them more supported and featureful.
 - **Containers** - While leveraging containers would be leaner, it would be less representative of a full system.
   Containers only run a single process in isolation, and lacks the nuances of being run on a full host. Additionally,
   lacking Systemd is a large aspect of this. Overall, attempting to run OpennSSH serve rin a container is simply not
   representative of the 'normal' setup without heavy effort.

## Setup

### Libvirt / target VM

#### Initial Host Setup

On host, install the following:

```text
sudo dnf install @virtualization libvirt-devel python3-devel gcc
```

Then ensure your user has the permissions to manage and interact with the VM:

```bash
sudo usermod -a -G libvirt $USER
sudo usermod -a -G kvm $USER
```

#### Setup guest (target) VM

Start by creating a new VM, with the target OS (Fedora 44) installed.

(Theoretically, we could make the test suite do this, but for this POC, not a big deal)

Important notes (these values are set in global class members in tests):

 - Name the guest vm `ssh-test`
 - Use a non-root account named `tuser`

##### Setup Host-to-guest execution

Add following to VM's `devices` xml:

```xml
<channel type='unix'>
  <target type='virtio' name='org.qemu.guest_agent.0'/>
</channel>
```

Install the following on the guest:

```text
qemu-guest-agent && sudo systemctl enable --now qemu-guest-agent
```

After installing, run the following:

```bash
sudo semanage permissive -a virt_qemu_ga_t
```

Add the file `/etc/ssh/sshd_config.d/99-test.conf` with the following content:

```text
PubkeyAcceptedKeyTypes +ssh-rsa
KexAlgorithms +diffie-hellman-group1-sha1,diffie-hellman-group14-sha1
MACs +hmac-sha1
```

On host, enable passwordless ssh:

```bash
ssh-copy-id tuser@<ip of guest>
```

###### Usage / Verification

on host:

```bash
virsh qemu-agent-command <vm_name> '{"execute": "guest-exec", "arguments": {"path": "/bin/uname", "arg": ["-a"], "capture-output": true}}'
```

This should return:

```json
{"return":{"pid":1234}}
```

You can then get the result using:

```bash
virsh qemu-agent-command <vm_name> '{"execute": "guest-exec-status", "arguments": {"pid": 1234}}'
```

Which can be decoded with `base64 --decode`


### Python Virtual Environment

To setup the virtual environment for testing:

```bash
python -m venv ./.venv
source .venv/bin/activate
pip install -r requirements.txt
```

After this is done, you can simply reactivate the environment with:

```bash
source .venv/bin/activate
```

## Running the Tests

Running the tests is a simple task of running the following:

```bash
pytest
```

### Listing Test Cases

```bash
pytest --collect-only
```

### Run just one test

```bash
pytest tests/test_crypto_policies.py::test_default_basic
```

## Notes / "Hard" parts.

 - Came across significant challenges attempting to run certain commands on the guest/test host due to SELinux.
   Eventually found a workaround to allow the guest additions to be permissive but not affect the rest of the system.
 - Some of the VM setup could likely be done through additional test automation. The addition of sha1 to the server's
   configuration comes to mind.
 - For a "true" production-ready solution, it's worth contemplating if worth doing with two VM's, one host and one client.
   Would be more flexible and repeatable for tests.