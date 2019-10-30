from ansible.plugins.test.core import skipped, success

def exec_ok(result):
    return (not skipped(result) and success(result))

class TestModule:
    """Main test class from Ansible."""

    def tests(self):
        """Add these tests to the list of tests available to Ansible."""
        return {
            'exec_ok': exec_ok,
        }
