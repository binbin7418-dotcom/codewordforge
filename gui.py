#!/usr/bin/env python3
"""CodeWordForge desktop shell (tkinter).
Set book options -> verified codeword interior PDF + build report."""
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from codeword_forge import build_book


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("CodeWordForge — Codeword Puzzle Book Generator")
        self.geometry("700x580")
        self.count = tk.StringVar(value="50")
        self.size = tk.StringVar(value="15")
        self.givens = tk.StringVar(value="3")
        self.trim = tk.StringVar(value="6x9")
        self.booktitle = tk.StringVar(value="Codeword Puzzle Book")
        tk.Label(self, text="Book title:").pack(anchor="w", padx=12, pady=(12, 2))
        tk.Entry(self, textvariable=self.booktitle).pack(fill="x", padx=12)
        tk.Label(self, text="Number of puzzles:").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Combobox(self, textvariable=self.count, values=["25", "50", "100", "200"],
                     state="readonly").pack(fill="x", padx=12)
        tk.Label(self, text="Grid size:").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Combobox(self, textvariable=self.size, values=["13", "15"],
                     state="readonly").pack(fill="x", padx=12)
        tk.Label(self, text="Given letters per puzzle:").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Combobox(self, textvariable=self.givens, values=["2", "3", "4"],
                     state="readonly").pack(fill="x", padx=12)
        tk.Label(self, text="Trim size (inches):").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Combobox(self, textvariable=self.trim, values=["6x9", "7x10", "8.5x11"],
                     state="readonly").pack(fill="x", padx=12)
        self.btn = tk.Button(self, text="Generate Book & Verify", command=self.run, height=2)
        self.btn.pack(pady=12)
        self.log = scrolledtext.ScrolledText(self, wrap="word")
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.write("CodeWordForge builds a print-ready codeword puzzle book interior:\n"
                   "interlocking word grids, a number key per puzzle, a few given\n"
                   "letters, and a solutions section. Every puzzle is verified —\n"
                   "valid word runs, a one-to-one number key, consistent givens —\n"
                   "before it is allowed into the book. Everything runs locally.\n")

    def write(self, s):
        self.log.insert("end", s)
        self.log.see("end")

    def run(self):
        self.btn.config(state="disabled")
        threading.Thread(target=self._work, daemon=True).start()

    def _work(self):
        try:
            outdir = os.path.join(os.path.expanduser("~"), "CodeWordForge_output")
            s = build_book(int(self.count.get()), outdir,
                           size=int(self.size.get()),
                           givens=int(self.givens.get()),
                           trim=self.trim.get(),
                           title=self.booktitle.get() or "Codeword Puzzle Book")
            self.write(f"\nDone. {len(s['puzzles'])}/{self.count.get()} puzzles built "
                       f"and verified ({s['pages']} pages). Failures discarded: "
                       f"{s['failures']}.\nInterior PDF: {s['pdf_path']}\n"
                       f"Report: {s['report_path']}\n")
            if not s["verdict"]:
                messagebox.showwarning(
                    "CodeWordForge",
                    "Some puzzles failed generation and were discarded — "
                    "see the report, then run again to top up.")
        except Exception as e:
            self.write(f"\nError: {e}\n")
        finally:
            self.btn.config(state="normal")


if __name__ == "__main__":
    App().mainloop()
