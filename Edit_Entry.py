from tkinter import *
from tkinter import messagebox


class Edit_Entry():
    def __init__(self, root_window):
        self.confroot = root_window
        self.frame = Frame(self.confroot)
        self.frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        Button(self.frame,
               text="Go Back",
               font=("Arial", 10),
               command=self.go_back).pack(anchor=W)

        Label(self.frame,
              text="Edit Entry is not implemented yet.",
              font=("Arial", 12),
              fg="#444441").pack(pady=20)

    def go_back(self):
        self.frame.forget()
        from conf import conf
        conf(self.confroot)
