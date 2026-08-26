import tkinter as tk
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

WORDS_FILE = Path("5words.txt")

# --- query model -------------------------------------------------------------


@dataclass(frozen=True)
class Query:
    """A search. Everything lowercase '.' marks an unkown position"""

    pattern: str
    required: str = ""
    excluded: str = ""


def matches(word: str, query: Query) -> bool:
    if any(p != "." and p != w for p, w in zip(query.pattern, word, strict=True)):
        return False
    if any(r not in word for r in query.required):
        return False
    return all(e not in word for e in query.excluded)


def find_matches(query: Query, words: Sequence[str]) -> list[str]:
    return [w for w in words if matches(w, query)]


def load_words(path: Path) -> list[str]:
    """One word per line, UTF-8 blank lines skipped, lowercase once here."""
    with path.open(encoding="utf-8") as f:
        return [stripped.lower() for line in f if (stripped := line.strip())]


# --- widgets -------------------------------------------------------------


class LettersInput(tk.Frame):
    """
    `length` Entry boxes side to side, each holding one letter

    Typing a letter replaces whatever is in the focused box and advances.
    Non-letters are rejected. Backspace on an emtpy box steps back, and
    Left/Right/Home/End move between boxes.

    'on_submit' is called with no arguments when Enter is pressed; read the
    contents of 'get()'.
    """

    def __init__(self, parent: tk.Misc, length: int = 5):
        super().__init__(parent)
        self.boxes: list[tk.Entry] = []
        self.on_submit: Callable[[], None] | None = None

        for i in range(length):
            box = tk.Entry(
                self,
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
            _ = box.bind("<Return>", lambda _e: self._on_return())
            _ = box.bind("<KP_Enter>", lambda _e: self._on_return())

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

    def _on_return(self) -> str:
        self.submit()
        return "break"

    # --- public API ----------------------------------------------------------

    def submit(self):
        if self.on_submit is not None:
            self.on_submit()

    def get(self, blank: str = ".") -> str:
        return "".join(box.get().lower() or blank for box in self.boxes)

    def is_complete(self) -> bool:
        return all(box.get() for box in self.boxes)

    def focus_first(self):
        self._focus(0)

    def clear(self):
        for box in self.boxes:
            box.delete(0, "end")
        self._focus(0)


class LetterSet(tk.Frame):
    """A labelled entry holding an unordered set of letters

    Same three-member interface as LettersInput: 'on_submit', 'get()',
    'clear()'.
    """

    def __init__(self, parent: tk.Misc, label: str):
        super().__init__(parent)
        self.on_submit: Callable[[], None] | None = None

        tk.Label(self, text=label, font=("Helvetica", 11), anchor="w").pack(fill="x")

        self.entry: tk.Entry = tk.Entry(self, font=("Helvetica", 16))
        self.entry.pack(fill="x", pady=(2, 0))

        _ = self.entry.bind("<KeyPress>", self._on_key)
        _ = self.entry.bind("<Return>", lambda _e: self._on_return())
        _ = self.entry.bind("<KP_Enter>", lambda _e: self._on_return())

    def _on_key(self, event: "tk.Event[tk.Entry]") -> str | None:
        char = event.char
        if not char or not char.isprintable():
            return None
        return None if char.isalpha() else "break"

    def _on_return(self) -> str:
        self.submit()
        return "break"

    def submit(self):
        if self.on_submit is not None:
            self.on_submit()

    def get(self) -> str:
        return "".join(dict.fromkeys(self.entry.get().lower()))

    def clear(self):
        self.entry.delete(0, "end")


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

    def show(self, query: Query, words: Sequence[str]):
        self.listbox.delete(0, "end")
        self.listbox.insert("end", *words)
        plural = "" if len(words) == 1 else "es"
        _ = self.set_status(f"{query.pattern} - {len(words)} match{plural}")

    def set_status(self, text: str):
        _ = self.status.config(text=text)

    def clear(self):
        self.listbox.delete(0, "end")
        self.set_status("")

    # --- public API ----------------------------------------------------------


class App(tk.Tk):
    def __init__(self, words: Sequence[str], length: int = 5):
        super().__init__()
        self.words: Sequence[str] = words

        self.title("German Wordle Solver")
        self.geometry("460x600")

        tk.Label(self, text="Known letters", font=("Helvetica", 14)).pack(pady=(24, 10))

        self.pattern: LettersInput = LettersInput(self, length=length)
        self.pattern.pack()

        self.required: LetterSet = LetterSet(self, "Somewhere in the word")
        self.excluded: LetterSet = LetterSet(self, "Not in the word")
        self.required.pack(fill="x", padx=24, pady=(20, 0))
        self.excluded.pack(fill="x", padx=24, pady=(12, 0))

        self.inputs: list[LettersInput | LetterSet] = [
            self.pattern,
            self.required,
            self.excluded,
        ]
        for widget in self.inputs:
            widget.on_submit = self.submit

        buttons = tk.Frame(self)
        buttons.pack(pady=18)
        tk.Button(buttons, text="Search", command=self.submit).pack(side="left", padx=6)
        tk.Button(buttons, text="Clear", command=self.clear).pack(side="left", padx=6)

        self.results: ResultsView = ResultsView(self)
        self.results.pack(fill="both", expand=True, padx=24, pady=(0, 24))

        self.pattern.focus_first()

    def build_query(self) -> Query:
        return Query(
            pattern=self.pattern.get(),
            required=self.required.get(),
            excluded=self.excluded.get(),
        )

    def submit(self):
        query = self.build_query()
        conflict = set(query.required) & set(query.excluded)
        if conflict:
            self.results.clear()
            self.results.set_status(f"{''.join(sorted(conflict))} is both in and out")
            return
        self.results.show(query, find_matches(query, self.words))

    def clear(self):
        for widget in self.inputs:
            widget.clear()
        self.results.clear()
        self.pattern.focus_first()


def main():
    try:
        words = load_words(WORDS_FILE)
        loaded = f"{len(words)} words loaded"
    except OSError:
        words = []
        loaded = f"Could not read {WORDS_FILE}"

    app = App(words)
    app.results.set_status(loaded)
    app.mainloop()


if __name__ == "__main__":
    main()
