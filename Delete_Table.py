from tkinter import *
from tkinter import messagebox
from db import con, cur


class Delete_Table:
    def __init__(self, root_window):
        self.confroot = root_window

        self.delete_frame = Frame(self.confroot)
        self.delete_frame.pack()

        self.delete_label = Label(self.delete_frame,
                                  text="Select a Table to delete",
                                  font=("arial", 10),
                                  )
        self.delete_label.grid(row=1)

        self.Menu_button = Button(self.delete_frame,
                                  text="Go Back",
                                  font=("Arial", 10),
                                  command=self.go_back)
        self.Menu_button.grid(row=0)

        cur.execute("SELECT table_name FROM user_tab_comments WHERE comments = 'GUI_CREATED'")
        self.table_name = [entry[0] for entry in cur.fetchall()]

        self.table_box = Listbox(self.delete_frame,
                                 selectmode="multiple",
                                 font=("Arial", 10),)
        self.table_box.grid(row=2)

        for entry in self.table_name:
            self.table_box.insert(END, entry)

        self.Drop_Button = Button(self.delete_frame,
                                  text="Drop Table/Tables",
                                  font=("Arial", 10),
                                  command=self.drop_table_tables)
        self.Drop_Button.grid(row=3)

        self.status_label = Label(self.delete_frame,
                                  text="",
                                  font=("Arial", 10),
                                  fg="red")
        self.status_label.grid(row=4)

    def drop_table_tables(self):
        selected_indices = self.table_box.curselection()
        if not selected_indices:
            messagebox.showwarning("No selection", "Please select at least one table to delete.")
            return

        confirm = messagebox.askyesno("Confirm Drop", "Are you sure you want to drop the selected table(s)?")
        if not confirm:
            return

        for index in selected_indices:
            name = self.table_box.get(index)
            sql = f'DROP TABLE "{name}"'
            try:
                cur.execute(sql)
            except Exception as e:
                self.status_label.config(text=f"Error dropping {name}: {e}", fg="red")
                con.rollback()
                return

        con.commit()
        self.status_label.config(text=f"Selected table(s) dropped successfully!", fg="green")
        self.update()

    def update(self):
        self.table_box.delete(0, END)
        cur.execute("SELECT table_name FROM user_tab_comments WHERE comments = 'GUI_CREATED'")
        self.table_name = [entry[0] for entry in cur.fetchall()]
        for entry in self.table_name:
            self.table_box.insert(END, entry)

    def go_back(self):
        self.delete_frame.forget()
        from conf import conf
        conf(self.confroot)
