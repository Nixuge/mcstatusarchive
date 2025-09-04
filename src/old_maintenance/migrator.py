import os
import sqlite3

from database.DbQueries import GlobalQueries, JavaDuplicateQueries, JavaQueries
from utils.timer import Timer
from vars.ExceptedKeys import JAVA_KEYS_ORDER

def process_column(table_name: str, column: str, table_index: int):
    TEMP_TABLE_NAME = f"AAA_temp_table_{table_index}"
    conn_n = sqlite3.connect("z_java_servers.db")
    cursor_n = conn_n.cursor()
    conn_d = sqlite3.connect("java_duplicates.db")
    cursor_d = conn_d.cursor()

    all_ALL_even_null_data  = cursor_n.execute(f"SELECT * FROM {table_name};").fetchall()
    all_data = cursor_n.execute(f"SELECT * FROM {table_name} WHERE {column} IS NOT NULL;").fetchall()
    column_index = JAVA_KEYS_ORDER[column]
    all_data_row_raw = [x[column_index] for x in all_data]
    all_diff_rows = tuple(set(all_data_row_raw))
    print(f"Reducing differents elements length from {len(all_data_row_raw)} to {len(all_diff_rows)}...")


    # For some reason the queue doesn't want to work
    cursor_d.execute(JavaDuplicateQueries.get_create_table_query(table_name, column))


    # Do the work on the 
    for row_index, row in enumerate(all_diff_rows):
        cursor_d.execute(
            JavaDuplicateQueries.get_insert_query(table_name, column),
            (row_index, row)
        )
    conn_d.commit()
    conn_d.close()
    print("Done writing to new db.")
    
    # Replace all values in the tuple from the db.
    for row_index, row in enumerate(all_ALL_even_null_data):
        elem = row[column_index]
        if elem == None: continue
        newindex = all_diff_rows.index(elem)
        newtuple = list(row)
        newtuple[column_index] = newindex
        all_ALL_even_null_data[row_index] = tuple(newtuple)

    print("did the do.")

    # move the table to a temporary one
    cursor_n.execute(f"ALTER TABLE {table_name} RENAME TO {TEMP_TABLE_NAME};")
    conn_n.commit()
    

    # remake the create table instruction while making sure to replace the needed column w the new type
    timer = Timer()
    TABLE_INFO = list(cursor_n.execute(GlobalQueries.get_table_info(TEMP_TABLE_NAME)).fetchall())
    for row_index, elem in enumerate(TABLE_INFO):
        if elem[0] == column: TABLE_INFO[row_index] = (column, "INT")

    create_table_sql = f"CREATE TABLE {table_name} ({', '.join([f'{col} {data_type}' for col, data_type in TABLE_INFO])});"
    cursor_n.execute(create_table_sql)
    conn_n.commit()

    # copy all from old to new
    cursor_n.executemany(JavaQueries.get_insert_query(table_name), all_ALL_even_null_data)
    conn_n.commit()


    conn_n.commit()
    print(timer.end())

    cursor_n.execute(F'DROP TABLE {TEMP_TABLE_NAME};')
    conn_n.commit()
    print("Done replacing elements in original db.")
    conn_n.close()


def process_column_db_intermediate(table_name: str, column: str, table_index: int):
    TEMP_TABLE_NAME = f"AAA_temp_table_{table_index}"
    conn = sqlite3.connect("z_java_servers.db", check_same_thread=True)
    all_data = conn.cursor().execute(f"SELECT * FROM {table_name} WHERE {column} IS NOT NULL;").fetchall()
    conn.close()
    column_index = JAVA_KEYS_ORDER[column]
    all_data_row_raw = [x[column_index] for x in all_data]
    all_diff_rows = tuple(set(all_data_row_raw))
    print(f"Reducing differents elements length from {len(all_data_row_raw)} to {len(all_diff_rows)}...")

    os.remove("java_duplicates.db")

    # For some reason the queue doesn't want to work
    conn = sqlite3.connect("java_duplicates.db", check_same_thread=True)
    cursor = conn.cursor()
    cursor.execute(JavaDuplicateQueries.get_create_table_query(table_name, column))


    # Do the work on the 
    for index, row in enumerate(all_diff_rows):
        cursor.execute(
            JavaDuplicateQueries.get_insert_query(table_name, column),
            (index, row)
        )
    conn.commit()
    conn.close()
    print("Done writing to new db.")

    # save_time: newvalue
    to_update: dict[int, int] = {}
    for row in all_data:
        save_time = row[0]
        to_update[save_time] = all_diff_rows.index(row[column_index])

    conn = sqlite3.connect("z_java_servers.db", timeout=30.0, check_same_thread=True)
    cursor = conn.cursor()
    # move the table to a temporary one
    cursor.execute(f"ALTER TABLE {table_name} RENAME TO {TEMP_TABLE_NAME};")
    conn.commit()
    
    # remake the create table instruction while making sure to replace the needed column w the new type
    TABLE_INFO = list(cursor.execute(GlobalQueries.get_table_info(TEMP_TABLE_NAME)).fetchall())
    for index, elem in enumerate(TABLE_INFO):
        if elem[0] == column: TABLE_INFO[index] = (column, "INT")

    create_table_sql = f"CREATE TABLE {table_name} ({', '.join([f'{col} {data_type}' for col, data_type in TABLE_INFO])});"
    # print(create_table_sql)
    cursor.execute(create_table_sql)
    conn.commit()
    # copy all from old to new minus changed column
    COLUMNS_TO_REPLACE = [col for col, _ in TABLE_INFO if col != column]
    INSTR = f"INSERT INTO {table_name} ({', '.join(COLUMNS_TO_REPLACE)}) SELECT {', '.join(COLUMNS_TO_REPLACE)} FROM {TEMP_TABLE_NAME};"
    # print(INSTR)
    cursor.execute(INSTR)
    conn.commit()
    print("Done making new db.")

    # Update values in the new table based on the dictionary
    # parameters = [(new_value, save_time) for save_time, new_value in to_update.items()]

    # Update values in the new table based on the dictionary
    timer = Timer()
    for save_time, new_value in to_update.items():
        cursor.execute(f"UPDATE {table_name} SET {column} = {new_value} WHERE save_time = {save_time};")

    conn.commit()
    print(timer.end())

    cursor.execute(F'DROP TABLE {TEMP_TABLE_NAME};')
    conn.commit()
    print("Done replacing elements in original db.")
    conn.close()
