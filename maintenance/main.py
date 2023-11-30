from database.DbQueries import GlobalQueries
from maintenance.checks import run_db_checks
from vars.DbInstances import DBINSTANCES
from vars.DbQueues import DBQUEUES
from vars.ExceptedKeys import JAVA_EXCEPTED_KEYS


def maintenance_main():
    DBQUEUES.db_queue_java.start()
    DBQUEUES.db_queue_duplicates_java.start()
    print("Maintenance tool for mcstatusarchive's DB.")
    print("Running basic DB checks")
    db_name = "Play_KingdomsMineMC_Net"
    columns_to_check = get_default_types_columns(db_name)
    print(f"columns to check: {columns_to_check}")
    data = run_db_checks(db_name, columns_to_check)
    print(f"Got data: {data}")

# Basically columns where it's possible to do maintenance
def get_default_types_columns(table_name: str):
    final = []
    columns = DBINSTANCES.java_instance.cursor.execute(GlobalQueries.get_table_info(table_name)).fetchall()

    for key, column_type in columns:
        if key not in JAVA_EXCEPTED_KEYS.keys() or column_type != JAVA_EXCEPTED_KEYS[key]: 
            continue
        final.append(key)

    return final
