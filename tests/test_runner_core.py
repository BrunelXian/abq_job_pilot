import unittest

from abqjobpilot.runner_core import build_abaqus_full_run_command


class TestRunnerCore(unittest.TestCase):
    def test_full_run_command_includes_resources(self):
        command = build_abaqus_full_run_command(
            {
                "job_name": "Job_test",
                "inp_path": r"D:\Projects\abqjobpilot\tests\fixtures\Job_test.inp",
                "cpus": 12,
                "gpus": 1,
            }
        )
        self.assertIn("cpus=12", command)
        self.assertIn("gpus=1", command)
        self.assertIn("interactive", command)
        self.assertNotIn("shell=True", command)


if __name__ == "__main__":
    unittest.main()
