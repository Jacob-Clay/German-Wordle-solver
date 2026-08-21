import tkinter as tk
from collections.abc import Callable

"""
A row of single-character entry boxes
"""


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


def main():
    root = tk.Tk()
    root.title("German Wordle Solver")
    root.geometry("300x120")

    tk.Label(root, text="Enter all Green Letters", font=("Helvetica", 14)).pack(
        pady=(20, 12)
    )

    greens = LettersInput(root)
    greens.pack()

    result = tk.Label(root, text="", font=("Helvetica", 12))

    def submit(pattern: str):
        _ = result.config(text=f"Pattern: {pattern}")

    greens.on_submit = submit

    buttons = tk.Frame(root)
    buttons.pack(pady=18)

    tk.Button(buttons, text="Submit", command=lambda: submit(greens.get())).pack(
        side="left", padx=6
    )
    tk.Button(buttons, text="Clear", command=greens.clear).pack(side="left", padx=6)

    result.pack()

    greens.boxes[0].focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
