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

# can i please just upd


class conf():
    def __init__(self, root_window):
        self.confroot = root_window
        self.confroot.title("Config")
        self.confroot.geometry("600x600")

        self.conf_frame = Frame(self.confroot)
        self.conf_frame.pack()

        self.created_button = Button(self.conf_frame,
                                     text="Created",
                                     font=("Arial", 20),
                                     command=lambda: self.select_option("Created")
                                     )
        self.created_button.grid(row=1, column=0)

        self.edit_button = Button(self.conf_frame,
                                  text="Edit",
                                  font=("Arial", 20),
                                  command=lambda: self.select_option("Edit")
                                  )
        self.edit_button.grid(row=1, column=2)

        self.delete_button = Button(self.conf_frame,
                                    text="Delete",
                                    font=("Arial", 20),
                                    command=lambda: self.select_option("Delete")
                                    )
        self.delete_button.grid(row=2, column=0)

        self.Test_DB = Button(self.conf_frame,
                              text="Query Tables",
                              font=("Arial", 20),
                              command=self.Query_DB)
        self.Test_DB.grid(row=3, column=0)

    def Query_DB(self):

        Query = """SELECT 
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

        cur.execute(Query)

        result = cur.fetchall()

        pprint.pprint(result)

    def select_option(self, operation_type):

        if operation_type == "Creatred":
            operation = "Created"
            state = "new"
        elif operation_type == "Edit":
            operation = "Edit"
            state= "existing"
        else:
            operation = "Delete"
            state = "existing"

        self.dialog = Toplevel(self.confroot)
        self.dialog_label = Label(self.dialog,
                                  text=f"Do you want to {operation} a {state} Table or {state} Entry in a Table?",
                                  font=("Arial", 12),
                                  )
        self.dialog_label.grid(row=0, columnspan=5)

        self.New_Table_Button = Button(self.dialog,
                                       text=f"{state} Table",
                                       font=("Arial", 12),
                                       command=lambda: self.selected_table(operation_type)
                                       )
        self.New_Table_Button.grid(row=1, column=1)

        self.New_Entry_Button = Button(self.dialog,
                                       text=f"{state} Entry",
                                       font=("Arial", 12),
                                       command=lambda: self.selected_entry(operation_type)
                                       )
        self.New_Entry_Button.grid(row=1, column=3)

    def selected_table(self, operation_type):
        self.dialog.destroy()
        self.conf_frame.forget()

        if operation_type == "Created":
            Open_Created_Table = Created_Table(self.confroot)
        elif operation_type == "Edit":
            pass
        elif operation_type == "Delete":
            open_Deleted_Table = Delete_Table(self.confroot)

    def selected_entry(self, operation_type):
        self.dialog.destroy()
        self.conf_frame.forget()
        Created_Entry(root_window)


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

                column_name = column_definitions[0].split()[0]
                full_datatype = column_definitions[0].split()[1]
                foreign_keys.append({
                    "column_name": column_name,
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


class Created_Entry():
    def __init__(self, root_window):
        self.confroot = root_window
        self.entries_list = []  # list of dicts, one per entry row
        self.columns_info = []  # list of dicts describing each column
        self.selected_table = None

        # ── Outer frames ──────────────────────────────────────────────────────
        self.top_frame = Frame(self.confroot)
        self.top_frame.pack(fill=X, padx=10, pady=5)

        self.table_frame = Frame(self.confroot)
        self.table_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)

        self.bottom_frame = Frame(self.confroot)
        self.bottom_frame.pack(fill=X, padx=10, pady=5)

        # ── Top bar: back button + table selector ─────────────────────────────
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

        # ── Bottom bar: + Add Row, Insert ─────────────────────────────────────
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

        # ── Scrollable area for column headers + entry rows ───────────────────
        self._build_scroll_area()

    # ──────────────────────────────────────────────────────────────────────────
    # Scrollable container
    # ──────────────────────────────────────────────────────────────────────────
    def _build_scroll_area(self):
        """Create a canvas with both H and V scrollbars that holds the grid."""
        # destroy any previous scroll area
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

        # Mouse-wheel scrolling (vertical)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ──────────────────────────────────────────────────────────────────────────
    # DB helpers
    # ──────────────────────────────────────────────────────────────────────────
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
        """Return ordered list of column info dicts for *table_name*."""
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
        """Return set of column names that are part of the primary key."""
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
        """Return dict mapping column_name -> (ref_table, ref_column) for FKs."""
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

    # ──────────────────────────────────────────────────────────────────────────
    # Table selection
    # ──────────────────────────────────────────────────────────────────────────
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

        # Rebuild scroll area so we start fresh
        self._build_scroll_area()
        self._build_header()

        # Enable controls
        self.add_row_button.config(state=NORMAL)
        self.insert_button.config(state=NORMAL)

        # Add first empty entry row automatically
        self._add_entry_row()

    def _build_header(self):
        """Draw the column-header row inside inner_frame."""
        # Row-number header
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

        # Delete-button column header
        Label(self.inner_frame,
              text="Del",
              font=("Arial", 9, "bold"),
              relief=RIDGE,
              width=4,
              bg="lightgray").grid(row=0, column=len(self.columns_info) + 1,
                                   padx=1, pady=1, sticky="nsew")

    # ──────────────────────────────────────────────────────────────────────────
    # Entry rows
    # ──────────────────────────────────────────────────────────────────────────
    def _add_entry_row(self):
        """Append a new editable row to inner_frame."""
        row_num = len(self.entries_list) + 1  # display index (1-based)
        grid_row = row_num  # row 0 is the header

        row_widgets = {}

        # Row number label
        Label(self.inner_frame,
              text=str(row_num),
              font=("Arial", 9),
              relief=GROOVE,
              width=4).grid(row=grid_row, column=0, padx=1, pady=1, sticky="nsew")

        for col_idx, col in enumerate(self.columns_info):
            col_name = col["name"]
            is_fk = col_name in self.fk_info

            if is_fk:
                # Show a dropdown with valid FK values
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

        # Delete button
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
            "row_label": None,  # we re-label on delete; store separately
        })

        # Update scrollregion
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

        # Destroy all widgets in that grid row
        for widget in self.inner_frame.grid_slaves(row=grid_row):
            widget.destroy()

        self.entries_list.pop(idx)

        # Rebuild remaining rows so grid stays compact and labels are correct
        self._rebuild_rows()

    def _rebuild_rows(self):
        """After a deletion, re-grid all existing entry rows."""
        # Destroy everything except row 0 (header)
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

    # ──────────────────────────────────────────────────────────────────────────
    # FK value lookup
    # ──────────────────────────────────────────────────────────────────────────
    def _fetch_fk_values(self, ref_table, ref_column):
        """Return list of string values from the referenced PK column."""
        try:
            cur.execute(f'SELECT "{ref_column}" FROM "{ref_table}" ORDER BY 1')
            return [str(row[0]) for row in cur.fetchall()]
        except Exception as e:
            print(f"Error fetching FK values from {ref_table}.{ref_column}: {e}")
            return []

    # ──────────────────────────────────────────────────────────────────────────
    # Validation & insert
    # ──────────────────────────────────────────────────────────────────────────
    def _validate_and_insert(self):
        self.status_label.config(text="", fg="black")

        if not self.entries_list:
            self.status_label.config(text="No rows to insert!", fg="red")
            return

        rows_to_insert = []  # list of dicts: col_name -> raw value

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

                # Required check (NOT NULL + not PK — PK required too)
                is_pk = col_name in self.pk_columns
                if not col["nullable"] or is_pk:
                    if raw == "":
                        self.status_label.config(
                            text=f"Row {row_data['row_num']}: '{col_name}' is required.",
                            fg="red")
                        return

                # Type validation
                err = self._validate_value(raw, col, row_data["row_num"])
                if err:
                    self.status_label.config(text=err, fg="red")
                    return

                row_values[col_name] = raw if raw != "" else None

            if valid:
                rows_to_insert.append(row_values)

        # Build and execute INSERT statements
        col_names = [col["name"] for col in self.columns_info]
        placeholders = ", ".join(f":{c}" for c in col_names)
        col_list = ", ".join(col_names)
        sql = f'INSERT INTO "{self.selected_table}" ({col_list}) VALUES ({placeholders})'

        inserted = 0
        try:
            for row_values in rows_to_insert:
                # Convert types for Oracle
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

            # Clear the grid, keep the table selection
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
            return None  # nullable / optional already checked above

        dtype = col["type"]

        if dtype == "NUMBER":
            try:
                float(raw)
            except ValueError:
                return f"Row {row_num}: '{col['name']}' must be a number."

            if col["precision"] is not None:
                # Check total digits
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

        return val  # VARCHAR2, CHAR, CLOB — pass as string

    # ──────────────────────────────────────────────────────────────────────────
    # Navigation
    # ──────────────────────────────────────────────────────────────────────────
    def go_back(self):
        self.top_frame.forget()
        self.table_frame.forget()
        self.bottom_frame.forget()
        conf(self.confroot)



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
    root_window = Tk()
    app = conf(root_window)
    root_window.mainloop()