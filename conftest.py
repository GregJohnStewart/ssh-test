import pytest

from tests.testResources.VirtMngmt import VirtMngmt


@pytest.fixture(autouse=True, scope="session")
def setup_and_teardown_all_tests():
    print("\n[GLOBAL SETUP] Initializing test session resources...")
    VirtMngmt.setUp()

    yield  # All tests in the entire suite execute during this yield

    print("\n[GLOBAL TEARDOWN] Tearing down test session resources...")
    VirtMngmt.tearDown()

@pytest.fixture(autouse=True, scope="function")
def setup_and_teardown_each_test():
    print("\n[TEST SETUP] Initializing test session resources...")
    VirtMngmt.resetTestVm()

    yield  # All tests in the entire suite execute during this yield

    # Write code here to execute ONCE after all tests finish
    print("\n[Test TEARDOWN] Tearing down test session resources...")