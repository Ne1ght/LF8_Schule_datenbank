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
        Created_Entry(roo)


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
                foreign_keys.append(column_name)

                self.Foreign_Key_True()

        if not column_definitions:
            self.status_label.config(text="Error: Check of table failed, not valid", fg="red")

        print(column_definitions)

        if primary_keys:
            pk_constraint = f"CONSTRAINT pk_{table_name} PRIMARY KEY ({', '.join(primary_keys)})"
            column_definitions.append(pk_constraint)

        print(column_definitions)

        sql = f"CREATE TABLE {table_name} (\n"
        sql += ",\n".join(f"     {col}" for col in column_definitions)
        sql += "\n)"

        print("\n" + "=" * 50)
        print("Generated SQL:")
        print("=" * 50)
        print(sql)
        print("=" * 50 + "\n")

        self.execute_sql(sql, table_name)


    def Foreign_Key_True(self):
        self.ForKey = Toplevel(self.confroot)

        self.ForKey_frame = Frame(self.ForKey)
        self.ForKey_frame.pack()

        self.ForKey_label = Label(self.ForKey_frame,
                                   text="Select a Table with a MATCHING Key",
                                   font=("arial", 12),
                                   fg="black")
        self.ForKey_label.pack()

        query = """
        SELECT 
            cols.table_name,
            cols.column_name,
            cols.data_type,
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
        WHERE
            
        ORDER BY 
            cols.table_name, 
            cons_cols.position
        """

        cur.execute(query)

        result = cur.fetchall()

        pprint.pprint(result)

        if not result:
            pass
        else:
            pass


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