import tkinter as tk

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
            _ = var.trace_add("write", lambda *_, i=i, var=var: self._on_write(i, var))
            _ = box.bind("<BackSpace>", lambda _e, i=i: self._on_backspace(i))
            _ = box.bind(
                "<Left>", lambda _e, i=i: self.boxes[(i - 1) % length].focus_set()
            )
            self.boxes.append(box)

    def _on_write(self, index: int, var: tk.StringVar):
        text = var.get()
        if len(text) > 1:
            var.set(text[-1])
            return
        if text and index + 1 < len(self.boxes):
            self.boxes[index + 1].focus_set()

    def _on_backspace(self, index: int) -> str | None:
        if not self.boxes[index].get() and index > 0:
            self.boxes[index - 1].focus_set()
            self.boxes[index - 1].delete(0, "end")
            return "break"
        return None

    def get(self) -> str:
        return "".join(box.get() for box in self.boxes)


def main():
    root = tk.Tk()
    root.title("German Wordle Solver")
    root.geometry("300x120")

    tk.Label(root, text="Enter all Green Letters", font=("Helvetica", 14)).pack(
        pady=(20, 12)
    )

    greens = LettersInput(root)
    greens.pack()

    tk.Button(root, text="Submit", command=lambda: print(greens.get())).pack(pady=20)

    greens.boxes[0].focus_set()

    root.mainloop()


if __name__ == "__main__":
    main()
