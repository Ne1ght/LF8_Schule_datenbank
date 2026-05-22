from tkinter import *
from tkinter import messagebox
import oracledb
from db import con, cur
import datetime

class Edit_Entry():
    def __init__(self, root_window):
        self.confroot = root_window
        self.entries_list = []  # New rows
        self.existing_rows = []  # Existing rows with tracking
        self.columns_info = []
        self.selected_table = None
        self.pk_columns = set()
        self.fk_info = {}
        self.table_inner = None  # Will store the canvas inner frame for data rows

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

        self.save_button = Button(self.bottom_frame,
                                  text="Save Changes",
                                  font=("Arial", 10, "bold"),
                                  bg="green",
                                  fg="white",
                                  state=DISABLED,
                                  command=self._validate_and_save)
        self.save_button.grid(row=0, column=1, padx=5, pady=5)

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

    def _fetch_columns(self, table_name):
        """Fetch column information for the selected table."""
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
        """Fetch primary key columns."""
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
        """Fetch foreign key information."""
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

    def _fetch_fk_values(self, ref_table, ref_column):
        """Fetch available values for a foreign key column."""
        try:
            cur.execute(f'SELECT "{ref_column}" FROM "{ref_table}" ORDER BY 1')
            return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching FK values from {ref_table}.{ref_column}: {e}")
            return []

    def _add_entry_row(self):
        """Add a new empty row for data entry."""
        if not self.table_inner:
            messagebox.showwarning("Error", "Please select a table first.")
            return

        row_num = len(self.entries_list) + len(self.existing_rows) + 1
        grid_row = len(self.existing_rows) + len(self.entries_list) + 1  # Account for header

        row_widgets = {}

        Label(self.table_inner,
              text=f"N{len(self.entries_list) + 1}",
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
                opt = OptionMenu(self.table_inner, fk_var, *fk_values)
                opt.config(width=18)
                opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                row_widgets[col_name] = {"widget": opt, "var": fk_var, "kind": "fk"}
            else:
                entry = Entry(self.table_inner, width=20)
                entry.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                row_widgets[col_name] = {"widget": entry, "var": None, "kind": "entry"}

        del_btn = Button(self.table_inner,
                         text="✕",
                         font=("Arial", 8),
                         fg="red",
                         width=3,
                         command=lambda r=row_num: self._delete_new_row(row_num))
        del_btn.grid(row=grid_row, column=len(self.columns_info) + 1,
                     padx=1, pady=1, sticky="nsew")

        self.entries_list.append({
            "row_num": row_num,
            "grid_row": grid_row,
            "widgets": row_widgets,
            "del_btn": del_btn,
        })

        self.table_inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _delete_new_row(self, row_num):
        """Delete a new row from entries_list."""
        idx = next((i for i, r in enumerate(self.entries_list)
                    if r["row_num"] == row_num), None)
        if idx is None:
            return

        row_data = self.entries_list[idx]
        grid_row = row_data["grid_row"]

        for widget in self.inner_frame.grid_slaves(row=grid_row):
            widget.destroy()

        self.entries_list.pop(idx)
        self._rebuild_display()

    def _delete_existing_row(self, row_idx):
        """Mark an existing row for deletion."""
        if row_idx < len(self.existing_rows):
            self.existing_rows[row_idx]["marked_for_delete"] = True
            self._rebuild_display()

    def _rebuild_display(self):
        """Rebuild the display after modifications."""
        if not self.table_inner:
            return

        # Destroy all data rows (but keep header)
        for widget in self.table_inner.grid_slaves():
            info = widget.grid_info()
            if info and int(info.get("row", 0)) > 0:
                widget.destroy()

        # Rebuild existing rows
        grid_row = 1
        for idx, row_data in enumerate(self.existing_rows):
            if row_data["marked_for_delete"]:
                continue

            Label(self.table_inner,
                  text=f"E{idx + 1}",
                  font=("Arial", 9),
                  relief=GROOVE,
                  width=4).grid(row=grid_row, column=0, padx=1, pady=1, sticky="nsew")

            for col_idx, col in enumerate(self.columns_info):
                col_name = col["name"]
                is_fk = col_name in self.fk_info
                current_value = row_data["current_values"][col_name]

                if is_fk:
                    fk_var = StringVar(value=str(current_value) if current_value else "-- Select --")
                    fk_values = self._fetch_fk_values(*self.fk_info[col_name])
                    if not fk_values:
                        fk_values = ["(no data)"]
                    opt = OptionMenu(self.table_inner, fk_var, *fk_values)
                    opt.config(width=18)
                    opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    row_data["widgets"][col_name] = {"widget": opt, "var": fk_var, "kind": "fk"}
                else:
                    entry = Entry(self.table_inner, width=20)
                    entry.insert(0, str(current_value) if current_value is not None else "")
                    entry.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    row_data["widgets"][col_name] = {"widget": entry, "var": None, "kind": "entry"}

            del_btn = Button(self.table_inner,
                             text="✕",
                             font=("Arial", 8),
                             fg="red",
                             width=3,
                             command=lambda r_idx=idx: self._delete_existing_row(r_idx))
            del_btn.grid(row=grid_row, column=len(self.columns_info) + 1,
                         padx=1, pady=1, sticky="nsew")

            row_data["grid_row"] = grid_row
            grid_row += 1

        # Rebuild new entry rows
        for entry_idx, entry_data in enumerate(self.entries_list):
            row_label = f"N{entry_idx + 1}"
            Label(self.table_inner,
                  text=row_label,
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
                    opt = OptionMenu(self.table_inner, fk_var, *fk_values)
                    opt.config(width=18)
                    opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    entry_data["widgets"][col_name] = {"widget": opt, "var": fk_var, "kind": "fk"}
                else:
                    entry = Entry(self.table_inner, width=20)
                    entry.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    entry_data["widgets"][col_name] = {"widget": entry, "var": None, "kind": "entry"}

            del_btn = Button(self.table_inner,
                             text="✕",
                             font=("Arial", 8),
                             fg="red",
                             width=3,
                             command=lambda r_num=entry_idx + len(self.existing_rows) + 1: self._delete_new_row(r_num))
            del_btn.grid(row=grid_row, column=len(self.columns_info) + 1,
                         padx=1, pady=1, sticky="nsew")

            entry_data["grid_row"] = grid_row
            grid_row += 1

        self.table_inner.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_table_selected(self, table_name):
        self.selected_table = table_name
        print(f"Selected table: {table_name}")
        self.entries_list.clear()
        self.existing_rows.clear()
        self.status_label.config(text="")

        # Fetch column info, PK, and FK
        self.columns_info = self._fetch_columns(table_name)
        self.pk_columns = self._fetch_pk_columns(table_name)
        self.fk_info = self._fetch_fk_info(table_name)

        if not self.columns_info:
            self.status_label.config(text="Could not load columns.", fg="red")
            return

        self._build_scroll_area()
        self._show_entry_table(table_name)

        self.add_row_button.config(state=NORMAL)
        self.save_button.config(state=NORMAL)

    def _show_entry_table(self, table_name):
        """Fetch and display all rows of table_name in editable form."""
        print("Loading table data...")

        for widget in self.inner_frame.winfo_children():
            widget.destroy()

        try:
            cur.execute(f'SELECT * FROM "{table_name}"')
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not query {table_name}:\n{e}")
            return

        # Store existing rows with tracking
        for row_data in rows:
            original_dict = dict(zip(columns, row_data))
            self.existing_rows.append({
                "original_values": original_dict.copy(),
                "current_values": original_dict.copy(),
                "widgets": {},
                "marked_for_delete": False,
                "grid_row": None,
                "column_names": columns  # Store column names for reference
            })

        print(f"Loaded {len(self.existing_rows)} existing rows")

        # Display header info
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

        # Build scroll area for editable rows
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

        self.table_inner = Frame(canvas, bg="#F8F7F4")
        cw = canvas.create_window((0, 0), window=self.table_inner, anchor=NW)
        self.canvas_table = canvas
        self.canvas_cw = cw

        self.table_inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfig(cw, width=e.width))
        canvas.bind_all("<MouseWheel>",
                        lambda e: canvas.yview_scroll(int(-1 * (e.delta / 120)), "units"))

        # Color scheme
        COL_W = 160
        HDR_BG = "#D3D1C7"
        HDR_FG = "#2C2C2A"
        ROW_BG = "#FFFFFF"
        ALT_BG = "#F1EFE8"
        CELL_FG = "#2C2C2A"
        NULL_FG = "#B4B2A9"

        # Build header row
        Label(self.table_inner,
              text="#",
              font=("Arial", 9, "bold"),
              bg=HDR_BG,
              fg=HDR_FG,
              width=5,
              relief=FLAT,
              anchor=CENTER,
              pady=7).grid(row=0, column=0, padx=(0, 1), pady=(0, 1), sticky="nsew")

        for c_idx, col_name in enumerate(columns):
            Label(self.table_inner,
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

        # Add delete column header
        Label(self.table_inner,
              text="Del",
              font=("Arial", 9, "bold"),
              bg=HDR_BG,
              fg=HDR_FG,
              width=5,
              relief=FLAT,
              anchor=CENTER,
              pady=7).grid(row=0, column=len(columns) + 1,
                           padx=(0, 1), pady=(0, 1), sticky="nsew")

        # Display rows as editable entries
        if not rows:
            Label(self.table_inner,
                  text="No entries found.",
                  font=("Arial", 10),
                  bg=ROW_BG,
                  fg=NULL_FG,
                  pady=12).grid(row=1, column=0,
                                columnspan=len(columns) + 2,
                                sticky="nsew")
        else:
            for r_idx, row in enumerate(rows):
                bg = ROW_BG if r_idx % 2 == 0 else ALT_BG

                Label(self.table_inner,
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
                    col_name = columns[c_idx]
                    is_null = value is None
                    display = "(null)" if is_null else str(value)
                    color = NULL_FG if is_null else CELL_FG

                    e = Entry(self.table_inner,
                            font=("Arial", 9),
                            bg=bg,
                            fg=color,
                            width=COL_W // 8,
                            relief=FLAT)
                    e.insert(0, display)
                    e.grid(row=r_idx + 1, column=c_idx + 1,
                           padx=(0, 1), pady=(0, 1), sticky="nsew")

                    # Store widget reference
                    self.existing_rows[r_idx]["widgets"][col_name] = {
                        "widget": e,
                        "var": None,
                        "kind": "entry"
                    }

                # Add delete button
                del_btn = Button(self.table_inner,
                                 text="✕",
                                 font=("Arial", 8),
                                 fg="red",
                                 width=3,
                                 relief=FLAT,
                                 command=lambda r_idx=r_idx: self._mark_row_for_delete(r_idx))
                del_btn.grid(row=r_idx + 1, column=len(columns) + 1,
                             padx=(0, 1), pady=(0, 1), sticky="nsew")

        self.table_inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def _mark_row_for_delete(self, row_idx):
        """Mark a row for deletion."""
        if row_idx < len(self.existing_rows):
            self.existing_rows[row_idx]["marked_for_delete"] = True
            self._rebuild_display()

    def bind_name(self, c):
        return c.replace(" ", "_").replace("-", "_")


    def _validate_and_save(self):
        """Validate and save all changes: updates, inserts, and deletes."""
        self.status_label.config(text="", fg="black")

        # Collect changes from existing rows
        updates = []
        deletes = []

        for row_idx, row_data in enumerate(self.existing_rows):
            if row_data["marked_for_delete"]:
                deletes.append(row_data)
                continue

            # Check for changes
            changes = {}
            for col_name in row_data["column_names"]:
                if col_name in row_data["widgets"]:
                    wd = row_data["widgets"][col_name]
                    if wd["kind"] == "fk":
                        new_val = wd["var"].get()
                    else:
                        new_val = wd["widget"].get().strip()

                    old_val = row_data["original_values"][col_name]

                    # Handle null comparison
                    if (new_val == "(null)" or new_val == "") and old_val is None:
                        continue
                    if str(new_val) != str(old_val):
                        changes[col_name] = new_val

            if changes:
                updates.append({
                    "original": row_data["original_values"],
                    "changes": changes,
                    "column_names": row_data["column_names"]
                })

        # Collect new rows to insert
        inserts = []
        for entry_data in self.entries_list:
            row_values = {}
            for col in self.columns_info:
                col_name = col["name"]
                wd = entry_data["widgets"][col_name]

                if wd["kind"] == "fk":
                    raw = wd["var"].get()
                    if raw in ("-- Select --", "(no data)"):
                        self.status_label.config(
                            text=f"New row: '{col_name}' needs a value.",
                            fg="red")
                        return
                else:
                    raw = wd["widget"].get().strip()

                is_pk = col_name in self.pk_columns
                if not col["nullable"] or is_pk:
                    if raw == "":
                        self.status_label.config(
                            text=f"New row: '{col_name}' is required.",
                            fg="red")
                        return

                err = self._validate_value(raw, col, "new")
                if err:
                    self.status_label.config(text=err, fg="red")
                    return

                row_values[col_name] = raw if raw != "" else None

            inserts.append(row_values)

        # Execute database operations
        try:
            deleted_count = 0
            updated_count = 0
            inserted_count = 0

            # Delete rows
            for row_data in deletes:
                pk_values = {}
                for pk_col in self.pk_columns:
                    pk_values[pk_col] = row_data["original_values"][pk_col]

                where_clause = " AND ".join([f'"{pk}" = :{pk}' for pk in self.pk_columns])
                sql = f'DELETE FROM "{self.selected_table}" WHERE {where_clause}'

                cur.execute(sql, pk_values)
                deleted_count += 1

            # Update existing rows
            for update_data in updates:
                pk_values = {}
                for pk_col in self.pk_columns:
                    pk_values[pk_col] = update_data["original"][pk_col]

                set_clause = ", ".join([f'"{col}" = :{self.bind_name(col)}' for col in update_data["changes"].keys()])
                where_clause = " AND ".join([f'"{pk}" = :{self.bind_name(pk)}' for pk in self.pk_columns])

                bind_vars = {self.bind_name(k): v for k, v in update_data["changes"].items()}
                for pk_col in self.pk_columns:
                    bind_vars[f"pk_{self.bind_name(pk_col)}"] = update_data["original"][pk_col]

                # Cast values properly
                for col_name, val in bind_vars.items():
                    if not col_name.startswith("pk_"):
                        col = next((c for c in self.columns_info if self.bind_name(c["name"]) == col_name), None)
                        if col:
                            bind_vars[col_name] = self._cast_value(val, col)

                sql = f'UPDATE "{self.selected_table}" SET {set_clause} WHERE {where_clause}'

                cur.execute(sql, bind_vars)
                updated_count += 1

            # Insert new rows
            if inserts:
                col_names = [col["name"] for col in self.columns_info]
                placeholders = ", ".join(f":{self.bind_name(c)}" for c in col_names)
                col_list = ", ".join([f'"{c}"' for c in col_names])
                sql = f'INSERT INTO "{self.selected_table}" ({col_list}) VALUES ({placeholders})'

                for row_values in inserts:
                    bound = {}
                    for col in self.columns_info:
                        val = row_values[col["name"]]
                        bound[self.bind_name(col["name"])] = self._cast_value(val, col)

                    cur.execute(sql, bound)
                    inserted_count += 1

            con.commit()

            msg = "✓ Changes saved!"
            if deleted_count > 0:
                msg += f" {deleted_count} deleted"
            if updated_count > 0:
                msg += f" {updated_count} updated"
            if inserted_count > 0:
                msg += f" {inserted_count} inserted"

            self.status_label.config(text=msg, fg="green")
            print(msg)

            # Reload the table
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
            print(f"Save error: {e}")

    def _validate_value(self, raw, col, row_context):
        """Validate a value according to its column definition."""
        if raw == "" or raw is None:
            return None

        dtype = col["type"]

        if dtype == "NUMBER":
            try:
                float(raw)
            except ValueError:
                return f"{row_context}: '{col['name']}' must be a number."

            if col["precision"] is not None:
                parts = raw.replace("-", "").split(".")
                int_digits = len(parts[0].lstrip("0") or "0")
                dec_digits = len(parts[1]) if len(parts) > 1 else 0
                scale = col["scale"] if col["scale"] is not None else 0
                prec = col["precision"]
                if int_digits > (prec - scale) or dec_digits > scale:
                    return (f"{row_context}: '{col['name']}' exceeds "
                            f"NUMBER({prec},{scale}) range.")

        elif dtype in ("VARCHAR2", "NVARCHAR2"):
            if col["length"] and len(raw.encode("utf-8")) > col["length"]:
                return (f"{row_context}: '{col['name']}' exceeds "
                        f"max length {col['length']}.")

        elif dtype in ("CHAR", "NCHAR"):
            if col["length"] and len(raw) > col["length"]:
                return (f"{row_context}: '{col['name']}' exceeds "
                        f"max length {col['length']}.")

        elif dtype == "DATE":
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y", "%Y/%m/%d"):
                try:
                    datetime.datetime.strptime(raw, fmt)
                    return None
                except ValueError:
                    continue
            return (f"{row_context}: '{col['name']}' invalid date. "
                    "Use YYYY-MM-DD, DD.MM.YYYY, or DD/MM/YYYY.")

        elif dtype == "TIMESTAMP":
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S",
                        "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    datetime.datetime.strptime(raw, fmt)
                    return None
                except ValueError:
                    continue
            return (f"{row_context}: '{col['name']}' invalid timestamp. "
                    "Use YYYY-MM-DD HH:MM:SS.")

        return None

    def _cast_value(self, val, col):
        """Cast a value to its appropriate Python type."""
        if val is None or val == "" or val == "(null)":
            return None

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
                    return datetime.datetime.strptime(val, fmt).date()
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

