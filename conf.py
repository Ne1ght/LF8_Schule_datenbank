from importlib import metadata
import sys
from tkinter import *
from tkinter import messagebox
from sqlalchemy import Date, Integer, String, create_engine, MetaData, inspect
from eralchemy import render_er
import yaerrrr
import subprocess
import os
import queue
import threading
import tempfile
import pprint
import traceback
from db import con, cur
from Create_Table import Created_Table
from Created_Entry import Created_Entry
from Edit_Table import Edit_Table
from Edit_Entry import Edit_Entry
from Delete_Table import Delete_Table
from Delete_Entry import Delete_Entry


class TerminalWidget:
    """Embedded terminal widget with output display and command input."""
    def __init__(self, parent):
        self.frame = Frame(parent, bg="#1e1e1e")

        # ── output area ────────────────────────────────
        self.output = Text(
            self.frame,
            bg="#1e1e1e", fg="#d4d4d4",
            font=("Consolas", 10),
            insertbackground="white",
            relief=FLAT, bd=0,
            state=DISABLED, 
            height=10          # read-only; user types in entry below
        )
        sb = Scrollbar(self.frame, command=self.output.yview)
        self.output.config(yscrollcommand=sb.set)
        sb.pack(side=RIGHT, fill=Y)
        self.output.pack(fill=BOTH, expand=True)

        # ── input row ──────────────────────────────────
        input_frame = Frame(self.frame, bg="#252526")
        input_frame.pack(fill=X)
        Label(input_frame, text="$ ",
              bg="#252526", fg="#1d9e75",
              font=("Consolas", 10)).pack(side=LEFT, padx=(8, 0))
        self.entry = Text(input_frame,
            bg="#252526", fg="#d4d4d4",
            font=("Consolas", 10),
            insertbackground="white",
            height=4, wrap="none")
        self.entry.pack(fill=BOTH, expand=True, padx=(4, 8), pady=6)
        self.entry.bind("<Control-Return>", self.run_command)
        self.entry.bind("<Up>",    self.history_up)
        self.entry.bind("<Down>",  self.history_down)

        self._history, self._hist_idx = [], -1
        self._queue = queue.Queue()
        self.frame.after(50, self._poll_queue)   # drain output on main thread

    # ── public: embed anywhere ──────────────────────
    def pack(self, **kw):
        self.frame.pack(**kw)

    def grid(self, **kw):
        self.frame.grid(**kw)

    def write(self, text, tag=None):
        self.output.config(state=NORMAL)
        self.output.insert(END, text, tag or ())
        self.output.see(END)
        self.output.config(state=DISABLED)

    def run_command(self, event=None):
        cmd = self.entry.get("1.0", END).strip()
        if not cmd:
            return
        self._history.insert(0, cmd)
        self._hist_idx = -1
        self.entry.delete("1.0", END)
        self.write(f"$ {cmd}\n")
        # Route SQL directly through the DB connection
        if cmd.upper().startswith(("SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "ALTER", "SHOW")):
            threading.Thread(target=self._exec_sql, args=(cmd,), daemon=True).start()
        else:
            threading.Thread(target=self._exec, args=(cmd,), daemon=True).start()

    def _exec_sql(self, cmd):
        try:
            from db import cur, con
            cur.execute(cmd)
            if cmd.strip().upper().startswith("SELECT"):
                cols = [d[0] for d in cur.description]
                rows = cur.fetchall()

                MAX_COL_WIDTH = 30

                widths = [min(len(col), MAX_COL_WIDTH) for col in cols]
                for row in rows:
                    for i, val in enumerate(row):
                        widths[i] = min(max(widths[i], len(str(val) if val is not None else "NULL")), MAX_COL_WIDTH)

                header  = "  ".join(col.ljust(widths[i])  for i, col in enumerate(cols))
                divider = "  ".join("─" * widths[i]       for i in range(len(cols)))
                self._queue.put(header  + "\n")
                self._queue.put(divider + "\n")

                for row in rows:
                    line = "  ".join(
                        (str(v).strip() if v is not None else "NULL").ljust(widths[i])
                        for i, v in enumerate(row)
                    )
                    self._queue.put(line + "\n")
            else:
                con.commit()
                self._queue.put(f"OK — {cur.rowcount} row(s) affected\n")
            self._queue.put("\n[done]\n")
        except Exception as e:
            self._queue.put(f"SQL Error: {e}\n")

    def _exec(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd, shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, bufsize=1,
            )
            for line in proc.stdout:
                self._queue.put(line)
            proc.wait()
            self._queue.put(f"\n[exited {proc.returncode}]\n")
        except Exception as e:
            self._queue.put(f"Error: {e}\n")

    def _poll_queue(self):
        while not self._queue.empty():
            self.write(self._queue.get_nowait())
        self.frame.after(50, self._poll_queue)

    def history_up(self, e):
        if self._history:
            self._hist_idx = min(self._hist_idx + 1, len(self._history) - 1)
            self.entry.delete(0, END)
            self.entry.insert(0, self._history[self._hist_idx])

    def history_down(self, e):
        self._hist_idx = max(self._hist_idx - 1, -1)
        self.entry.delete(0, END)
        if self._hist_idx >= 0:
            self.entry.insert(0, self._history[self._hist_idx])


class conf():
    def __init__(self, root_window):
        self.confroot = root_window
        self.confroot.title("DB Manager")
        self.confroot.geometry("680x700")
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
        
        Button(header_frame,
               text=" ⇄ ",
               font=("Arial", 18),
               bg="#F8F7F4",
               fg="#1A1A18",
               activebackground="#F7F6F2",
               activeforeground="#1A1A18",
               relief=FLAT,
               bd=0,
               ).pack(side=LEFT)

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
            ("Query", "Create Diagrams", "#FAEEDA", "#854F0B", "#633806", "Query"),
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

        # ── Terminal widget below debug tools ────────────────────────
        Frame(self.conf_frame, height=1, bg="#D3D1C7").pack(fill=X, pady=(14, 10))

        Label(self.conf_frame,
             text="Terminal",
             font=("Arial", 10),
             bg="#F8F7F4",
             fg="#888780").pack(anchor=W, pady=(0, 8))

        self.terminal = TerminalWidget(self.conf_frame)
        self.terminal.frame.config(height=200)
        self.terminal.pack(fill=BOTH, expand=True, pady=(0, 0))
        self.terminal.write("Terminal ready.\n")

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

        self.Query_DB()
        
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

                print(row)

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

                    print(display)

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
        #if operation_type == "Query":
        #    self.open_entry_viewer()
        #    return

        if operation_type == "Created":
            verb, adj = "Create", "new"
        elif operation_type == "Edit":
            verb, adj = "Edit", "existing"
        elif operation_type == "Delete":
            verb, adj = "Delete", "existing"
        else:
            verb, adj = "Query Rational", "Query Chen"

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

        if operation_type != "Query":

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
        
        else:
            Button(btn_row,
                   text=f"Show Rational Diagram  ",
                   font=("Arial", 11),
                   bg="#A59018",
                   fg="#FFFFFF",
                   activebackground="#6B7C0C",
                   activeforeground="#FFFFFF",
                   relief=FLAT,
                   padx=14,
                   pady=8,
                   cursor="hand2",
                   command=lambda: (dialog.destroy(),
                                    self.draw_er_diagram())).pack(side=LEFT, padx=8)
            
            Button(btn_row,
                   text=f"Show Chen Diagram  ",
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
                                    self.draw_chen_diagram())).pack(side=LEFT, padx=8)

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
        elif operation_type == "Query":
            self.draw_er_diagram()

    def selected_entry(self, operation_type):
        self.conf_frame.forget()
        if operation_type == "Created":
            Created_Entry(self.confroot)
        elif operation_type == "Edit":
            Edit_Entry(self.confroot)
        elif operation_type == "Delete":
            Delete_Entry(self.confroot)
        elif operation_type == "Query":
            self.draw_er_diagram()

    def draw_er_diagram(self):

        os.environ["PATH"] += os.pathsep + r"C:\Users\MMO\LF8_Schule_datenbank\graphviz\bin"

        cur.execute("""
        SELECT
            cols.table_name,
            cols.column_name,
            cols.data_type,
            cons.constraint_type,
            fk_cols.table_name AS ref_table,
            fk_cols.column_name AS ref_column   -- <-- add this
        FROM user_tab_columns cols
        LEFT JOIN user_cons_columns cons_cols
            ON cols.table_name = cons_cols.table_name
            AND cols.column_name = cons_cols.column_name
        LEFT JOIN user_constraints cons
            ON cons_cols.constraint_name = cons.constraint_name
            AND cons.constraint_type IN ('P', 'R')
        LEFT JOIN user_constraints fk_cons
            ON cons.r_constraint_name = fk_cons.constraint_name
        LEFT JOIN user_cons_columns fk_cols
            ON fk_cons.constraint_name = fk_cols.constraint_name
        LEFT JOIN user_tab_comments tab_comments
            ON cols.table_name = tab_comments.table_name
        WHERE tab_comments.comments = 'GUI_CREATED'
        ORDER BY cols.table_name, cols.column_id
        """)
    
        rows = cur.fetchall()

        from sqlalchemy import Table, Column, String, Integer, Date, ForeignKey
    
        engine = create_engine("oracle+oracledb://system:LF8@localhost:1251/?service_name=XEPDB1")
        metadata = MetaData()

        def map_type(data_type):
            return {"NUMBER": Integer, "DATE": Date}.get(data_type, String)

        tables_dict = {}
        for table_name, col_name, data_type, constraint_type, ref_table, ref_column in rows:
            if table_name not in tables_dict:
                tables_dict[table_name] = []
            tables_dict[table_name].append((col_name, data_type, constraint_type, ref_table, ref_column))

        sa_tables = {}
        for table_name, cols in tables_dict.items():
            columns = []
            seen_columns = set()
            for col_name, data_type, constraint_type, ref_table, ref_column in cols:
                if col_name in seen_columns:
                    continue
                seen_columns.add(col_name)

                if constraint_type == 'R' and ref_table and ref_column:
                    columns.append(Column(col_name, map_type(data_type), ForeignKey(f"{ref_table}.{ref_column}")))  # <-- ref_column not col_name
                else:
                    kwargs = {}
                    if constraint_type == 'P':
                        kwargs['primary_key'] = True
                    columns.append(Column(col_name, map_type(data_type), **kwargs))
            sa_tables[table_name] = Table(table_name, metadata, *columns)

        print("Tables in metadata:", list(metadata.tables.keys()))
        for table_name, table in metadata.tables.items():
            print(f"  {table_name}: {[c.name for c in table.columns]}")
            pprint.pprint(sa_tables)

        try:
            render_er(metadata, "er_diagram.svg")
            messagebox.showinfo("ER Diagram", "ER diagram saved as 'er_diagram.svg'.")
            os.startfile("er_diagram.svg")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate ER diagram:\n{e}")
    

    def draw_chen_diagram(self):
    
        os.environ["PATH"] += os.pathsep + r"C:\Users\MMO\LF8_Schule_datenbank\graphviz\bin"

        cur.execute("""
            SELECT
                cols.table_name,
                cols.column_name,
                cols.data_type,
                cons.constraint_type,
                fk_cols.table_name AS ref_table,
                fk_cols.column_name AS ref_column
            FROM user_tab_columns cols
            LEFT JOIN user_cons_columns cons_cols
                ON cols.table_name = cons_cols.table_name
                AND cols.column_name = cons_cols.column_name
            LEFT JOIN user_constraints cons
                ON cons_cols.constraint_name = cons.constraint_name
                AND cons.constraint_type IN ('P', 'R')
            LEFT JOIN user_constraints fk_cons
                ON cons.r_constraint_name = fk_cons.constraint_name
            LEFT JOIN user_cons_columns fk_cols
                ON fk_cons.constraint_name = fk_cols.constraint_name
            LEFT JOIN user_tab_comments tab_comments
                ON cols.table_name = tab_comments.table_name
            WHERE tab_comments.comments = 'GUI_CREATED'
            ORDER BY cols.table_name, cols.column_id
        """)
        rows = cur.fetchall()

        # Struktur aufbauen
        tables_dict = {}
        for table_name, col_name, data_type, constraint_type, ref_table, ref_column in rows:
            if table_name not in tables_dict:
                tables_dict[table_name] = {"cols": [], "fks": []}
            tables_dict[table_name]["cols"].append((col_name, constraint_type))
            if constraint_type == 'R' and ref_table:
                tables_dict[table_name]["fks"].append((table_name, ref_table, col_name))

        # .dot Datei manuell bauen (Chen-Stil)
        project_dir = os.path.dirname(os.path.abspath(__file__))
        dot_path    = os.path.join(project_dir, "er_chen_diagram.dot")
        output_path = os.path.join(project_dir, "er_chen_diagram.svg")

        lines = ["digraph ER {", "    graph [rankdir=LR];"]

        for table_name, info in tables_dict.items():
            pk_cols = [c for c, t in info["cols"] if t == 'P']
            other_cols = [c for c, t in info["cols"] if t != 'P']

            pk_rows    = "".join(f"<tr><td><u>{c}</u></td></tr>" for c in pk_cols)
            other_rows = "".join(f"<tr><td>{c}</td></tr>"        for c in other_cols)

            lines.append(
                f'    "{table_name}" [shape=none, label=<<table border="1" cellborder="0" cellspacing="0">'
                f'<tr><td bgcolor="#BBDEFB"><b>{table_name}</b></td></tr>'
                f'{pk_rows}{other_rows}</table>>];'
            )

        seen = set()
        for table_name, info in tables_dict.items():
            for from_table, to_table, via_col in info["fks"]:
                key = (from_table, to_table)
                if key not in seen:
                    seen.add(key)
                    lines.append(f'    "{to_table}" -> "{from_table}" [label="{via_col}", arrowhead=crow, arrowtail=none, dir=both];')

        lines.append("}")

        with open(dot_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        try:
            # Zwei separate Argumente — kein Windows-Bug
            result = subprocess.run(
                ["dot", "-Tsvg", "-o", output_path, dot_path],
                capture_output=True, text=True
            )
            if result.returncode != 0:
                raise Exception(result.stderr)

            messagebox.showinfo("Chen ER Diagram", f"Gespeichert als '{output_path}'.")
            os.startfile(output_path)
        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Fehler", f"Chen-Diagramm konnte nicht erstellt werden:\n{e}")
        
if __name__ == "__main__":
    root_window = Tk()
    app = conf(root_window)
    root_window.mainloop()