import os
import sqlite3
from database.DbQueries import GlobalQueries, JavaDuplicateQueries
from vars.DbInstances import DBINSTANCES
# from vars.DbQueues import DBQUEUES
from vars.ExceptedKeys import JAVA_KEYS_ORDER


def process_column(table_name: str, column: str):
    all_data = DBINSTANCES.java_instance.cursor.execute(f"SELECT * FROM {table_name} WHERE {column} IS NOT NULL;").fetchall()
    column_index = JAVA_KEYS_ORDER[column]
    all_data_row_raw = [x[column_index] for x in all_data]
    all_diff_rows = tuple(set(all_data_row_raw))
    print(f"Reducing differents elements length from {len(all_data_row_raw)} to {len(all_diff_rows)}...")

    # For some reason the queue doesn't want to work
    conn = sqlite3.connect("java_duplicates.db")
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

    conn = sqlite3.connect("z_java_servers.db")
    cursor = conn.cursor()
    # move the table to a temporary one
    cursor.execute(f"ALTER TABLE {table_name} RENAME TO AAA_temp_table;")
    conn.commit()
    
    # remake the create table instruction while making sure to replace the needed column w the new type
    TABLE_INFO = list(cursor.execute(GlobalQueries.get_table_info("AAA_temp_table")).fetchall())
    for index, elem in enumerate(TABLE_INFO):
        if elem[0] == column: TABLE_INFO[index] = (column, "INT")

    create_table_sql = f"CREATE TABLE {table_name} ({', '.join([f'{col} {data_type}' for col, data_type in TABLE_INFO])});"
    # print(create_table_sql)
    cursor.execute(create_table_sql)
    conn.commit()
    # copy all from old to new minus changed column
    COLUMNS_TO_REPLACE = [col for col, _ in TABLE_INFO if col != column]
    INSTR = f"INSERT INTO {table_name} ({', '.join(COLUMNS_TO_REPLACE)}) SELECT {', '.join(COLUMNS_TO_REPLACE)} FROM AAA_temp_table;"
    # print(INSTR)

    cursor.execute(INSTR)
    conn.commit()

    # Update values in the new table based on the dictionary
    for save_time, new_value in to_update.items():
        cursor.execute(f"UPDATE {table_name} SET {column} = {new_value} WHERE save_time = {save_time};")
    conn.commit()

    cursor.execute('DROP TABLE AAA_temp_table;')
    conn.commit()
    print("Done replacing elements in original db.")
