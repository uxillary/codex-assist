import tkinter as tk
from tkinter import filedialog, messagebox
from datetime import datetime
from typing import Dict, Optional

from logging_bus import (
    subscribe,
    snapshot,
    set_log_level_filter,
    set_kind_filter,
    set_verbose,
    get_verbose,
    set_file_logger,
)


class ActivityConsole(tk.Frame):
    def __init__(self, master, ctx):
        super().__init__(master)
        self.ctx = ctx
        self.paused = False
        self._build_ui()
        self.last_ts = 0.0
        for evt in snapshot():
            self._append(evt)
            self.last_ts = evt.ts

        def on_evt(evt):
            if self.paused:
                return
            self.after(0, lambda e=evt: (self._append(e), setattr(self, 'last_ts', e.ts)))

        subscribe(on_evt)

    def _build_ui(self) -> None:
        tb = tk.Frame(self)
        tb.pack(fill="x")
        self.verbose_var = tk.BooleanVar(value=get_verbose())
        tk.Checkbutton(tb, text="Verbose", variable=self.verbose_var, command=self._on_verbose).pack(
            side="left"
        )
        self.info_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tb, text="Info", variable=self.info_var, command=self._on_levels).pack(side="left")
        self.warn_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tb, text="Warn", variable=self.warn_var, command=self._on_levels).pack(side="left")
        self.err_var = tk.BooleanVar(value=True)
        tk.Checkbutton(tb, text="Error", variable=self.err_var, command=self._on_levels).pack(side="left")

        self.kind_vars: Dict[str, tk.BooleanVar] = {}
        for k in ("BUILD", "NETWORK", "STREAM", "COST", "SYSTEM"):
            v = tk.BooleanVar(value=True)
            self.kind_vars[k] = v
            tk.Checkbutton(tb, text=k.title(), variable=v, command=self._on_kinds).pack(side="left")

        tk.Button(tb, text="Pause", command=self._toggle_pause).pack(side="right")
        tk.Button(tb, text="Copy", command=self._copy).pack(side="right")
        tk.Button(tb, text="Clear Log", command=self._clear).pack(side="right")
        tk.Button(tb, text="Save…", command=self._save).pack(side="right")
        tk.Button(tb, text="Log File…", command=self._choose_file).pack(side="right")

        self.text = tk.Text(self, wrap="word", height=12, state="disabled")
        scroll = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=scroll.set)
        self.text.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.text.tag_config("INFO", foreground="black")
        self.text.tag_config("WARN", foreground="orange")
        self.text.tag_config("ERROR", foreground="red")

    def _fmt(self, evt) -> str:
        ts = datetime.fromtimestamp(evt.ts).strftime("%H:%M:%S")
        return f"[{ts}] {evt.level:<5} {evt.kind:<7} — {evt.msg} {evt.meta}\n"

    def _append(self, evt) -> None:
        self.text.configure(state="normal")
        self.text.insert("end", self._fmt(evt), evt.level)
        self.text.see("end")
        self.text.configure(state="disabled")

    def _toggle_pause(self) -> None:
        was_paused = self.paused
        self.paused = not self.paused
        if was_paused and not self.paused:
            for evt in snapshot():
                if evt.ts > self.last_ts:
                    self._append(evt)
                    self.last_ts = evt.ts

    def _copy(self) -> None:
        data = self.text.get("1.0", "end-1c")
        self.clipboard_clear()
        self.clipboard_append(data)

    def _clear(self) -> None:
        self.text.configure(state="normal")
        self.text.delete("1.0", "end")
        self.text.configure(state="disabled")

    def _save(self) -> None:
        data = self.text.get("1.0", "end-1c")
        path = filedialog.asksaveasfilename(
            defaultextension=".log", filetypes=[("Log", "*.log"), ("Text", "*.txt")]
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(data)
            except Exception as e:
                messagebox.showerror("Save failed", str(e))

    def _choose_file(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".jsonl",
            filetypes=[("JSON Lines", "*.jsonl"), ("All", "*.*")],
        )
        if path:
            set_file_logger(path)
            self.ctx.settings["activity_log_file"] = path
        else:
            set_file_logger(None)
            self.ctx.settings["activity_log_file"] = None
        self.ctx.save_settings()

    def _on_verbose(self) -> None:
        v = self.verbose_var.get()
        set_verbose(v)
        self.ctx.settings["verbose"] = v
        self.ctx.save_settings()

    def _on_levels(self) -> None:
        set_log_level_filter({
            "INFO": self.info_var.get(),
            "WARN": self.warn_var.get(),
            "ERROR": self.err_var.get(),
        })

    def _on_kinds(self) -> None:
        set_kind_filter({k: v.get() for k, v in self.kind_vars.items()})

    def show(self) -> None:
        self.pack(fill="both", side="bottom")

    def hide(self) -> None:
        self.pack_forget()

    def apply_settings(self, s: Dict[str, Optional[str]]) -> None:
        if "verbose" in s:
            self.verbose_var.set(bool(s["verbose"]))
            set_verbose(bool(s["verbose"]))
        if "activity_log_file" in s:
            path = s.get("activity_log_file")
            set_file_logger(path)
