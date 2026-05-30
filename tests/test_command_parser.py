import unittest

from abqjobpilot.command_parser import CommandParseError, extract_agent_commands, parse_agent_command


class TestCommandParser(unittest.TestCase):
    def test_enqueue_windows_path_with_quotes(self):
        parsed = parse_agent_command(
            'enqueue --inp "D:\\Projects\\some folder\\Job_test.inp" --cpus 14 '
            "--batch 32track_full --strategy center_out"
        )
        self.assertEqual(parsed["command"], "enqueue")
        self.assertEqual(parsed["inp"], "D:\\Projects\\some folder\\Job_test.inp")
        self.assertEqual(parsed["cpus"], 14)
        self.assertIsNone(parsed["gpus"])
        self.assertEqual(parsed["batch_name"], "32track_full")
        self.assertEqual(parsed["strategy_name"], "center_out")

    def test_enqueue_folder_defaults(self):
        parsed = parse_agent_command('enqueue-folder --folder "D:\\Projects\\strategy"')
        self.assertEqual(parsed["command"], "enqueue-folder")
        self.assertEqual(parsed["pattern"], "*.inp")
        self.assertIsNone(parsed["cpus"])
        self.assertIsNone(parsed["gpus"])

    def test_enqueue_gpu_argument(self):
        parsed = parse_agent_command('enqueue --inp "D:\\Projects\\Job_test.inp" --gpus 1')
        self.assertEqual(parsed["gpus"], 1)

    def test_list_help_clear(self):
        self.assertEqual(parse_agent_command("list")["command"], "list")
        self.assertEqual(parse_agent_command("help")["command"], "help")
        self.assertEqual(parse_agent_command("clear")["command"], "clear")

    def test_unknown_command_rejected(self):
        with self.assertRaises(CommandParseError):
            parse_agent_command("dir")

    def test_extract_multiple_ai_commands(self):
        pasted = """
        Here are the commands:
        ```text
        1. enqueue --inp "D:\\Projects\\A\\Job_a.inp"
        - enqueue-folder --folder "D:\\Projects\\B" --gpus 1
        ```
        """
        commands = extract_agent_commands(pasted)
        self.assertEqual(len(commands), 2)
        self.assertTrue(commands[0].startswith("enqueue --inp"))
        self.assertTrue(commands[1].startswith("enqueue-folder --folder"))


if __name__ == "__main__":
    unittest.main()
