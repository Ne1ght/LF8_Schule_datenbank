from tkinter import *
from tkinter import messagebox
import oracledb
from db import con, cur
import pprint

class Edit_Entry():
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

    def _on_table_selected(self, table_name):
        self.selected_table = table_name
        print(table_name)
        self.entries_list.clear()
        self.status_label.config(text="")

        self._build_scroll_area()
        self._build_header(table_name)

        self.add_row_button.config(state=NORMAL)
        self.insert_button.config(state=NORMAL)


        self._show_entry_table(table_name)
        #self._add_entry_row()

    def _show_entry_table(self, table_name):
        """Fetch and display all rows of *table_name* in a scrollable grid."""
        print("reached show entry table")

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        try:
            cur.execute(f'SELECT * FROM "{table_name}"')
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not query {table_name}:\n{e}")
            return

        
        #viewer = Toplevel(self.confroot)
        #viewer.title(f"Entries — {table_name}")
        #viewer.geometry("860x520")
        #viewer.configure(bg="#F8F7F4")

        
        hdr = Frame(self.inner_frame, bg="#F8F7F4")
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

        Frame(self.inner_frame, height=1, bg="#D3D1C7").pack(fill=X, padx=20, pady=(0, 10))

        
        canvas_frame = Frame(self.inner_frame, bg="#F8F7F4")
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

                    e = Entry(inner,
                            font=("Arial", 9),
                            bg=bg,
                            fg=color,
                            width=COL_W // 8,
                            relief=FLAT)
                    e.insert(0, display)
                    e.grid(row=r_idx + 1, column=c_idx + 1,
                    padx=(0, 1), pady=(0, 1), sticky="nsew")

        Button(self.inner_frame,
               text="Close",
               font=("Arial", 10),
               bg="#E8E7E1",
               fg="#444441",
               activebackground="#D3D1C7",
               relief=FLAT,
               padx=16,
               pady=6,
               cursor="hand2",
               command=self.inner_frame.destroy).pack(pady=(0, 14))

    def _build_header(self, table_name):
        
        print("reached build header")
        cur.execute(f'SELECT * FROM "{table_name}"')
        columns = [desc[0] for desc in cur.description]
        pprint.pprint(columns)
        rows = cur.fetchall()
        pprint.pprint(rows)

        COL_W = 160
        HDR_BG = "#D3D1C7"
        HDR_FG = "#2C2C2A"
        ROW_BG = "#FFFFFF"
        ALT_BG = "#F1EFE8"
        CELL_FG = "#2C2C2A"
        NULL_FG = "#B4B2A9"

        Label(self.inner_frame,
              text="#",
              font=("Arial", 9, "bold"),
              relief=RIDGE,
              width=4,
              bg="lightgray").grid(row=0, column=0, padx=1, pady=1, sticky="nsew")

        for c_idx, col_name in enumerate(columns):
            Label(self.inner_frame,
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

        Label(self.inner_frame,
              text="Del",
              font=("Arial", 9, "bold"),
              relief=RIDGE,
              width=4,
              bg="lightgray").grid(row=0, column=len(self.columns_info) + 1,
                                   padx=1, pady=1, sticky="nsew")

    def _validate_and_insert(self):
        self.status_label.config(text="", fg="black")

        if not self.entries_list:
            self.status_label.config(text="No rows to insert!", fg="red")
            return

        rows_to_insert = []

        for row_data in self.entries_list:
            row_values = {}

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
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    import datetime
                    datetime.datetime.strptime(raw, fmt)
                    return None
                except ValueError:
                    continue
            return (f"Row {row_num}: '{col['name']}' invalid date. "
                    "Use YYYY-MM-DD, DD.MM.YYYY, or DD/MM/YYYY.")

        elif dtype == "TIMESTAMP":
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    import datetime
                    datetime.datetime.strptime(raw, fmt)
                    return None
                except ValueError:
                    continue
            return (f"Row {row_num}: '{col['name']}' invalid timestamp. "
                    "Use YYYY-MM-DD HH:MM:SS.")

        return None

    def _cast_value(self, val, col):
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
        from conf import conf
        conf(self.confroot)

