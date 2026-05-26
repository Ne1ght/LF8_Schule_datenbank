from tkinter import *
from tkinter import messagebox
import pprint
import oracledb
from db import con, cur


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
        self.enter_table_name.grid(row=0, column=3)

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

        self.opt = StringVar(value="Select a datatype")

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
            column_name = row["entry_name"].get().strip().upper()
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
                primary_keys.append(column_name)

            if is_fk:
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
                   command=self.ForKey.destroy).pack(pady=10)
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
            return []

    def update_fk_columns(self, fk_idx):
        ref = self.fk_references[fk_idx]
        selected_table = ref["table_var"].get()

        if selected_table == "-- Select Table --":
            return

        table_info = next(
            (t for t in ref["available_pks"] if t["table_name"] == selected_table),
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
                command=lambda val=col: ref["column_var"].set(f"{val['column_name']} ({val['datatype']})")
            )

    def validate_and_create_table(self):
        for idx, ref in self.fk_references.items():
            table = ref["table_var"].get()
            column_full = ref["column_var"].get()

            if table == "-- Select Table --" or column_full == "-- Select Column --":
                messagebox.showerror(
                    "Missing Selection",
                    f"Please select a reference for FK column '{ref['fk_column']}'"
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
        from conf import conf
        conf(self.confroot)
