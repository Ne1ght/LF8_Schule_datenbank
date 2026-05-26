from tkinter import *
from tkinter import messagebox
import oracledb
from db import con, cur


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
                fk_pairs = self._fetch_fk_values(*self.fk_info[col_name])  # [(label, val), ...]

                if not fk_pairs:
                    fk_pairs = [("(no data)", "(no data)")]

                fk_labels = [pair[0] for pair in fk_pairs]
                fk_map = {pair[0]: pair[1] for pair in fk_pairs}  # label -> actual FK value

                opt = OptionMenu(self.inner_frame, fk_var, *fk_labels)
                opt.config(width=18)
                opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                row_widgets[col_name] = {"widget": opt, "var": fk_var, "kind": "fk", "fk_map": fk_map}
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
                    fk_var = StringVar(value="-- Select --")
                    fk_pairs = self._fetch_fk_values(*self.fk_info[col_name])  # [(label, val), ...]

                    if not fk_pairs:
                        fk_pairs = [("(no data)", "(no data)")]

                    fk_labels = [pair[0] for pair in fk_pairs]
                    fk_map = {pair[0]: pair[1] for pair in fk_pairs}  # label -> actual FK value

                    opt = OptionMenu(self.inner_frame, fk_var, *fk_labels)
                    opt.config(width=18)
                    opt.grid(row=grid_row, column=col_idx + 1, padx=1, pady=1, sticky="nsew")
                    new_widgets[col_name] = {"widget": opt, "var": fk_var, "kind": "fk", "fk_map": fk_map}
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
        try:
            cur.execute(f'SELECT * FROM "{ref_table}" ORDER BY 1')
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()

            result = []
            for row in rows:
                row_dict = dict(zip(columns, row))
                fk_val = str(row_dict[ref_column])

                # Alle anderen Spalten als Label anzeigen
                other_parts = [
                    f"{col}: {row_dict[col]}"
                    for col in columns
                    if col != ref_column
                ]
                label = f"[{fk_val}]  " + "  |  ".join(other_parts)
                result.append((label, fk_val))

            return result
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

            for col in self.columns_info:
                col_name = col["name"]
                wd = row_data["widgets"][col_name]

                if wd["kind"] == "fk":
                    label = wd["var"].get()
                    if label in ("-- Select --", "(no data)"):
                        self.status_label.config(
                            text=f"Row {row_data['row_num']}: '{col_name}' needs a value.",
                            fg="red")
                        return
                    # Echten FK-Wert aus dem Mapping holen
                    raw = wd["fk_map"].get(label, label)
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
