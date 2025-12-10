from sqlite3 import connect, Row

database: str = 'db/school.db'

def getprocess(sql: str, vals: list) -> list:
    conn = connect(database)
    conn.row_factory = Row
    cursor = conn.cursor()
    cursor.execute(sql, vals)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return data

def postprocess(sql: str, vals: list) -> bool:
    try:
        conn = connect(database)
        cursor = conn.cursor()
        cursor.execute(sql, vals)
        conn.commit()
        success = cursor.rowcount > 0
    except Exception as e:
        print(f"ERROR : {e}")
        success = False
    finally:
        cursor.close()
        conn.close()
    return success

def getall(table: str) -> list:
    sql = f"SELECT * FROM `{table}`"
    return getprocess(sql, [])

def getrecord(table: str, **kwargs) -> list:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    flds = [f"`{key}` = ?" for key in keys]
    fields = " AND ".join(flds)
    sql = f"SELECT * FROM `{table}` WHERE {fields}"
    return getprocess(sql, vals)

def addrecord(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    placeholders = ",".join(["?"] * len(keys))
    fields = "`,`".join(keys)
    sql = f"INSERT INTO `{table}`(`{fields}`) VALUES ({placeholders})"
    return postprocess(sql, vals)

def deleterecord(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    flds = [f"`{key}` = ?" for key in keys]
    fields = " AND ".join(flds)
    sql = f"DELETE FROM `{table}` WHERE {fields}"
    return postprocess(sql, vals)

def updaterecord(table: str, **kwargs) -> bool:
    keys = list(kwargs.keys())
    vals = list(kwargs.values())
    # First key = primary key (like idno)
    flds = [f"`{key}` = ?" for key in keys[1:]]
    fields = ",".join(flds)
    sql = f"UPDATE `{table}` SET {fields} WHERE `{keys[0]}` = ?"
    new_vals = vals[1:] + [vals[0]]
    return postprocess(sql, new_vals)
