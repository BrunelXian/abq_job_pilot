"""Tkinter Agent Command Console."""

from __future__ import annotations

import tkinter as tk
from tkinter import scrolledtext, ttk

from .command_parser import HELP_TEXT, CommandParseError, extract_agent_commands, parse_agent_command
from .queue_store import add_folder_to_queue, add_inp_job_to_queue, load_queue
from .settings_store import load_settings


EXAMPLE_COMMANDS = (
    'enqueue --inp "D:\\Projects\\RL-LAM-ScanOpt\\LDED_2D_CAE_Framework\\cae_models\\'
    '32track_full\\center_out\\Job_2D_32track_full_center_out.inp" --batch 32track_full '
    '--strategy center_out\n'
    'enqueue-folder --folder "D:\\Projects\\RL-LAM-ScanOpt\\LDED_2D_CAE_Framework\\cae_models\\'
    '32track_full\\teacher_pool_full20_v01\\random_scan_1" --pattern "*.inp"'
)


AI_SKILL_PROMPT = """You are generating abqjobpilot Agent Command strings.

Output only plain text commands, one command per line. Do not use Markdown.
Allowed commands:
enqueue --inp "D:\\path\\Job_xxx.inp" --cpus 14 --gpus 1 --batch batch_name --strategy strategy_name
enqueue-folder --folder "D:\\path\\strategy_folder" --pattern "*.inp" --cpus 14 --gpus 1 --batch batch_name --strategy strategy_name
list
help

Rules:
- Use quoted Windows paths.
- Include --cpus only if the user explicitly gave a CPU count.
- Include --gpus only if the user explicitly asked for GPU or gave a GPU count.
- If CPU/GPU are not specified, omit them so abqjobpilot uses Settings.
- Never output shell commands, Python code, PowerShell, explanations, or bullets.
"""


class AgentCommandConsole(tk.Toplevel):
    def __init__(self, master, on_queue_changed=None):
        super().__init__(master)
        self.title("Agent Command Console")
        self.geometry("1040x760")
        self.minsize(860, 620)
        self.on_queue_changed = on_queue_changed

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        self.rowconfigure(4, weight=2)
        self._build_widgets()
        self._append_output(HELP_TEXT)
        self.input_text.focus_set()

    def _build_widgets(self) -> None:
        skill_frame = ttk.LabelFrame(self, text="AI Skill Prompt", padding=8)
        skill_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 6))
        skill_frame.columnconfigure(0, weight=1)
        self.skill_text = tk.Text(skill_frame, height=6, wrap="word")
        self.skill_text.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self.skill_text.insert("1.0", AI_SKILL_PROMPT)
        self.skill_text.configure(state="disabled")
        ttk.Button(skill_frame, text="Copy AI Prompt", command=self.copy_ai_prompt).grid(row=0, column=1, sticky="n")

        input_frame = ttk.LabelFrame(self, text="Paste Commands", padding=8)
        input_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 6))
        input_frame.columnconfigure(0, weight=1)
        input_frame.rowconfigure(0, weight=1)
        self.input_text = scrolledtext.ScrolledText(input_frame, height=8, wrap="word")
        self.input_text.grid(row=0, column=0, sticky="nsew")
        self.input_text.insert("1.0", "help")

        button_frame = ttk.Frame(self, padding=(10, 0, 10, 6))
        button_frame.grid(row=2, column=0, sticky="ew")
        ttk.Button(button_frame, text="Run Commands", command=self.run_commands).grid(row=0, column=0, padx=(0, 6))
        ttk.Button(button_frame, text="Clear Input", command=self.clear_input).grid(row=0, column=1, padx=(0, 6))
        ttk.Button(button_frame, text="Clear Output", command=self.clear_output).grid(row=0, column=2, padx=(0, 6))
        ttk.Button(button_frame, text="Copy Examples", command=self.copy_examples).grid(row=0, column=3, padx=(0, 6))

        help_frame = ttk.LabelFrame(self, text="Supported Internal Commands", padding=8)
        help_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(0, 6))
        help_text = (
            'enqueue --inp "D:\\path\\Job_xxx.inp" --cpus 14 --gpus 1\n'
            'enqueue-folder --folder "D:\\path\\strategy_folder" --cpus 14 --gpus 1\n'
            "list | help | clear\n"
            "Multiple commands are supported. One command per line."
        )
        ttk.Label(help_frame, text=help_text, justify="left").grid(row=0, column=0, sticky="w")

        output_frame = ttk.LabelFrame(self, text="Output", padding=8)
        output_frame.grid(row=4, column=0, sticky="nsew", padx=10, pady=(0, 10))
        output_frame.rowconfigure(0, weight=1)
        output_frame.columnconfigure(0, weight=1)
        self.output = scrolledtext.ScrolledText(output_frame, wrap="word", state="disabled")
        self.output.grid(row=0, column=0, sticky="nsew")

    def _append_output(self, text: str) -> None:
        self.output.configure(state="normal")
        if self.output.get("1.0", "end-1c"):
            self.output.insert("end", "\n")
        self.output.insert("end", text.rstrip() + "\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def clear_input(self) -> None:
        self.input_text.delete("1.0", "end")

    def clear_output(self) -> None:
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def copy_ai_prompt(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(AI_SKILL_PROMPT)

    def copy_examples(self) -> None:
        self.clipboard_clear()
        self.clipboard_append(EXAMPLE_COMMANDS)
        self.input_text.delete("1.0", "end")
        self.input_text.insert("1.0", EXAMPLE_COMMANDS)

    def run_commands(self) -> None:
        pasted_text = self.input_text.get("1.0", "end-1c")
        commands = extract_agent_commands(pasted_text)
        if not commands:
            self._append_output("ERROR: no supported Agent Command lines found.")
            return

        any_queue_change = False
        for command_text in commands:
            result = self._run_one_command(command_text)
            any_queue_change = any_queue_change or bool(result.get("queue_changed"))
        if any_queue_change and self.on_queue_changed:
            self.on_queue_changed()

    def _run_one_command(self, command_text: str) -> dict:
        try:
            parsed = parse_agent_command(command_text)
        except CommandParseError as exc:
            self._append_output(f"> {command_text}\n\nERROR: {exc}")
            return {"queue_changed": False}

        command = parsed["command"]
        if command == "clear":
            self.clear_output()
            return {"queue_changed": False}
        if command == "help":
            self._append_output(f"> {command_text}\n\n{HELP_TEXT}")
            return {"queue_changed": False}
        if command == "list":
            self._append_output(f"> {command_text}\n\n{self._format_queue_list()}")
            return {"queue_changed": False}
        if command == "enqueue":
            result = self._enqueue(parsed)
            self._append_output(f"> {command_text}\n\n{self._format_enqueue_result(result)}")
            return {"queue_changed": bool(result.get("ok"))}
        if command == "enqueue-folder":
            result = self._enqueue_folder(parsed)
            self._append_output(f"> {command_text}\n\n{self._format_folder_result(result)}")
            return {"queue_changed": bool(result.get("added"))}
        self._append_output(f"> {command_text}\n\nERROR: unsupported command: {command}")
        return {"queue_changed": False}

    def _resource_defaults(self, parsed: dict) -> tuple[int, int]:
        settings = load_settings()
        cpus = parsed["cpus"] if parsed.get("cpus") is not None else settings["default_cpus"]
        gpus = parsed["gpus"] if parsed.get("gpus") is not None else (
            settings["default_gpus"] if settings["use_gpu"] else 0
        )
        return cpus, gpus

    def _enqueue(self, parsed: dict) -> dict:
        cpus, gpus = self._resource_defaults(parsed)
        return add_inp_job_to_queue(
            parsed["inp"],
            cpus=cpus,
            gpus=gpus,
            batch_name=parsed.get("batch_name"),
            strategy_name=parsed.get("strategy_name"),
            job_name=parsed.get("job_name"),
            run_datacheck=parsed.get("datacheck", True),
            run_full=parsed.get("full_run", True),
            notes=parsed.get("notes", ""),
        )

    def _enqueue_folder(self, parsed: dict) -> dict:
        cpus, gpus = self._resource_defaults(parsed)
        return add_folder_to_queue(
            parsed["folder"],
            pattern=parsed.get("pattern", "*.inp"),
            cpus=cpus,
            gpus=gpus,
            batch_name=parsed.get("batch_name"),
            strategy_name=parsed.get("strategy_name"),
        )

    def _format_enqueue_result(self, result: dict) -> str:
        if not result.get("ok"):
            return result.get("message", "ERROR: failed to add job")
        return (
            "OK: added job to queue\n"
            f"Queue ID: {result['queue_id']}\n"
            f"Job: {result['job_name']}\n"
            f"Strategy: {result['strategy_name']}\n"
            f"Batch: {result['batch_name']}\n"
            f"CPUs: {result['cpus']}\n"
            f"GPUs: {result.get('gpus', 0)}\n"
            f"Work dir: {result['work_dir']}\n"
            f"Queue position: {result['queue_position']}"
        )

    def _format_folder_result(self, result: dict) -> str:
        lines: list[str] = []
        if result.get("added"):
            lines.append(f"OK: added {len(result['added'])} job(s) to queue")
            for item in result["added"]:
                lines.append(
                    f"- {item['job_name']} | {item['strategy_name']} | "
                    f"CPUs {item['cpus']} | GPUs {item.get('gpus', 0)} | position {item['queue_position']}"
                )
        if result.get("errors"):
            if lines:
                lines.append("")
            lines.append("Errors:")
            lines.extend(result["errors"])
        if not lines:
            lines.append(result.get("message", "ERROR: no jobs were added"))
        return "\n".join(lines)

    def _format_queue_list(self) -> str:
        jobs = load_queue()
        if not jobs:
            return "Queue is empty."
        header = "index | status | batch_name | strategy_name | job_name | inp_path | cpus | gpus | created_at"
        lines = [header, "-" * len(header)]
        for index, job in enumerate(jobs, start=1):
            lines.append(
                f"{index} | {job.get('status', '')} | {job.get('batch_name', '')} | "
                f"{job.get('strategy_name', '')} | {job.get('job_name', '')} | "
                f"{job.get('inp_path', '')} | {job.get('cpus', '')} | "
                f"{job.get('gpus', 0)} | {job.get('created_at', '')}"
            )
        return "\n".join(lines)
