import sys
from tkinter import *
from tkinter import messagebox

import pprint
import oracledb
from oracledb import cursor

con = oracledb.connect(
    user="system",
    password="LF8",
    dsn="localhost:1251/XEPDB1"
)

cur = con.cursor()

# can i please just upd | Hatte problem mit Github über pycharm deswegen steht das hier

# Weiteres ich bin mitten im projekt jetzt von pycharm auf VScode umgestiegen weswegen ein zwei sachen jetzt auch anders sind

# Conf wurde verschönert per Claude, 
# grundfunktionen hatte ich selber geschrieben aber damit es halbwegs schön aussieht hab ich es aufbessern lassen.
#  Wenn ich mehr zeit hätte wäre ich noch auf QT6 umgestiegen aber eine GUI zu lernen passt nicht bis zum abgabe Termin.
class conf():
    def __init__(self, root_window):
        self.confroot = root_window
        self.confroot.title("DB Manager")
        self.confroot.geometry("680x520")
        self.confroot.configure(bg="#F8F7F4")

        self.conf_frame = Frame(self.confroot, bg="#F8F7F4")
        self.conf_frame.pack(fill=BOTH, expand=True, padx=30, pady=30)

        header_frame = Frame(self.conf_frame, bg="#F8F7F4")
        header_frame.pack(fill=X, pady=(0, 24))

        Label(header_frame,
              text="DB Manager",
              font=("Arial", 22, "bold"),
              bg="#F8F7F4",
              fg="#1A1A18").pack(side=LEFT)

        self.status_dot = Label(header_frame,
                                text="● Connected",
                                font=("Arial", 10),
                                bg="#F8F7F4",
                                fg="#3B6D11")
        self.status_dot.pack(side=RIGHT, pady=6)

        Frame(self.conf_frame, height=1, bg="#D3D1C7").pack(fill=X, pady=(0, 20))

        Label(self.conf_frame,
              text="What would you like to do?",
              font=("Arial", 12),
              bg="#F8F7F4",
              fg="#5F5E5A").pack(anchor=W, pady=(0, 14))

        card_grid = Frame(self.conf_frame, bg="#F8F7F4")
        card_grid.pack(fill=X, pady=(0, 24))
        card_grid.columnconfigure(0, weight=1)
        card_grid.columnconfigure(1, weight=1)

        card_specs = [
            ("Create", "Add new tables or entries", "#E1F5EE", "#0F6E56", "#085041", "Created"),
            ("Edit", "Modify existing data", "#E6F1FB", "#185FA5", "#0C447C", "Edit"),
            ("Delete", "Remove tables or entries", "#FCEBEB", "#A32D2D", "#791F1F", "Delete"),
            ("Query", "Browse & debug data", "#FAEEDA", "#854F0B", "#633806", "Query"),
        ]

        for i, (title, subtitle, bg, fg_title, fg_sub, op) in enumerate(card_specs):
            r, c = divmod(i, 2)
            btn_frame = Frame(card_grid,
                              bg=bg,
                              cursor="hand2",
                              relief=FLAT,
                              bd=0)
            btn_frame.grid(row=r, column=c, padx=6, pady=6, sticky="nsew")

            inner = Frame(btn_frame, bg=bg)
            inner.pack(fill=BOTH, expand=True, padx=18, pady=16)

            Label(inner,
                  text=title,
                  font=("Arial", 15, "bold"),
                  bg=bg,
                  fg=fg_title,
                  anchor=W).pack(anchor=W)

            Label(inner,
                  text=subtitle,
                  font=("Arial", 10),
                  bg=bg,
                  fg=fg_sub,
                  anchor=W).pack(anchor=W, pady=(2, 0))

            for widget in [btn_frame, inner] + inner.winfo_children():
                widget.bind("<Button-1>", lambda e, o=op: self.select_option(o))
                widget.bind("<Enter>", lambda e, f=btn_frame, b=bg: f.config(bg=self._darken(b)))
                widget.bind("<Leave>", lambda e, f=btn_frame, b=bg: f.config(bg=b))

        Frame(self.conf_frame, height=1, bg="#D3D1C7").pack(fill=X, pady=(4, 14))

        debug_frame = Frame(self.conf_frame, bg="#F8F7F4")
        debug_frame.pack(fill=X)

        Label(debug_frame,
              text="Debug tools",
              font=("Arial", 10),
              bg="#F8F7F4",
              fg="#888780").pack(side=LEFT, padx=(0, 12))

        self._make_debug_btn(debug_frame, "Print table schema", self.Query_DB)
        self._make_debug_btn(debug_frame, "Browse table entries", self.open_entry_viewer)

        

    def _make_debug_btn(self, parent, text, cmd):
        btn = Button(parent,
                     text=text,
                     font=("Arial", 9),
                     relief=FLAT,
                     bd=0,
                     bg="#E8E7E1",
                     fg="#444441",
                     activebackground="#D3D1C7",
                     activeforeground="#2C2C2A",
                     padx=10,
                     pady=5,
                     cursor="hand2",
                     command=cmd)
        btn.pack(side=LEFT, padx=(0, 8))
        return btn

    def _darken(self, hex_color):
        
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        factor = 0.92
        r, g, b = int(r * factor), int(g * factor), int(b * factor)
        return f"#{r:02x}{g:02x}{b:02x}"

        

    def Query_DB(self):
        query = """
                   SELECT
                       cols.table_name,
                       tab_comments.comments AS table_comment,
                       cols.column_name,
                       cols.data_type,
                       cols.data_length,
                       cols.data_precision,
                       cols.data_scale,
                       cons.constraint_type
                   FROM
                       user_tab_columns cols
                   LEFT JOIN
                       user_cons_columns cons_cols
                       ON cols.table_name = cons_cols.table_name
                       AND cols.column_name = cons_cols.column_name
                   LEFT JOIN
                       user_constraints cons
                       ON cons_cols.constraint_name = cons.constraint_name
                       AND cons.constraint_type IN ('P', 'R')
                   LEFT JOIN
                       user_tab_comments tab_comments
                       ON cols.table_name = tab_comments.table_name
                   WHERE
                       tab_comments.comments = 'GUI_CREATED'
                   ORDER BY
                       cols.table_name,
                       cols.column_id
               """
        cur.execute(query)
        result = cur.fetchall()
        pprint.pprint(result)

        

        

    def open_entry_viewer(self):
        """Open the entry-viewer: first pick a table, then see its rows."""
        
        try:
            cur.execute("""
                       SELECT table_name
                       FROM user_tab_comments
                       WHERE comments = 'GUI_CREATED'
                       ORDER BY table_name
                   """)
            tables = [row[0] for row in cur.fetchall()]
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not fetch tables:\n{e}")
            return

        if not tables:
            messagebox.showinfo("No tables", "No GUI-created tables found.")
            return

        
        picker = Toplevel(self.confroot)
        picker.title("Browse entries")
        picker.geometry("400x300")
        picker.configure(bg="#F8F7F4")
        picker.grab_set()

        Label(picker,
              text="Select a table to browse",
              font=("Arial", 13, "bold"),
              bg="#F8F7F4",
              fg="#1A1A18").pack(pady=(20, 8))

        Label(picker,
              text="Choose which table's entries you want to inspect.",
              font=("Arial", 10),
              bg="#F8F7F4",
              fg="#888780").pack(pady=(0, 14))

        Frame(picker, height=1, bg="#D3D1C7").pack(fill=X, padx=20, pady=(0, 10))

        list_frame = Frame(picker, bg="#F8F7F4")
        list_frame.pack(fill=BOTH, expand=True, padx=20)

        v_scroll = Scrollbar(list_frame, orient=VERTICAL)
        v_scroll.pack(side=RIGHT, fill=Y)

        lb = Listbox(list_frame,
                     font=("Arial", 11),
                     bg="#FFFFFF",
                     fg="#2C2C2A",
                     selectbackground="#B5D4F4",
                     selectforeground="#042C53",
                     activestyle="none",
                     relief=FLAT,
                     bd=1,
                     highlightthickness=0,
                     yscrollcommand=v_scroll.set)
        lb.pack(side=LEFT, fill=BOTH, expand=True)
        v_scroll.config(command=lb.yview)

        for t in tables:
            lb.insert(END, f"  {t}")

        btn_row = Frame(picker, bg="#F8F7F4")
        btn_row.pack(fill=X, padx=20, pady=12)

        def on_open():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("No selection", "Please select a table first.")
                return
            table_name = tables[sel[0]]
            picker.destroy()
            self._show_entry_table(table_name)

        Button(btn_row,
               text="Open",
               font=("Arial", 10, "bold"),
               bg="#1D9E75",
               fg="#FFFFFF",
               activebackground="#0F6E56",
               activeforeground="#FFFFFF",
               relief=FLAT,
               padx=16,
               pady=6,
               cursor="hand2",
               command=on_open).pack(side=LEFT, padx=(0, 8))

        Button(btn_row,
               text="Cancel",
               font=("Arial", 10),
               bg="#E8E7E1",
               fg="#444441",
               activebackground="#D3D1C7",
               relief=FLAT,
               padx=16,
               pady=6,
               cursor="hand2",
               command=picker.destroy).pack(side=LEFT)

        lb.bind("<Double-Button-1>", lambda e: on_open())

    def _show_entry_table(self, table_name):
        """Fetch and display all rows of *table_name* in a scrollable grid."""
        try:
            cur.execute(f'SELECT * FROM "{table_name}"')
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not query {table_name}:\n{e}")
            return

        
        viewer = Toplevel(self.confroot)
        viewer.title(f"Entries — {table_name}")
        viewer.geometry("860x520")
        viewer.configure(bg="#F8F7F4")

        
        hdr = Frame(viewer, bg="#F8F7F4")
        hdr.pack(fill=X, padx=20, pady=(16, 8))

        Label(hdr,
              text=table_name,
              font=("Arial", 15, "bold"),
              bg="#F8F7F4",
              fg="#1A1A18").pack(side=LEFT)

        Label(hdr,
              text=f"{len(rows)} row{'s' if len(rows) != 1 else ''}  ·  {len(columns)} column{'s' if len(columns) != 1 else ''}",
              font=("Arial", 10),
              bg="#F8F7F4",
              fg="#888780").pack(side=RIGHT, pady=4)

        Frame(viewer, height=1, bg="#D3D1C7").pack(fill=X, padx=20, pady=(0, 10))

        
        canvas_frame = Frame(viewer, bg="#F8F7F4")
        canvas_frame.pack(fill=BOTH, expand=True, padx=20, pady=(0, 16))

        v_sb = Scrollbar(canvas_frame, orient=VERTICAL)
        v_sb.pack(side=RIGHT, fill=Y)

        h_sb = Scrollbar(canvas_frame, orient=HORIZONTAL)
        h_sb.pack(side=BOTTOM, fill=X)

        canvas = Canvas(canvas_frame,
                        yscrollcommand=v_sb.set,
                        xscrollcommand=h_sb.set,
                        bg="#F8F7F4",
                        highlightthickness=0)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)

        v_sb.config(command=canvas.yview)
        h_sb.config(command=canvas.xview)

        inner = Frame(canvas, bg="#F8F7F4")
        cw = canvas.create_window((0, 0), window=inner, anchor=NW)

        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

       
        COL_W = 160
        HDR_BG = "#D3D1C7"
        HDR_FG = "#2C2C2A"
        ROW_BG = "#FFFFFF"
        ALT_BG = "#F1EFE8"
        CELL_FG = "#2C2C2A"
        NULL_FG = "#B4B2A9"

        
        Label(inner,
              text="#",
              font=("Arial", 9, "bold"),
              bg=HDR_BG,
              fg=HDR_FG,
              width=5,
              relief=FLAT,
              anchor=CENTER,
              pady=7).grid(row=0, column=0, padx=(0, 1), pady=(0, 1), sticky="nsew")

        for c_idx, col_name in enumerate(columns):
            Label(inner,
                  text=col_name,
                  font=("Arial", 9, "bold"),
                  bg=HDR_BG,
                  fg=HDR_FG,
                  width=COL_W // 8,
                  relief=FLAT,
                  anchor=W,
                  padx=8,
                  pady=7).grid(row=0, column=c_idx + 1,
                               padx=(0, 1), pady=(0, 1), sticky="nsew")

       
        if not rows:
            Label(inner,
                  text="No entries found.",
                  font=("Arial", 10),
                  bg=ROW_BG,
                  fg=NULL_FG,
                  pady=12).grid(row=1, column=0,
                                columnspan=len(columns) + 1,
                                sticky="nsew")
        else:
            for r_idx, row in enumerate(rows):
                bg = ROW_BG if r_idx % 2 == 0 else ALT_BG

                Label(inner,
                      text=str(r_idx + 1),
                      font=("Arial", 9),
                      bg=bg,
                      fg=NULL_FG,
                      width=5,
                      relief=FLAT,
                      anchor=CENTER,
                      pady=5).grid(row=r_idx + 1, column=0,
                                   padx=(0, 1), pady=(0, 1), sticky="nsew")

                for c_idx, value in enumerate(row):
                    is_null = value is None
                    display = "(null)" if is_null else str(value)
                    color = NULL_FG if is_null else CELL_FG

                    Label(inner,
                          text=display,
                          font=("Arial", 9),
                          bg=bg,
                          fg=color,
                          width=COL_W // 8,
                          relief=FLAT,
                          anchor=W,
                          padx=8,
                          pady=5).grid(row=r_idx + 1, column=c_idx + 1,
                                       padx=(0, 1), pady=(0, 1), sticky="nsew")

        Button(viewer,
               text="Close",
               font=("Arial", 10),
               bg="#E8E7E1",
               fg="#444441",
               activebackground="#D3D1C7",
               relief=FLAT,
               padx=16,
               pady=6,
               cursor="hand2",
               command=viewer.destroy).pack(pady=(0, 14))


    def select_option(self, operation_type):
        if operation_type == "Query":
            self.open_entry_viewer()
            return

        if operation_type == "Created":
            verb, adj = "Create", "new"
        elif operation_type == "Edit":
            verb, adj = "Edit", "existing"
        else:
            verb, adj = "Delete", "existing"

        dialog = Toplevel(self.confroot)
        dialog.title(verb)
        dialog.geometry("420x220")
        dialog.configure(bg="#F8F7F4")
        dialog.grab_set()

        Label(dialog,
              text=f"{verb} a {adj}…",
              font=("Arial", 14, "bold"),
              bg="#F8F7F4",
              fg="#1A1A18").pack(pady=(24, 6))

        Label(dialog,
              text=f"Would you like to {verb.lower()} a {adj} table or an entry inside a table?",
              font=("Arial", 10),
              bg="#F8F7F4",
              fg="#888780",
              wraplength=360).pack(pady=(0, 16))

        Frame(dialog, height=1, bg="#D3D1C7").pack(fill=X, padx=20, pady=(0, 16))

        btn_row = Frame(dialog, bg="#F8F7F4")
        btn_row.pack()

        Button(btn_row,
               text=f"  Table  ",
               font=("Arial", 11),
               bg="#1D9E75",
               fg="#FFFFFF",
               activebackground="#0F6E56",
               activeforeground="#FFFFFF",
               relief=FLAT,
               padx=14,
               pady=8,
               cursor="hand2",
               command=lambda: (dialog.destroy(),
                                self.selected_table(operation_type))).pack(side=LEFT, padx=8)

        Button(btn_row,
               text=f"  Entry  ",
               font=("Arial", 11),
               bg="#185FA5",
               fg="#FFFFFF",
               activebackground="#0C447C",
               activeforeground="#FFFFFF",
               relief=FLAT,
               padx=14,
               pady=8,
               cursor="hand2",
               command=lambda: (dialog.destroy(),
                                self.selected_entry(operation_type))).pack(side=LEFT, padx=8)

        Button(btn_row,
               text="Cancel",
               font=("Arial", 11),
               bg="#E8E7E1",
               fg="#444441",
               activebackground="#D3D1C7",
               relief=FLAT,
               padx=14,
               pady=8,
               cursor="hand2",
               command=dialog.destroy).pack(side=LEFT, padx=8)


    def selected_table(self, operation_type):
        self.conf_frame.forget()
        if operation_type == "Created":
            Created_Table(self.confroot)
        elif operation_type == "Edit":
            Edit_Table(self.confroot)
        elif operation_type == "Delete":
            Delete_Table(self.confroot)

    def selected_entry(self, operation_type):
        self.conf_frame.forget()
        if operation_type == "Created":
            Created_Entry(self.confroot)
        elif operation_type == "Edit":
            Edit_Entry(self.confroot)
        elif operation_type == "Delete":
            pass

# Die Funktion is zu 80% von mir, es wurde zwar bei Claude gefragt wie ich das in der theorie machen würde, aka den logischen ablauf.
# die 20% die ich mit Claude gemacht hatte war das erstellen und abfragen von foreign key weswegen ich auch bei der erstellung des
# Tables den commentar "GUI_CREATED" hinzufüge damit ich nur die Tables von Oracle bekomme die per der GUI kommen
# Das foreign key fenster wurde auch verschönert durch claude, da sonst dort nur eine auswahlbox wäre wo dann der key mit aufkommt
# Edit: Wie ich in der Delete Classe erwähne, die Create table ansicht ist auch von design non mir, das FK fenster ist aber wieder durch
# claude designed
class Created_Table():
    def __init__(self, root_window):
        self.confroot = root_window
        self.row_count = 1
        self.rows_data = []

        self.Create_TFrame = Frame(self.confroot)
        self.Create_TFrame.pack()

        self.add_frame = Frame(self.confroot)
        self.add_frame.pack()

        self.Menu_button = Button(self.Create_TFrame,
                                  text="Go Back",
                                  font=("Arial", 10),
                                  command=self.go_back)
        self.Menu_button.grid(row=0, column=0)

        self.label_name = Label(self.Create_TFrame,
                                text="Table Name: ",
                                font=("Arial", 15),
                                )
        self.label_name.grid(row=0, column=1)

        self.enter_table_name = Entry(self.Create_TFrame,)
        self.enter_table_name.grid(row=0, column=3  )

        self.entry_name_label = Label(self.Create_TFrame,
                                      text="Entry Name",
                                      font=("Arial", 10),
                                      )
        self.entry_name_label.grid(row=1, column=0)

        self.datatype_selected = Label(self.Create_TFrame,
                                       text="Datatype",
                                       font=("Arial", 10),
                                       )
        self.datatype_selected.grid(row=1, column=1)

        self.parameters = Label(self.Create_TFrame,
                                text="Parameters",
                                font=("Arial", 10),
                                )
        self.parameters.grid(row=1, column=2)

        self.pkey_label = Label(self.Create_TFrame,
                                text="Primary Key",
                                font=("Arial", 10),
                                )
        self.pkey_label.grid(row=1, column=3)

        self.fkey_label = Label(self.Create_TFrame,
                                text="Foreign Key",
                                font=("Arial", 10),
                                )
        self.fkey_label.grid(row=1, column=4)

        self.opt = StringVar(value="Select a datatyp.")

        self.dropdown_datatyps = ["NUMBER", "NUMBER(p,s)",
                                  "VARCHAR2(n)", "CHAR(n)", "CLOB",
                                  "DATE", "TIMESTAMP",
                                  ]


        self.select_typ = OptionMenu(self.add_frame, self.opt, *self.dropdown_datatyps,)
        self.select_typ.grid(row=0, column=1)

        self.row_button = Button(self.add_frame,
                                 text="+",
                                 font=("Arial", 10),
                                 command=self.create_row
                                 )
        self.row_button.grid(row=0, column=0)

        self.create_table = Button(self.add_frame,
                                   text="Create Table",
                                   font=("Arial", 10),
                                   command=self.generate_and_execute_sql
                                   )
        self.create_table.grid(row=0, column=3)

        self.status_label = Label(self.add_frame,
                                  text="",
                                  font=("Arial", 10),
                                  fg="red")
        self.status_label.grid(row=0, column=4)

    def create_row(self):
        selected_datatype = self.opt.get()
        print(selected_datatype)

        if selected_datatype == "Select a datatype":
            return

        self.row_count += 1
        current_row = self.row_count

        entry_name = Entry(self.Create_TFrame,)
        entry_name.grid(row=current_row, column=0)

        lbl_datatype = Label(self.Create_TFrame,
                             text=selected_datatype,
                             font=("Arial", 10),
                             )
        lbl_datatype.grid(row=current_row, column=1)

        entry_parameters = Entry(self.Create_TFrame,)
        entry_parameters.grid(row=current_row, column=2)

        if selected_datatype in ["NUMBER(p,s)", "VARCHAR2(n)", "CHAR(n)"]:
            entry_parameters.config(state=NORMAL)
        else:
            entry_parameters.config(state=DISABLED)

        var_pk = IntVar()
        check_pk = Checkbutton(self.Create_TFrame, variable=var_pk)
        check_pk.grid(row=current_row, column=3)

        var_fk = IntVar()
        check_fk = Checkbutton(self.Create_TFrame, variable=var_fk)
        check_fk.grid(row=current_row, column=4)

        delete_button = Button(self.Create_TFrame,
                               text="X",
                               font=("Arial", 8),
                               command=lambda: self.delete_row(current_row)
                               )
        delete_button.grid(row=current_row, column=5)

        self.rows_data.append({
            "entry_name": entry_name,
            "datatype": selected_datatype,
            "entry_parameters": entry_parameters,
            "var_pk": var_pk,
            "var_fk": var_fk,
            "row_number": current_row,
            "widgets": [entry_name, lbl_datatype, entry_parameters, check_pk, check_fk, delete_button]
        })

    def delete_row(self, row_number):

        print(row_number)

        row_index = None
        for i, row in enumerate(self.rows_data):
            if row["row_number"] == row_number:
                row_index = i
                break

        print(row_index)

        if row_index is None:
            print(f"Row {row_number} not found!")
            return

        for widget in self.rows_data[row_index]["widgets"]:
            widget.destroy()

        deleted_row = self.rows_data.pop(row_index)

        print(f"✓ Row {row_number} deleted (Column: {deleted_row['datatype']})")
        print(f"  Remaining rows: {len(self.rows_data)}")
        pprint.pprint(self.rows_data)

    def generate_and_execute_sql(self):
        self.status_label.config(text="", fg="black")

        table_name = self.enter_table_name.get().strip()


        if not table_name:
            self.status_label.config(text="Error: Table name is required", fg="red")
            return

        if not self.rows_data:
            self.status_label.config(text="Error: No columns definded!", fg="red")
            return

        column_definitions = []
        primary_keys = []
        foreign_keys = []

        for row in self.rows_data:
            column_name = row["entry_name"].get().strip()
            datatype = row["datatype"]
            parameters = row["entry_parameters"].get().strip()
            is_pk = row["var_pk"].get()
            print(is_pk)
            is_fk = row["var_fk"].get()

            if not column_name:
                self.status_label.config(text="Warning: Some rows have empty name!", fg="orange")
                continue

            if datatype == "NUMBER(p,s)":

                if not parameters:
                    self.status_label.config(text="Warning: Paramters has a empty value!", fg="orange")
                    return

                p, s = [x.strip() for x in parameters.split(",")]

                if int(p) < 1 or int(p) > 38:
                    self.status_label.config(text="Error: p must be between 1-38!", fg="red")
                    return

                if int(s) < -84 or int(s) > 127:
                    self.status_label.config(text="Error: s must be between -84 and 127!", fg="red")
                    return

                full_datatype = datatype.replace("(p,s)", F"({parameters})")
                column_definitions.append(f"{column_name} {full_datatype}")

            elif datatype == "VARCHAR2(n)":

                if not parameters:
                    self.status_label.config(text="Warning: Paramters has a empty value!", fg="orange")
                    return

                n = parameters

                if int(n) < 1 or int(n) > 4000:
                    self.status_label.config(text="Error: n must be between 1-4000!", fg="red")
                    return

                full_datatype = datatype.replace("(n)", F"({parameters})")
                column_definitions.append(f"{column_name} {full_datatype}")

            elif datatype == "CHAR(n)":

                if not parameters:
                    self.status_label.config(text="Warning: Paramters has a empty value!", fg="orange")
                    return

                n = parameters

                if int(n) < 1 or int(n) > 2000:
                    self.status_label.config(text="Error: n must be between 1-2000!", fg="red")
                    return

                full_datatype = datatype.replace("(n)", F"({parameters})")
                column_definitions.append(f"{column_name} {full_datatype}")

            else:
                column_definitions.append(f"{column_name} {datatype}")


            if is_pk and is_fk:
                self.status_label.config(text=f"Error: cannot use PK and FKs for the same row!", fg="red")
                return

            if is_pk:
                print(column_definitions)
                # column_definitions[-1] += " Primary Key"
                primary_keys.append(column_name)


            if is_fk:
                # column_definitions[-1] += " Foreign Key"

                fk_column_name = column_name
                full_datatype = column_definitions[0].split()[1]
                foreign_keys.append({
                    "column_name": fk_column_name,
                    "datatype": full_datatype,
                })



        if not column_definitions:
            self.status_label.config(text="Error: Check of table failed, not valid", fg="red")

        print(column_definitions)

        if primary_keys:
            pk_constraint = f"CONSTRAINT pk_{table_name} PRIMARY KEY ({', '.join(primary_keys)})"
            column_definitions.append(pk_constraint)

        print(column_definitions)

        self.pending_table_name = table_name
        self.pending_column_definitions = column_definitions
        self.pending_foreign_keys = foreign_keys

        sql = f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(f"     {col}" for col in column_definitions)
        sql += "\n)"

        print("\n" + "=" * 50)
        print("Generated SQL:")
        print("=" * 50)
        print(sql)
        print("=" * 50 + "\n")

        if foreign_keys:
            self.Foreign_Key_True()
        else:
            self.execute_sql(sql, table_name)


    def Foreign_Key_True(self):
        self.ForKey = Toplevel(self.confroot)
        self.ForKey.geometry("800x500")

        #self.ForKey_frame = Frame(self.ForKey)
        #self.ForKey_frame.pack()

        """
        self.ForKey_label = Label(self.ForKey_frame,
                                   text="Select a Table with a MATCHING Key",
                                   font=("arial", 12),
                                   fg="black")
        self.ForKey_label.grid(row=0)

        self.table_box_PriKey = Listbox(self.ForKey_frame,
                                        selectmode=SINGLE,
                                        font=("Arial", 10), )
        self.table_box_PriKey.grid(row=1)
        """

        available_pks = self.get_tables_with_pk()

        pprint.pprint(available_pks)

        print(f"Peding forgine keys: {self.pending_foreign_keys}")

        if not available_pks:
            Label(self.ForKey,
                  text="X No tables with Primary Keys found!\nCreate a table with a Primary Key first!",
                  font=("Arial", 12),
                  fg="red").pack(pady=20)

            Button(self.ForKey,
                   text="Cancel",
                   font=("Arial", 12),
                   command=self.ForKey_frame.destroy).pack(pady=10)
            return

        canvas = Canvas(self.ForKey)
        scrollbar = Scrollbar(self.ForKey, orient=VERTICAL, command=canvas.yview)
        scrollbar_frame = Frame(canvas)

        scrollbar_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0,0), window=scrollbar_frame, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=RIGHT, fill=Y)

        header_frame = Frame(scrollbar_frame, relief=RIDGE, borderwidth=2, bg="lightgray")
        header_frame.pack(padx=5, pady=5)

        Label(header_frame,
              text="FK Column",
              font=("Arial", 10, "bold"),
              bg="lightgrey",
              width=15
              ).grid(row=0, column=0, padx=5, pady=5)
        Label(header_frame,
              text="FK Datatype",
              font=("Arial", 10, "bold"),
              bg="lightgrey",
              width=15
              ).grid(row=0, column=1, padx=5, pady=5)
        Label(header_frame,
              text="References Table",
              font=("Arial", 10, "bold"),
              bg="lightgrey",
              width=20
              ).grid(row=0, column=2, padx=5, pady=5)
        Label(header_frame,
              text="References Column",
              font=("Arial", 10, "bold"),
              bg="lightgrey",
              width=25
              ).grid(row=0, column=3, padx=5, pady=5)

        self.fk_references = {}

        for idx, fk in enumerate(self.pending_foreign_keys):
            print(f"idx: {idx}")
            print(f"fk: {fk}")
            print(f"fk Column: {fk['column_name']}")
            row_frame = Frame(scrollbar_frame, relief=GROOVE, borderwidth=1)
            row_frame.pack(fill=X, padx=5, pady=2)

            Label(row_frame,
                  text=fk['column_name'],
                  font=("Arial", 10),
                  width=15
                  ).grid(row=idx, column=0, padx=5, pady=5)

            Label(row_frame,
                  text=fk['datatype'],
                  font=("Arial", 10),
                  width=15,
                  ).grid(row=0, column=1, padx=5, pady=5)

            table_var = StringVar(value="-- Select Table --")
            table_menu = OptionMenu(row_frame, table_var, *[pk["table_name"] for pk in available_pks])
            table_menu.config(width=18)
            table_menu.grid(row=0, column=2, padx=5, pady=5)

            column_var = StringVar(value="-- Select Column --")
            column_menu = OptionMenu(row_frame, column_var, "")
            column_menu.config(width=23)
            column_menu.grid(row=0, column=3, padx=5, pady=5)

            self.fk_references[idx] = {
                "fk_column": fk["column_name"],
                "fk_datatype": fk["datatype"],
                "table_var": table_var,
                "column_var": column_var,
                "column_menu": column_menu,
                "available_pks": available_pks
            }

            table_var.trace("w", lambda *args, i=idx: self.update_fk_columns(i))

        button_frame = Frame(scrollbar_frame)
        button_frame.pack(pady=10)

        Button(button_frame,
               text="Create Table",
               font=("Arial", 12, "bold"),
               bg="green",
               fg="white",
               command=self.validate_and_create_table).pack(side=LEFT, pady=10)

        Button(button_frame,
               text="Cancel Creation",
               font=("Arial", 12, "bold"),
               bg="red",
               fg="white",
               command=self.ForKey.destroy).pack(side=LEFT, pady=10)

    def get_tables_with_pk(self):
        try:
            query = """
                    SELECT 
                        cols.table_name,
                        tab_comments.comments AS table_comment,
                        cols.column_name,
                        cols.data_type,
                        cols.data_length,
                        cols.data_precision,
                        cols.data_scale,
                        'PRIMARY KEY' as constraint_type
                    FROM 
                        user_tab_columns cols
                    INNER JOIN 
                        user_cons_columns cons_cols 
                        ON cols.table_name = cons_cols.table_name 
                        AND cols.column_name = cons_cols.column_name
                    INNER JOIN 
                        user_constraints cons 
                        ON cons_cols.constraint_name = cons.constraint_name 
                        AND cons.constraint_type = 'P'
                    LEFT JOIN
                    user_tab_comments tab_comments
                    ON cols.table_name = tab_comments.table_name
                    WHERE
                        tab_comments.comments = 'GUI_CREATED'
                    ORDER BY 
                        cols.table_name, 
                        cons_cols.position
                    """

            cur.execute(query)

            result = cur.fetchall()

            pprint.pprint(f"Result query: {result}")

            tables = {}
            for table in result:

                table_name = table[0]
                column_name = table[2]
                datatype = table[3]
                data_length = table[4]
                data_precision = table[5]
                data_scale = table[6]
                column_key = table[7]

                if datatype == "NUMBER":
                    if data_precision and data_scale:
                        full_type = f"NUMBER({data_precision},{data_scale})"
                    elif data_precision:
                        full_type = f"NUMBER({data_precision})"
                    else:
                        full_type = "NUMBER"
                elif datatype in ["VARCHAR", "CHAR", "NVARCHAR2", "NCHAR"]:
                    full_type = f"{datatype}({data_precision})"
                else:
                    full_type = datatype

                if table_name not in tables:
                    tables[table_name] = {
                        "table_name": table_name,
                        "pk_colums": []
                    }

                tables[table_name]["pk_colums"].append({
                    "column_name": column_name,
                    "datatype": full_type
                })

                pprint.pprint(f"Content in tables{tables}")
            return list(tables.values())

        except Exception as e:
            print(f"Error fetching tables with PK: {e}")
            return[]

    def update_fk_columns(self, fk_idx):
        ref = self.fk_references[fk_idx]
        selected_table = ref["table_var"].get()

        if selected_table == "-- Select Table --":
            return

        table_info = next(
            (t for t in ref["available_pks"] if t ["table_name"] == selected_table),
            None
        )

        if not table_info:
            return

        menu = ref["column_menu"]["menu"]
        menu.delete(0, "end")

        ref["column_var"].set("-- Select Column --")

        for col in table_info["pk_colums"]:
            display_text = f"{col['column_name']} ({col['datatype']})"
            menu.add_command(
                label=display_text,
                command=lambda val=col: ref["column_var"].set(f"{val["column_name"]} ({val['datatype']})")
            )


    def validate_and_create_table(self):

        for idx, ref in self.fk_references.items():
            table = ref["table_var"].get()
            column_full = ref["column_var"].get()

            if table == "-- Select Table --" or column_full == "-- Select Column --":
                messagebox.showerror(
                    "Missing Selection",
                    f"Please select a reference for FK column '{ref["fk_column"]}'"
                )
                return

            column_name = column_full.split(" (")[0]
            ref_datatype = column_full.split(" (")[1].rstrip(")")

            if ref["fk_datatype"] != ref_datatype:
                messagebox.showerror(
                    "Datatype Mismatch",
                    f"FK column '{ref['fk_column']}' has type {ref['fk_datatype']}\n"
                    f"but references column '{column_name}' with type {ref_datatype}\n\n"
                    f"Datatype must match!"
                )
                return

            fk_constraint = f"CONSTRAINT fk_{self.pending_table_name}_{ref['fk_column']} FOREIGN KEY ({ref['fk_column']}) REFERENCES {table}({column_name})"
            self.pending_column_definitions.append(fk_constraint)

        self.ForKey.destroy()

        self.finalize_and_execute_sql()

    def finalize_and_execute_sql(self):

        sql = f"CREATE TABLE {self.pending_table_name} (\n"
        sql += ",\n".join(f"     {col}" for col in self.pending_column_definitions)
        sql += "\n)"

        print("\n" + "=" * 50)
        print("Generated SQL:")
        print("=" * 50)
        print(sql)
        print("=" * 50 + "\n")

        self.execute_sql(sql, self.pending_table_name)

    def execute_sql(self, sql, table_name):

        try:
            check_sql = """
            SELECT COUNT(*)
            FROM user_tables
            WHERE UPPER(table_name) = UPPER(:table_name)
            """
            cur.execute(check_sql, {'table_name': table_name})
            exists = cur.fetchone()[0]

            if exists > 0:
                self.status_label.config(text=f"Error: Table '{table_name}' already exists!", fg="red")

                print(f"X Table '{table_name}' already exists in database!")
                return
            cur.execute(sql)

            comment_sql = f"COMMENT ON TABLE {table_name} IS 'GUI_CREATED'"
            cur.execute(comment_sql)

            con.commit()

            self.status_label.config(text=f"Table '{table_name}' created!", fg="green")
            print(f"Y Table '{table_name}' created!\n")

        except oracledb.DataError as e:
            error_obj, = e.args
            self.status_label.config(text=f"Error: {error_obj.message[:50]}", fg="red")
            print(f"X Oracle Database Error: {error_obj.message}")

        except Exception as e:
            self.status_label.config(text=f"Error: {str(e)[:50]}...", fg="red")
            print(f"X Error: {e}")


    def go_back(self):
        self.Create_TFrame.forget()
        self.add_frame.forget()
        conf(self.confroot)

# Gleiche Geschichte, bare bones code hab ich selbst gemacht doch bei der verschönerung gab es von claud mehrere verbesserungs punkte 
# weswegen das hier ein gutes stück anders aussieht
class Created_Entry():
    def __init__(self, root_window):
        self.confroot = root_window
        self.entries_list = []  
        self.columns_info = []  
        self.selected_table = None
        
        self.top_frame = Frame(self.confroot)
        self.top_frame.pack(fill=X, padx=10, pady=5)

        self.table_frame = Frame(self.confroot)
        self.table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.bottom_frame = Frame(self.confroot)
        self.bottom_frame.pack(fill=X, padx=10, pady=5)

        self.menu_button = Button(self.top_frame,
                                  text="Go Back",
                                  font=("Arial", 10),
                                  command=self.go_back)
        self.menu_button.grid(row=0, column=0, padx=5)

        Label(self.top_frame,
              text="Select Table:",
              font=("Arial", 12)).grid(row=0, column=1, padx=5)

        self.table_var = StringVar(value="-- Select Table --")
        self.table_names = self._fetch_gui_tables()

        if self.table_names:
            self.table_dropdown = OptionMenu(
                self.top_frame,
                self.table_var,
                *self.table_names,
                command=self._on_table_selected
            )
        else:
            self.table_dropdown = OptionMenu(self.top_frame, self.table_var, "No tables found")

        self.table_dropdown.config(width=25)
        self.table_dropdown.grid(row=0, column=2, padx=5)

        self.status_label = Label(self.top_frame,
                                  text="",
                                  font=("Arial", 10),
                                  fg="red")
        self.status_label.grid(row=0, column=3, padx=10)

        self.add_row_button = Button(self.bottom_frame,
                                     text="+ Add Row",
                                     font=("Arial", 10),
                                     state=DISABLED,
                                     command=self._add_entry_row)
        self.add_row_button.grid(row=0, column=0, padx=5, pady=5)

        self.insert_button = Button(self.bottom_frame,
                                    text="Insert Entries",
                                    font=("Arial", 10, "bold"),
                                    bg="green",
                                    fg="white",
                                    state=DISABLED,
                                    command=self._validate_and_insert)
        self.insert_button.grid(row=0, column=1, padx=5, pady=5)

        self._build_scroll_area()


    def _build_scroll_area(self):
    
        if hasattr(self, "canvas_frame"):
            self.canvas_frame.destroy()

        self.canvas_frame = Frame(self.table_frame)
        self.canvas_frame.pack(fill=BOTH, expand=True)

        self.v_scroll = Scrollbar(self.canvas_frame, orient=VERTICAL)
        self.v_scroll.pack(side=RIGHT, fill=Y)

        self.h_scroll = Scrollbar(self.canvas_frame, orient=HORIZONTAL)
        self.h_scroll.pack(side=BOTTOM, fill=X)

        self.canvas = Canvas(self.canvas_frame,
                             yscrollcommand=self.v_scroll.set,
                             xscrollcommand=self.h_scroll.set)
        self.canvas.pack(side=LEFT, fill=BOTH, expand=True)

        self.v_scroll.config(command=self.canvas.yview)
        self.h_scroll.config(command=self.canvas.xview)

        self.inner_frame = Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner_frame, anchor=NW)

        self.inner_frame.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _fetch_gui_tables(self):
        """Return list of table names created via the GUI."""
        try:
            cur.execute("""
                SELECT table_name
                FROM user_tab_comments
                WHERE comments = 'GUI_CREATED'
                ORDER BY table_name
            """)
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching GUI tables: {e}")
            return []

    def _fetch_columns(self, table_name):
        
        try:
            cur.execute("""
                SELECT
                    column_name,
                    data_type,
                    data_length,
                    data_precision,
                    data_scale,
                    nullable
                FROM user_tab_columns
                WHERE table_name = UPPER(:tn)
                ORDER BY column_id
            """, {"tn": table_name})
            rows = cur.fetchall()

            columns = []
            for r in rows:
                col_name, dtype, d_len, d_prec, d_scale, nullable = r

                if dtype == "NUMBER":
                    if d_prec is not None and d_scale is not None:
                        display_type = f"NUMBER({d_prec},{d_scale})"
                    elif d_prec is not None:
                        display_type = f"NUMBER({d_prec})"
                    else:
                        display_type = "NUMBER"
                elif dtype in ("VARCHAR2", "CHAR", "NVARCHAR2", "NCHAR"):
                    display_type = f"{dtype}({d_len})"
                else:
                    display_type = dtype

                columns.append({
                    "name": col_name,
                    "type": dtype,
                    "display_type": display_type,
                    "length": d_len,
                    "precision": d_prec,
                    "scale": d_scale,
                    "nullable": nullable == "Y",
                })
            return columns
        except Exception as e:
            print(f"Error fetching columns for {table_name}: {e}")
            return []

    def _fetch_pk_columns(self, table_name):
        try:
            cur.execute("""
                SELECT cols.column_name
                FROM user_cons_columns cols
                JOIN user_constraints cons
                  ON cols.constraint_name = cons.constraint_name
                WHERE cons.table_name = UPPER(:tn)
                  AND cons.constraint_type = 'P'
            """, {"tn": table_name})
            return {row[0] for row in cur.fetchall()}
        except Exception:
            return set()

    def _fetch_fk_info(self, table_name):
        
        try:
            cur.execute("""
                SELECT
                    a.column_name,
                    c_pk.table_name  AS ref_table,
                    b.column_name    AS ref_column
                FROM user_cons_columns a
                JOIN user_constraints  c
                  ON a.constraint_name = c.constraint_name
                JOIN user_constraints  c_pk
                  ON c.r_constraint_name = c_pk.constraint_name
                JOIN user_cons_columns b
                  ON c_pk.constraint_name = b.constraint_name
                 AND a.position = b.position
                WHERE c.table_name = UPPER(:tn)
                  AND c.constraint_type = 'R'
            """, {"tn": table_name})
            return {row[0]: (row[1], row[2]) for row in cur.fetchall()}
        except Exception:
            return {}

    
    def _on_table_selected(self, table_name):
        self.selected_table = table_name
        self.entries_list.clear()
        self.status_label.config(text="")

        self.columns_info = self._fetch_columns(table_name)
        self.pk_columns = self._fetch_pk_columns(table_name)
        self.fk_info = self._fetch_fk_info(table_name)

        if not self.columns_info:
            self.status_label.config(text="Could not load columns.", fg="red")
            return

        self._build_scroll_area()
        self._build_header()

        self.add_row_button.config(state=NORMAL)
        self.insert_button.config(state=NORMAL)

        self._add_entry_row()

    def _build_header(self):
        
        Label(self.inner_frame,
              text="#",
              font=("Arial", 9, "bold"),
              relief=RIDGE,
              width=4,
              bg="lightgray").grid(row=0, column=0, padx=1, pady=1, sticky="nsew")

        for col_idx, col in enumerate(self.columns_info):
            is_pk = col["name"] in self.pk_columns
            is_fk = col["name"] in self.fk_info

            badge = ""
            if is_pk:
                badge = " 🔑"
            if is_fk:
                badge = " 🔗"

            header_text = f"{col['name']}{badge}\n{col['display_type']}"
            if not col["nullable"] and not is_pk:
                header_text += "\n*required"

            Label(self.inner_frame,
                  text=header_text,
                  font=("Arial", 9, "bold"),
                  relief=RIDGE,
                  width=20,
                  bg="lightgray",
                  justify=CENTER).grid(row=0, column=col_idx + 1, padx=1, pady=1, sticky="nsew")

        
        Label(self.inner_frame,
              text="Del",
              font=("Arial", 9, "bold"),
              relief=RIDGE,
              width=4,
              bg="lightgray").grid(row=0, column=len(self.columns_info) + 1,
                                   padx=1, pady=1, sticky="nsew")

    
    def _add_entry_row(self):
        """Append a new editable row to inner_frame."""
        row_num = len(self.entries_list) + 1  
        grid_row = row_num  

        row_widgets = {}

        
        Label(self.inner_frame,
              text=str(row_num),
              font=("Arial", 9),
              relief=GROOVE,
              width=4).grid(row=grid_row, column=0, padx=1, pady=1, sticky="nsew")

        for col_idx, col in enumerate(self.columns_info):
            col_name = col["name"]
            is_fk = col_name in self.fk_info

            if is_fk:
                
                fk_var = StringVar(value="-- Select --")
                fk_values = self._fetch_fk_values(*self.fk_info[col_name])
                if not fk_values:
                    fk_values = ["(no data)"]
                opt = OptionMenu(self.inner_frame, fk_var, *fk_values)
                opt.config(width=18)
                opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                row_widgets[col_name] = {"widget": opt, "var": fk_var, "kind": "fk"}
            else:
                entry = Entry(self.inner_frame, width=20)
                entry.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                row_widgets[col_name] = {"widget": entry, "var": None, "kind": "entry"}

        
        del_btn = Button(self.inner_frame,
                         text="✕",
                         font=("Arial", 8),
                         fg="red",
                         width=3,
                         command=lambda r=row_num: self._delete_entry_row(r))
        del_btn.grid(row=grid_row, column=len(self.columns_info) + 1,
                     padx=1, pady=1, sticky="nsew")

        self.entries_list.append({
            "row_num": row_num,
            "grid_row": grid_row,
            "widgets": row_widgets,
            "del_btn": del_btn,
            "row_label": None,  
        })

        
        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _delete_entry_row(self, row_num):
        """Remove an entry row by its display number."""
        idx = next((i for i, r in enumerate(self.entries_list)
                    if r["row_num"] == row_num), None)
        if idx is None:
            return

        row_data = self.entries_list[idx]
        grid_row = row_data["grid_row"]

        
        for widget in self.inner_frame.grid_slaves(row=grid_row):
            widget.destroy()

        self.entries_list.pop(idx)

        
        self._rebuild_rows()

    def _rebuild_rows(self):
        
        for widget in self.inner_frame.winfo_children():
            info = widget.grid_info()
            if info and int(info.get("row", 0)) > 0:
                widget.destroy()

        old_entries = self.entries_list[:]
        self.entries_list.clear()

        for new_idx, old_row in enumerate(old_entries):
            row_num = new_idx + 1
            grid_row = row_num

            Label(self.inner_frame,
                  text=str(row_num),
                  font=("Arial", 9),
                  relief=GROOVE,
                  width=4).grid(row=grid_row, column=0, padx=1, pady=1, sticky="nsew")

            new_widgets = {}
            for col_idx, col in enumerate(self.columns_info):
                col_name = col["name"]
                old_wd = old_row["widgets"][col_name]

                if old_wd["kind"] == "fk":
                    fk_var = StringVar(value=old_wd["var"].get())
                    fk_values = self._fetch_fk_values(*self.fk_info[col_name])
                    if not fk_values:
                        fk_values = ["(no data)"]
                    opt = OptionMenu(self.inner_frame, fk_var, *fk_values)
                    opt.config(width=18)
                    opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    new_widgets[col_name] = {"widget": opt, "var": fk_var, "kind": "fk"}
                else:
                    old_value = old_wd["widget"].get()
                    entry = Entry(self.inner_frame, width=20)
                    entry.insert(0, old_value)
                    entry.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    new_widgets[col_name] = {"widget": entry, "var": None, "kind": "entry"}

            del_btn = Button(self.inner_frame,
                             text="✕",
                             font=("Arial", 8),
                             fg="red",
                             width=3,
                             command=lambda r=row_num: self._delete_entry_row(r))
            del_btn.grid(row=grid_row, column=len(self.columns_info) + 1,
                         padx=1, pady=1, sticky="nsew")

            self.entries_list.append({
                "row_num": row_num,
                "grid_row": grid_row,
                "widgets": new_widgets,
                "del_btn": del_btn,
            })

        self.inner_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    
    def _fetch_fk_values(self, ref_table, ref_column):
        """Return list of string values from the referenced PK column."""
        try:
            cur.execute(f'SELECT "{ref_column}" FROM "{ref_table}" ORDER BY 1')
            return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching FK values from {ref_table}.{ref_column}: {e}")
            return []

    
    def _validate_and_insert(self):
        self.status_label.config(text="", fg="black")

        if not self.entries_list:
            self.status_label.config(text="No rows to insert!", fg="red")
            return

        rows_to_insert = []  

        for row_data in self.entries_list:
            row_values = {}
            valid = True

            for col in self.columns_info:
                col_name = col["name"]
                wd = row_data["widgets"][col_name]

                if wd["kind"] == "fk":
                    raw = wd["var"].get()
                    if raw in ("-- Select --", "(no data)"):
                        self.status_label.config(
                            text=f"Row {row_data['row_num']}: '{col_name}' needs a value.",
                            fg="red")
                        return
                else:
                    raw = wd["widget"].get().strip()

                
                is_pk = col_name in self.pk_columns
                if not col["nullable"] or is_pk:
                    if raw == "":
                        self.status_label.config(
                            text=f"Row {row_data['row_num']}: '{col_name}' is required.",
                            fg="red")
                        return

                
                err = self._validate_value(raw, col, row_data["row_num"])
                if err:
                    self.status_label.config(text=err, fg="red")
                    return

                row_values[col_name] = raw if raw != "" else None

            if valid:
                rows_to_insert.append(row_values)

        
        col_names = [col["name"] for col in self.columns_info]
        placeholders = ", ".join(f":{c}" for c in col_names)
        col_list = ", ".join(col_names)
        sql = f'INSERT INTO "{self.selected_table}" ({col_list}) VALUES ({placeholders})'

        inserted = 0
        try:
            for row_values in rows_to_insert:
                
                bound = {}
                for col in self.columns_info:
                    val = row_values[col["name"]]
                    bound[col["name"]] = self._cast_value(val, col)

                cur.execute(sql, bound)
                inserted += 1

            con.commit()
            self.status_label.config(
                text=f"✓ {inserted} row(s) inserted into '{self.selected_table}'!",
                fg="green")
            print(f"Inserted {inserted} row(s) into {self.selected_table}")

            
            self._on_table_selected(self.selected_table)

        except oracledb.IntegrityError as e:
            con.rollback()
            err_obj, = e.args
            self.status_label.config(
                text=f"Integrity error: {err_obj.message[:60]}",
                fg="red")
            print(f"Integrity error: {err_obj.message}")

        except oracledb.DataError as e:
            con.rollback()
            err_obj, = e.args
            self.status_label.config(
                text=f"Data error: {err_obj.message[:60]}",
                fg="red")
            print(f"Data error: {err_obj.message}")

        except Exception as e:
            con.rollback()
            self.status_label.config(text=f"Error: {str(e)[:60]}", fg="red")
            print(f"Insert error: {e}")

    def _validate_value(self, raw, col, row_num):
        """Return error string or None if value is acceptable."""
        if raw == "" or raw is None:
            return None  

        dtype = col["type"]

        if dtype == "NUMBER":
            try:
                float(raw)
            except ValueError:
                return f"Row {row_num}: '{col['name']}' must be a number."

            if col["precision"] is not None:
                
                parts = raw.replace("-", "").split(".")
                int_digits = len(parts[0].lstrip("0") or "0")
                dec_digits = len(parts[1]) if len(parts) > 1 else 0
                scale = col["scale"] if col["scale"] is not None else 0
                prec = col["precision"]
                if int_digits > (prec - scale) or dec_digits > scale:
                    return (f"Row {row_num}: '{col['name']}' exceeds "
                            f"NUMBER({prec},{scale}) range.")

        elif dtype in ("VARCHAR2", "NVARCHAR2"):
            if col["length"] and len(raw.encode("utf-8")) > col["length"]:
                return (f"Row {row_num}: '{col['name']}' exceeds "
                        f"max length {col['length']}.")

        elif dtype in ("CHAR", "NCHAR"):
            if col["length"] and len(raw) > col["length"]:
                return (f"Row {row_num}: '{col['name']}' exceeds "
                        f"max length {col['length']}.")

        elif dtype == "DATE":
            import datetime
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    datetime.datetime.strptime(raw, fmt)
                    return None
                except ValueError:
                    continue
            return (f"Row {row_num}: '{col['name']}' invalid date. "
                    "Use YYYY-MM-DD, DD.MM.YYYY, or DD/MM/YYYY.")

        elif dtype == "TIMESTAMP":
            import datetime
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    datetime.datetime.strptime(raw, fmt)
                    return None
                except ValueError:
                    continue
            return (f"Row {row_num}: '{col['name']}' invalid timestamp. "
                    "Use YYYY-MM-DD HH:MM:SS.")

        return None

    def _cast_value(self, val, col):
        """Convert a string value to the right Python type for cx_Oracle binding."""
        if val is None or val == "":
            return None

        import datetime
        dtype = col["type"]

        if dtype == "NUMBER":
            try:
                if "." in str(val):
                    return float(val)
                return int(val)
            except (ValueError, TypeError):
                return val

        elif dtype == "DATE":
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    return datetime.datetime.strptime(val, fmt)
                except ValueError:
                    continue
            return val

        elif dtype == "TIMESTAMP":
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return datetime.datetime.strptime(val, fmt)
                except ValueError:
                    continue
            return val

        return val  

    def go_back(self):
        self.top_frame.forget()
        self.table_frame.forget()
        self.bottom_frame.forget()
        conf(self.confroot)

class Edit_Table():
    def __init__(self, root_window):
        self.confroot = root_window
        self.selected_table = None
        self.rows_data = []
        self.existing_columns_info = []
        self.pk_columns = []
        self.fk_info = {}
        self.dropdown_datatypes = [
            "NUMBER",
            "NUMBER(p,s)",
            "VARCHAR2(n)",
            "CHAR(n)",
            "CLOB",
            "DATE",
            "TIMESTAMP",
        ]

        self.edit_frame = Frame(self.confroot, bg="#F8F7F4")
        self.edit_frame.pack(fill=BOTH, expand=True, padx=20, pady=20)

        top_frame = Frame(self.edit_frame, bg="#F8F7F4")
        top_frame.pack(fill=X, pady=(0, 16))

        Button(top_frame,
               text="Go Back",
               font=("Arial", 10),
               bg="#E8E7E1",
               fg="#444441",
               relief=FLAT,
               command=self.go_back).pack(side=LEFT)

        Label(top_frame,
              text="Edit a table",
              font=("Arial", 16, "bold"),
              bg="#F8F7F4",
              fg="#1A1A18").pack(side=LEFT, padx=12)

        self.table_var = StringVar(value="-- Select Table --")
        self.table_menu = OptionMenu(top_frame,
                                     self.table_var,
                                     *self._fetch_gui_tables(),
                                     command=self._on_table_selected)
        self.table_menu.config(width=24)
        self.table_menu.pack(side=RIGHT)

        frame = Frame(self.edit_frame, bg="#F8F7F4")
        frame.pack(fill=BOTH, expand=True)

        self.table_grid = Frame(frame, bg="#F8F7F4")
        self.table_grid.pack(fill=BOTH, expand=True)

        self._build_header_row()

        bottom_frame = Frame(self.edit_frame, bg="#F8F7F4")
        bottom_frame.pack(fill=X, pady=(16, 0))

        Button(bottom_frame,
               text="Add Column",
               font=("Arial", 10),
               bg="#1D9E75",
               fg="#FFFFFF",
               relief=FLAT,
               padx=12,
               pady=6,
               cursor="hand2",
               command=self.create_row).pack(side=LEFT)

        Button(bottom_frame,
               text="Save Changes",
               font=("Arial", 10, "bold"),
               bg="#185FA5",
               fg="#FFFFFF",
               relief=FLAT,
               padx=12,
               pady=6,
               cursor="hand2",
               command=self.save_changes).pack(side=LEFT, padx=(8, 0))

        self.status_label = Label(bottom_frame,
                                  text="",
                                  font=("Arial", 10),
                                  bg="#F8F7F4",
                                  fg="red")
        self.status_label.pack(side=LEFT, padx=(12, 0))

    def _fetch_gui_tables(self):
        try:
            cur.execute("SELECT table_name FROM user_tab_comments WHERE comments = 'GUI_CREATED' ORDER BY table_name")
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching GUI_CREATED tables: {e}")
            return []

    def _on_table_selected(self, table_name):
        if not table_name or table_name == "-- Select Table --":
            return

        self.selected_table = table_name
        self.table_var.set(table_name)
        self.rows_data = []
        self._load_table_schema(table_name)
        self._render_rows()

    def _load_table_schema(self, table_name):
        self.existing_columns_info = self._fetch_table_columns(table_name)
        self.pk_columns = self._fetch_primary_keys(table_name)
        self.fk_info = self._fetch_foreign_keys(table_name)

        for col in self.existing_columns_info:
            col_name = col["name"]
            datatype, params = self._normalize_datatype(col)
            is_pk = col_name in self.pk_columns
            fk_data = self.fk_info.get(col_name, {})
            self.rows_data.append({
                "original_name": col_name,
                "name_var": StringVar(value=col_name),
                "datatype_var": StringVar(value=datatype),
                "params_var": StringVar(value=params),
                "pk_var": IntVar(value=1 if is_pk else 0),
                "fk_var": StringVar(value=fk_data.get("ref_table", "-- None --")),
                "is_existing": True,
                "original_fk_table": fk_data.get("ref_table"),
                "widgets": []
            })
        
    def _fetch_table_columns(self, table_name):
        try:
            query = """
                SELECT column_name, data_type, data_length, data_precision, data_scale, nullable
                FROM user_tab_columns
                WHERE table_name = :table_name
                ORDER BY column_id
            """
            cur.execute(query, {"table_name": table_name})
            rows = cur.fetchall()
            columns = []
            for column_name, data_type, data_length, data_precision, data_scale, nullable in rows:
                columns.append({
                    "name": column_name,
                    "data_type": data_type,
                    "data_length": data_length,
                    "data_precision": data_precision,
                    "data_scale": data_scale,
                    "nullable": nullable == "Y"
                })
            return columns
        except Exception as e:
            print(f"Error loading columns for {table_name}: {e}")
            return []

    def _fetch_primary_keys(self, table_name):
        try:
            query = """
                SELECT acc.column_name
                FROM user_constraints ac
                JOIN user_cons_columns acc ON ac.constraint_name = acc.constraint_name
                WHERE ac.table_name = :table_name AND ac.constraint_type = 'P'
                ORDER BY acc.position
            """
            cur.execute(query, {"table_name": table_name})
            return [row[0] for row in cur.fetchall()]
        except Exception as e:
            print(f"Error loading PKs for {table_name}: {e}")
            return []

    def _fetch_foreign_keys(self, table_name):
        try:
            query = """
                SELECT acc.column_name,
                       ref.table_name AS ref_table,
                       refcol.column_name AS ref_column,
                       ac.constraint_name
                FROM user_constraints ac
                JOIN user_cons_columns acc ON ac.constraint_name = acc.constraint_name
                JOIN user_constraints ref ON ac.r_constraint_name = ref.constraint_name
                JOIN user_cons_columns refcol ON ref.constraint_name = refcol.constraint_name AND refcol.position = acc.position
                WHERE ac.table_name = :table_name AND ac.constraint_type = 'R'
            """
            cur.execute(query, {"table_name": table_name})
            result = {}
            for column_name, ref_table, ref_column, constraint_name in cur.fetchall():
                result[column_name] = {
                    "ref_table": ref_table,
                    "ref_column": ref_column,
                    "constraint_name": constraint_name
                }
            return result
        except Exception as e:
            print(f"Error loading FKs for {table_name}: {e}")
            return {}

    def _normalize_datatype(self, column):
        data_type = column["data_type"]
        precision = column["data_precision"]
        scale = column["data_scale"]
        length = column["data_length"]

        if data_type == "NUMBER":
            if precision is not None and scale is not None:
                return "NUMBER(p,s)", f"{precision},{scale}"
            return "NUMBER", ""

        if data_type in ("VARCHAR2", "NVARCHAR2"):
            return "VARCHAR2(n)", str(length or "")

        if data_type in ("CHAR", "NCHAR"):
            return "CHAR(n)", str(length or "")

        return data_type, ""

    def _build_header_row(self):
        headers = ["Column Name", "Datatype", "Parameters", "Primary Key", "Foreign Key", ""]
        for idx, label_text in enumerate(headers):
            Label(self.table_grid,
                  text=label_text,
                  font=("Arial", 10, "bold"),
                  bg="#F8F7F4").grid(row=0, column=idx, padx=4, pady=8)

    def _clear_rows(self):
        for widget in self.table_grid.winfo_children():
            info = widget.grid_info()
            if info and info.get("row", 0) > 0:
                widget.destroy()

    def _render_rows(self):
        self._clear_rows()
        self._build_header_row()
        fk_table_options = ["-- None --"] + [table["table_name"] for table in self._get_tables_with_pk_details()]

        for idx, row_data in enumerate(self.rows_data, start=1):
            name_entry = Entry(self.table_grid,
                               font=("Arial", 10),
                               textvariable=row_data["name_var"])
            name_entry.grid(row=idx, column=0, padx=4, pady=4, sticky="ew")

            datatype_menu = OptionMenu(self.table_grid,
                                       row_data["datatype_var"],
                                       *self.dropdown_datatypes,
                                       command=lambda value, row=row_data: self._on_datatype_changed(row, value))
            datatype_menu.config(width=16)
            datatype_menu.grid(row=idx, column=1, padx=4, pady=4)

            params_entry = Entry(self.table_grid,
                                 font=("Arial", 10),
                                 textvariable=row_data["params_var"])
            params_entry.grid(row=idx, column=2, padx=4, pady=4, sticky="ew")

            pk_checkbox = Checkbutton(self.table_grid,
                                      variable=row_data["pk_var"],
                                      bg="#F8F7F4")
            pk_checkbox.grid(row=idx, column=3, padx=4, pady=4)

            fk_var = row_data["fk_var"]
            fk_menu = OptionMenu(self.table_grid,
                                 fk_var,
                                 *fk_table_options)
            fk_menu.config(width=20)
            fk_menu.grid(row=idx, column=4, padx=4, pady=4)

            delete_button = Button(self.table_grid,
                                   text="X",
                                   font=("Arial", 9),
                                   bg="#E8E7E1",
                                   fg="#444441",
                                   relief=FLAT,
                                   command=lambda row=row_data: self.delete_row(row))
            delete_button.grid(row=idx, column=5, padx=4, pady=4)

            row_data["widgets"] = [name_entry, datatype_menu, params_entry, pk_checkbox, fk_menu, delete_button]
            self._on_datatype_changed(row_data, row_data["datatype_var"].get())

    def _on_datatype_changed(self, row_data, datatype_value):
        params_widget = row_data["widgets"][2] if len(row_data.get("widgets", [])) >= 3 else None
        if datatype_value in ["NUMBER(p,s)", "VARCHAR2(n)", "CHAR(n)"]:
            if params_widget:
                params_widget.config(state=NORMAL)
        else:
            if params_widget:
                params_widget.delete(0, END)
                params_widget.config(state=DISABLED)

    def create_row(self):
        self.rows_data.append({
            "original_name": "",
            "name_var": StringVar(value=""),
            "datatype_var": StringVar(value="NUMBER"),
            "params_var": StringVar(value=""),
            "pk_var": IntVar(value=0),
            "fk_var": StringVar(value="-- None --"),
            "is_existing": False,
            "original_fk_table": None,
            "widgets": []
        })
        self._render_rows()

    def delete_row(self, row_data):
        if row_data in self.rows_data:
            self.rows_data.remove(row_data)
            self._render_rows()

    def save_changes(self):
        if not self.selected_table:
            self.status_label.config(text="Please select a table first.", fg="red")
            return

        rows = []
        for row in self.rows_data:
            name = row["name_var"].get().strip()
            if not name:
                continue
            datatype = row["datatype_var"].get()
            params = row["params_var"].get().strip()
            is_pk = bool(row["pk_var"].get())
            fk_table = row["fk_var"].get()
            if fk_table == "-- None --":
                fk_table = None

            if datatype in ["NUMBER(p,s)", "VARCHAR2(n)", "CHAR(n)"] and not params:
                self.status_label.config(text=f"{datatype} requires parameters.", fg="red")
                return

            rows.append({
                "original_name": row["original_name"],
                "name": name,
                "datatype": datatype,
                "params": params,
                "is_pk": is_pk,
                "fk_table": fk_table,
                "is_existing": row["is_existing"],
                "original_fk_table": row.get("original_fk_table")
            })

        names = [row["name"] for row in rows]
        if len(names) != len(set(names)):
            self.status_label.config(text="Duplicate column names are not allowed.", fg="red")
            return

        existing_names = [col["name"] for col in self.existing_columns_info]
        added_columns = [row for row in rows if row["name"] not in existing_names]
        removed_columns = [name for name in existing_names if name not in names]
        modified_rows = [row for row in rows if row["name"] in existing_names]
        
        statements = []
        fk_changes = []
        pk_new = [row["name"] for row in rows if row["is_pk"]]
        pk_old = set(self.pk_columns)

        for row in modified_rows:
            original = row["original_name"] or row["name"]
            column_info = next((col for col in self.existing_columns_info if col["name"] == original), None)
            if not column_info:
                continue

            current_type, current_params = self._normalize_datatype(column_info)
            target_type = row["datatype"]
            target_params = row["params"]
            full_current = self._format_datatype(current_type, current_params)
            full_target = self._format_datatype(target_type, target_params)

            if row["name"] != original:
                statements.append(f'ALTER TABLE "{self.selected_table}" RENAME COLUMN "{original}" TO "{row["name"]}"')

            if full_current != full_target:
                statements.append(f'ALTER TABLE "{self.selected_table}" MODIFY ("{row["name"]}" {full_target})')

            original_fk = row["original_fk_table"]
            if original_fk and row["fk_table"] != original_fk:
                fk_changes.append({
                    "column": row["name"],
                    "old_fk_table": original_fk,
                    "new_fk_table": row["fk_table"],
                    "original_constraint": self.fk_info.get(original, {}).get("constraint_name")
                })
            elif not original_fk and row["fk_table"]:
                fk_changes.append({
                    "column": row["name"],
                    "old_fk_table": None,
                    "new_fk_table": row["fk_table"],
                    "original_constraint": None
                })
            elif original_fk and not row["fk_table"]:
                fk_changes.append({
                    "column": row["name"],
                    "old_fk_table": original_fk,
                    "new_fk_table": None,
                    "original_constraint": self.fk_info.get(original, {}).get("constraint_name")
                })

        for row in added_columns:
            full_type = self._format_datatype(row["datatype"], row["params"])
            statements.append(f'ALTER TABLE "{self.selected_table}" ADD ("{row["name"]}" {full_type})')
            if row["fk_table"]:
                fk_changes.append({
                    "column": row["name"],
                    "old_fk_table": None,
                    "new_fk_table": row["fk_table"],
                    "original_constraint": None
                })

        for col_name in removed_columns:
            statements.append(f'ALTER TABLE "{self.selected_table}" DROP COLUMN "{col_name}" CASCADE CONSTRAINTS')

        if pk_old != set(pk_new):
            if pk_old:
                statements.append(f'ALTER TABLE "{self.selected_table}" DROP PRIMARY KEY')
            if pk_new:
                pk_name = f"pk_{self.selected_table}"
                columns_csv = ", ".join(f'"{col}"' for col in pk_new)
                statements.append(f'ALTER TABLE "{self.selected_table}" ADD CONSTRAINT "{pk_name}" PRIMARY KEY ({columns_csv})')

        if fk_changes:
            self.pending_fk_changes = fk_changes
            self.pending_statements = statements
            self._prompt_fk_references(rows)
            return

        self._execute_update_statements(statements, [])

    def _prompt_fk_references(self, rows):
        available_pks = self._get_tables_with_pk_details()
        if not available_pks:
            self.status_label.config(text="No tables with primary keys available for foreign key references.", fg="red")
            return

        self.fk_picker = Toplevel(self.confroot)
        self.fk_picker.title("Foreign Key References")
        self.fk_picker.geometry("760x440")
        self.fk_picker.configure(bg="#F8F7F4")
        self.fk_picker.grab_set()

        Label(self.fk_picker,
              text="Select reference columns for foreign key changes",
              font=("Arial", 13, "bold"),
              bg="#F8F7F4",
              fg="#1A1A18").pack(pady=(18, 10))

        Label(self.fk_picker,
              text="Pick the referenced table and primary key column for each foreign key.",
              font=("Arial", 10),
              bg="#F8F7F4",
              fg="#888780").pack(pady=(0, 12))

        canvas = Canvas(self.fk_picker, bg="#F8F7F4", highlightthickness=0)
        scrollbar = Scrollbar(self.fk_picker, orient=VERTICAL, command=canvas.yview)
        content = Frame(canvas, bg="#F8F7F4")
        content.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=content, anchor=NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=LEFT, fill=BOTH, expand=True, padx=(12, 0), pady=12)
        scrollbar.pack(side=RIGHT, fill=Y, pady=12)

        header = Frame(content, bg="#F8F7F4")
        header.pack(fill=X, pady=(0, 6))
        for idx, title in enumerate(["Column", "Datatype", "Ref Table", "Ref PK Column"]):
            Label(header,
                  text=title,
                  font=("Arial", 10, "bold"),
                  bg="#F8F7F4").grid(row=0, column=idx, padx=8, pady=6)

        self.fk_reference_widgets = []
        fk_tables_map = {t["table_name"]: t for t in available_pks}

        for fk in self.pending_fk_changes:
            row_frame = Frame(content, bg="#F8F7F4")
            row_frame.pack(fill=X, pady=4)

            Label(row_frame,
                  text=fk["column"],
                  font=("Arial", 10),
                  bg="#F8F7F4").grid(row=0, column=0, padx=8, pady=4)

            datatype = next((r["datatype"] for r in rows if r["name"] == fk["column"]), "")
            Label(row_frame,
                  text=datatype,
                  font=("Arial", 10),
                  bg="#F8F7F4").grid(row=0, column=1, padx=8, pady=4)

            table_var = StringVar(value=fk["new_fk_table"] or "-- Select Table --")
            table_menu = OptionMenu(row_frame,
                                     table_var,
                                     *[t["table_name"] for t in available_pks])
            table_menu.config(width=18)
            table_menu.grid(row=0, column=2, padx=8, pady=4)

            column_var = StringVar(value="-- Select Column --")
            column_menu = OptionMenu(row_frame, column_var, "-- Select Column --")
            column_menu.config(width=26)
            column_menu.grid(row=0, column=3, padx=8, pady=4)

            widget_info = {
                "column": fk["column"],
                "datatype": datatype,
                "table_var": table_var,
                "column_var": column_var,
                "column_menu": column_menu,
                "available_pks": available_pks
            }
            self.fk_reference_widgets.append(widget_info)
            table_var.trace("w", lambda *args, widget=widget_info: self._update_fk_columns(widget))

            if fk["new_fk_table"] and fk["new_fk_table"] in fk_tables_map:
                self._update_fk_columns(widget_info)
                column_var.set(fk_tables_map[fk["new_fk_table"]]["pk_colums"][0]["column_name"])

        button_frame = Frame(self.fk_picker, bg="#F8F7F4")
        button_frame.pack(pady=(0, 14))

        Button(button_frame,
               text="Apply FK Changes",
               font=("Arial", 11, "bold"),
               bg="#1D9E75",
               fg="#FFFFFF",
               relief=FLAT,
               padx=12,
               pady=8,
               command=self._apply_fk_updates).pack(side=LEFT, padx=8)

        Button(button_frame,
               text="Cancel",
               font=("Arial", 11),
               bg="#E8E7E1",
               fg="#444441",
               relief=FLAT,
               padx=12,
               pady=8,
               command=self.fk_picker.destroy).pack(side=LEFT, padx=8)

    def _get_tables_with_pk_details(self):
        try:
            query = """
                SELECT cols.table_name,
                       cols.column_name,
                       cols.data_type,
                       cols.data_length,
                       cols.data_precision,
                       cols.data_scale
                FROM user_tab_columns cols
                JOIN user_cons_columns cons_cols
                  ON cols.table_name = cons_cols.table_name
                 AND cols.column_name = cons_cols.column_name
                JOIN user_constraints cons
                  ON cons_cols.constraint_name = cons.constraint_name
                 AND cons.constraint_type = 'P'
                JOIN user_tab_comments tab_comments
                  ON cols.table_name = tab_comments.table_name
                WHERE tab_comments.comments = 'GUI_CREATED'
                ORDER BY cols.table_name, cons_cols.position
            """
            cur.execute(query)
            rows = cur.fetchall()
            tables = {}
            for table_name, column_name, data_type, data_length, data_precision, data_scale in rows:
                if table_name not in tables:
                    tables[table_name] = {
                        "table_name": table_name,
                        "pk_colums": []
                    }
                tables[table_name]["pk_colums"].append({
                    "column_name": column_name,
                    "datatype": self._format_datatype(*self._normalize_datatype({
                        "data_type": data_type,
                        "data_precision": data_precision,
                        "data_scale": data_scale,
                        "data_length": data_length
                    }))
                })
            return list(tables.values())
        except Exception as e:
            print(f"Error fetching tables with PK details: {e}")
            return []

    def _update_fk_columns(self, widget):
        selected_table = widget["table_var"].get()
        if not selected_table or selected_table == "-- Select Table --":
            return

        info = next((t for t in widget["available_pks"] if t["table_name"] == selected_table), None)
        if not info:
            return

        menu = widget["column_menu"]["menu"]
        menu.delete(0, "end")
        widget["column_var"].set("-- Select Column --")
        for col in info["pk_colums"]:
            menu.add_command(label=col["column_name"], command=lambda value=col["column_name"]: widget["column_var"].set(value))

    def _apply_fk_updates(self):
        fk_statements = []
        details = self._get_tables_with_pk_details()
        pk_map = {t["table_name"]: t for t in details}

        for widget in self.fk_reference_widgets:
            source_column = widget["column"]
            ref_table = widget["table_var"].get()
            ref_column = widget["column_var"].get()
            if not ref_table or ref_table == "-- Select Table --":
                self.status_label.config(text=f"Reference table missing for {source_column}.", fg="red")
                return
            if not ref_column or ref_column == "-- Select Column --":
                self.status_label.config(text=f"Reference column missing for {source_column}.", fg="red")
                return

            if ref_table not in pk_map:
                self.status_label.config(text=f"Table {ref_table} has no primary key.", fg="red")
                return

            fk_name = f"fk_{self.selected_table}_{source_column}"
            fk_statements.append(
                f'ALTER TABLE "{self.selected_table}" ADD CONSTRAINT "{fk_name}" FOREIGN KEY ("{source_column}") REFERENCES "{ref_table}" ("{ref_column}")'
            )

        self.fk_picker.destroy()
        self._execute_update_statements(self.pending_statements, fk_statements)

    def _format_datatype(self, datatype, params):
        if datatype == "NUMBER(p,s)":
            return f"NUMBER({params})"
        if datatype in ["VARCHAR2(n)", "CHAR(n)"]:
            return datatype.replace("(n)", f"({params})")
        return datatype

    def _execute_update_statements(self, statements, fk_statements):
        if not statements and not fk_statements:
            self.status_label.config(text="No changes detected.", fg="orange")
            return

        try:
            for statement in statements:
                cur.execute(statement)
            for statement in fk_statements:
                cur.execute(statement)
            con.commit()
            self.status_label.config(text=f"Table '{self.selected_table}' updated successfully.", fg="green")
            self._on_table_selected(self.selected_table)
        except Exception as e:
            con.rollback()
            self.status_label.config(text=f"Update failed: {str(e)[:80]}", fg="red")
            print(f"Update failed: {e}")

    def go_back(self):
        self.edit_frame.forget()
        conf(self.confroot)

class Edit_Entry():
    def __init__(self, root_window):
        pass
# Die Classe werde ich so lassen damit man es sehen kann wie mein design ausehen würde
# Werde es trozdem denke ich in einer anderen branch schöner machen, Gibt natürlich in jeder classe bugs die durch die Programmirung
# und durch fehlende checks passieren können aber solange sie nicht stark die funktion des programms beinträchtigen werde ich diese leider
# dabei behalten durch zeit probleme
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
        self.table_name = cur.fetchall()

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
        for name in self.table_box.curselection():
            name = self.table_box.get(name)

            n = name[0]

            sql = f"DROP TABLE {n}"
            cur.execute(sql)

            self.status_label.config(text=f"Table '{n}' has been dropped!", fg="green")

            self.update(n)

    def update(self, n):

        self.table_box.delete(0, END)

        cur.execute("SELECT table_name FROM user_tab_comments WHERE comments = 'GUI_CREATED'")
        self.table_name = cur.fetchall()

        for entry in self.table_name:
            self.table_box.insert(END, entry[0])


    def go_back(self):
        self.delete_frame.forget()
        conf(self.confroot)

if __name__ == "__main__":
    cur.execute("""SELECT
    c.table_name,
    tc.comments AS table_comment,
    c.column_name,
    c.data_type,
    c.data_length,
    c.data_precision,
    c.data_scale,

    CASE WHEN pk.column_name IS NOT NULL THEN 'PRIMARY KEY' END AS pk_flag,
    CASE WHEN fk.column_name IS NOT NULL THEN 'FOREIGN KEY' END AS fk_flag

FROM user_tab_columns c

LEFT JOIN user_tab_comments tc
    ON c.table_name = tc.table_name

LEFT JOIN (
    SELECT acc.table_name, acc.column_name
    FROM user_constraints ac
    JOIN user_cons_columns acc
        ON ac.constraint_name = acc.constraint_name
    WHERE ac.constraint_type = 'P'
) pk
ON c.table_name = pk.table_name
AND c.column_name = pk.column_name

LEFT JOIN (
    SELECT acc.table_name, acc.column_name
    FROM user_constraints ac
    JOIN user_cons_columns acc
        ON ac.constraint_name = acc.constraint_name
    WHERE ac.constraint_type = 'R'
) fk
ON c.table_name = fk.table_name
AND c.column_name = fk.column_name

WHERE tc.comments = 'GUI_CREATED'
ORDER BY c.table_name, c.column_id""")
    pprint.pprint(cur.fetchall())
    root_window = Tk()
    app = conf(root_window)
    root_window.mainloop()