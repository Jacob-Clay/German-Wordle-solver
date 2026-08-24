import tkinter as tk
from collections.abc import Callable, Sequence
from functools import partial
from pathlib import Path

WORDS_FILE = Path("5words.txt")


"""
A row of single-character entry boxes
"""


def load_words(path: Path) -> list[str]:
    """One word per line, UTF-8 blank lines skipped, lowercase once here."""
    with path.open(encoding="utf-8") as f:
        return [stripped.lower() for line in f if (stripped := line.strip())]


def matches(word: str, pattern: str, required: str = "", excluded: str = "") -> bool:
    """`pattern` uses '.' for unknown positions. Everything lowercase."""
    if any(p != "." and p != w for p, w in zip(pattern, word, strict=True)):
        return False
    if any(r not in word for r in required):
        return False
    return all(e not in word for e in excluded)


def find_matches(
    pattern: str, words: Sequence[str], required: str = "", excluded: str = ""
) -> list[str]:
    pattern = pattern.lower()
    return [w for w in words if matches(w, pattern, required, excluded)]


class LettersInput(tk.Frame):
    """
    `length` Entry boxes side to side, each holding one letter

    Typing a letter replaces whatever is in the focused box and advances.
    Non-letters are rejected. Backspace on an emtpy box steps back, and
    Left/Right/Home/End move between boxes.
    """

    def __init__(self, parent: tk.Misc, length: int = 5):
        super().__init__(parent)
        self.boxes: list[tk.Entry] = []
        self.on_submit: Callable[[str], None] | None = None

        for i in range(length):
            var = tk.StringVar()
            box = tk.Entry(
                self,
                textvariable=var,
                width=2,
                font=("Helvetica", 32),
                justify="center",
            )
            box.grid(row=0, column=i, padx=4)
            _ = box.bind("<KeyPress>", lambda e, i=i: self._on_key(i, e))
            _ = box.bind("<BackSpace>", lambda _e, i=i: self._on_backspace(i))
            _ = box.bind("<Left>", lambda _e, i=i: self._move(i - 1))
            _ = box.bind("<Right>", lambda _e, i=i: self._move(i + 1))
            _ = box.bind("<Home>", lambda _e: self._move(0))
            _ = box.bind("<End>", lambda _e: self._move(length - 1))
            _ = box.bind("<<Paste>>", lambda _e, i=i: self._on_paste(i))
            _ = box.bind("<Return>", lambda _e: self._submit())
            _ = box.bind("<KP_Enter>", lambda _e: self._submit())

            self.boxes.append(box)

    # --- helpers -------------------------------------------------------------

    def _focus(self, index: int):
        """Focus a box and select it's contents, so the next letter replaces it"""
        box = self.boxes[index]
        box.focus_set()
        box.select_range(0, "end")
        box.icursor("end")

    def _move(self, index: int) -> str:
        """Move focus, capping at the ends. returns 'break' for bindings."""
        self._focus(min(max(0, index), len(self.boxes) - 1))
        return "break"

    def _set(self, index: int, char: str):
        box = self.boxes[index]
        box.delete(0, "end")
        box.insert(0, char)

    # --- event handlers ------------------------------------------------------

    def _on_key(self, index: int, event: "tk.Event[tk.Entry]") -> str | None:
        char = event.char
        if not char or not char.isprintable():
            return None
        if not char.isalnum():
            return "break"
        self._set(index, char)
        if index + 1 < len(self.boxes):
            self._focus(index + 1)
        else:
            self.boxes[index].select_range(0, "end")
        return "break"

    def _on_backspace(self, index: int) -> str | None:
        if not self.boxes[index].get() and index > 0:
            self._focus(index - 1)
            self.boxes[index - 1].delete(0, "end")
            return "break"
        return None

    def _on_paste(self, index: int) -> str:
        try:
            pasted = self.clipboard_get()
        except tk.TclError:
            return "break"

        letters = [c for c in pasted if c.isalpha()][: len(self.boxes) - index]
        for offset, char in enumerate(letters):
            self._set(index + offset, char)
        self._focus(min(index + len(letters), len(self.boxes) - 1))
        return "break"

    def _submit(self) -> str:
        if self.on_submit is not None:
            self.on_submit(self.get())
        return "break"

    # --- public API ----------------------------------------------------------

    def get(self, blank: str = ".") -> str:
        return "".join(box.get() or blank for box in self.boxes)

    def is_complete(self) -> bool:
        return all(box.get() for box in self.boxes)

    def clear(self):
        for box in self.boxes:
            box.delete(0, "end")
        self._focus(0)


class ResultsView(tk.Frame):
    def __init__(self, parent: tk.Misc, height: int = 12):
        super().__init__(parent)

        self.status: tk.Label = tk.Label(
            self, text="", font=("Helvetica", 11), anchor="w"
        )
        self.status.pack(fill="x", pady=(0, 6))

        body = tk.Frame(self)
        body.pack(fill="both", expand=True)

        self.listbox: tk.Listbox = tk.Listbox(
            body, height=height, font=("Helvetica", 13)
        )
        scroll = tk.Scrollbar(body, orient="vertical", command=self.listbox.yview)
        _ = self.listbox.config(yscrollcommand=scroll.set)

        scroll.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)

    def show(self, pattern: str, words: Sequence[str]):
        self.listbox.delete(0, "end")
        self.listbox.insert("end", *words)
        plural = "" if len(words) == 1 else "es"
        _ = self.set_status(f"{pattern} - {len(words)} match{plural}")

    def set_status(self, text: str):
        _ = self.status.config(text=text)


def search(pattern: str, words: Sequence[str], results: ResultsView):
    results.show(pattern, find_matches(pattern, words))


def main():
    try:
        words = load_words(WORDS_FILE)
        loaded = f"{len(words)} words loaded"
    except OSError:
        words = []
        loaded = f"Could not read {WORDS_FILE}"

    root = tk.Tk()
    root.title("German Wordle Solver")
    root.geometry("440x520")

    tk.Label(root, text="Enter all Green Letters", font=("Helvetica", 14)).pack(
        pady=(20, 12)
    )

    greens = LettersInput(root)
    greens.pack()

    results = ResultsView(root)
    run = partial(search, words=words, results=results)
    greens.on_submit = run

    buttons = tk.Frame(root)
    buttons.pack(pady=18)
    tk.Button(buttons, text="Submit", command=lambda: run(greens.get())).pack(
        side="left", padx=6
    )
    tk.Button(buttons, text="Clear", command=greens.clear).pack(side="left", padx=6)

    results.pack(fill="both", expand=True, padx=24, pady=(0, 24))
    results.set_status(loaded)

    greens.boxes[0].focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
