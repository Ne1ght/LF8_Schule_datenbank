from tkinter import *
from tkinter import messagebox
import oracledb
from db import con, cur


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
                "name_var": StringVar(value=col_name.upper()),
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
                    "name": column_name.upper(),
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
                    "ref_column": ref_column.upper(),
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
                    "column_name": column_name.upper(),
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
        from conf import conf
        conf(self.confroot)
