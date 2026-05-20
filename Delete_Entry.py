from tkinter import *
from tkinter import messagebox
from db import con, cur


class Delete_Entry:
    def __init__(self, root_window):
        self.confroot = root_window
        self.current_table = None
        self.current_rows = []

        self.top_frame = Frame(self.confroot)
        self.top_frame.pack(fill=X, padx=10, pady=10)

        self.table_frame = Frame(self.confroot)
        self.table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.bottom_frame = Frame(self.confroot)
        self.bottom_frame.pack(fill=X, padx=10, pady=10)

        self.go_back_button = Button(self.top_frame,
                                     text="Go Back",
                                     font=("Arial", 10),
                                     command=self.go_back)
        self.go_back_button.grid(row=0, column=0, padx=5)

        Label(self.top_frame,
              text="Select Table:",
              font=("Arial", 12)).grid(row=0, column=1, padx=5)

        self.table_var = StringVar(value="-- Select Table --")
        self.table_names = self._fetch_gui_tables()

        if self.table_names:
            self.table_dropdown = OptionMenu(self.top_frame,
                                             self.table_var,
                                             *self.table_names,
                                             command=self._on_table_selected)
        else:
            self.table_dropdown = OptionMenu(self.top_frame, self.table_var, "No tables found")

        self.table_dropdown.config(width=25)
        self.table_dropdown.grid(row=0, column=2, padx=5)

        self.refresh_button = Button(self.top_frame,
                                     text="Refresh",
                                     font=("Arial", 10),
                                     command=self._refresh_tables)
        self.refresh_button.grid(row=0, column=3, padx=5)

        self.status_label = Label(self.top_frame,
                                  text="",
                                  font=("Arial", 10),
                                  fg="red")
        self.status_label.grid(row=0, column=4, padx=10)

        self.rows_listbox = Listbox(self.table_frame,
                                    font=("Arial", 10),
                                    selectmode="multiple",
                                    width=120,
                                    height=20)
        self.rows_listbox.pack(side=LEFT, fill=BOTH, expand=True)

        self.rows_scroll = Scrollbar(self.table_frame, orient=VERTICAL, command=self.rows_listbox.yview)
        self.rows_scroll.pack(side=RIGHT, fill=Y)
        self.rows_listbox.config(yscrollcommand=self.rows_scroll.set)

        self.delete_button = Button(self.bottom_frame,
                                    text="Delete Selected Entries",
                                    font=("Arial", 10, "bold"),
                                    bg="#A32D2D",
                                    fg="#FFFFFF",
                                    command=self.delete_selected_rows)
        self.delete_button.pack(side=LEFT, padx=5)

    def _fetch_gui_tables(self):
        try:
            cur.execute("SELECT table_name FROM user_tab_comments WHERE comments = 'GUI_CREATED' ORDER BY table_name")
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching GUI tables: {e}")
            return []

    def _refresh_tables(self):
        self.table_names = self._fetch_gui_tables()
        menu = self.table_dropdown["menu"]
        menu.delete(0, "end")
        for t in self.table_names:
            menu.add_command(label=t, command=lambda value=t: self.table_var.set(value))

    def _on_table_selected(self, table_name):
        self.current_table = table_name
        self.current_rows = []
        self.status_label.config(text="")
        self.rows_listbox.delete(0, END)

        if not table_name or table_name == "-- Select Table --":
            return

        try:
            cur.execute(f'SELECT ROWID, * FROM "{table_name}"')
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description][1:]
        except Exception as e:
            self.status_label.config(text=f"Could not load rows: {e}", fg="red")
            return

        if not rows:
            self.rows_listbox.insert(END, "No entries found.")
            return

        for row in rows:
            rid = row[0]
            data = row[1:]
            row_text = " | ".join(str(val) for val in data)
            self.current_rows.append({"rowid": rid, "display": row_text})
            self.rows_listbox.insert(END, row_text)

    def delete_selected_rows(self):
        selected = self.rows_listbox.curselection()
        if not selected:
            messagebox.showwarning("No selection", "Please select at least one entry to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Delete the selected row(s)?")
        if not confirm:
            return

        try:
            for index in selected[::-1]:
                row_info = self.current_rows[index]
                cur.execute(f'DELETE FROM "{self.current_table}" WHERE ROWID = :rid', {"rid": row_info["rowid"]})

            con.commit()
            self.status_label.config(text="Selected entry row(s) deleted.", fg="green")
            self._on_table_selected(self.current_table)
        except Exception as e:
            con.rollback()
            self.status_label.config(text=f"Delete failed: {e}", fg="red")

    def go_back(self):
        self.top_frame.forget()
        self.table_frame.forget()
        self.bottom_frame.forget()
        from conf import conf
        conf(self.confroot)
