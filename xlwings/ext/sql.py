from .. import func, arg, ret
import sqlite3


def conv_value(value, col_is_str):
    if value is None:
        return "NULL"
    if col_is_str:
        return repr(str(value))
    elif isinstance(value, bool):
        return 1 if value else 0
    else:
        return repr(value)


@func
@arg("tables", expand="table", ndim=2)
@ret(expand="table")
def sql(query, *tables):
    return _sql(query, *tables)


@func
@arg("tables", expand="table", ndim=2)
def sql_dynamic(query, *tables):
    """Called if native dynamic arrays are available"""
    return _sql(query, *tables)


def _sql(query, *tables):
    conn = sqlite3.connect(":memory:")

    c = conn.cursor()

    for i, table in enumerate(tables):
        cols = table[0]
        rows = table[1:]
        types = [any(type(row[j]) is str for row in rows) for j in range(len(cols))]
        name = chr(65 + i)

        stmt = f'''CREATE TABLE {name} ({", ".join(f"""'{col}' {"STRING" if typ else "REAL"}""" for col, typ in zip(cols, types))})'''
        c.execute(stmt)

        if rows:
            stmt = f"""INSERT INTO {name} VALUES {", ".join(f'({", ".join(conv_value(value, type) for value, typ in zip(row, types))})' for row in rows)}"""
            # Fixes values like these:
            # sql('SELECT a FROM a', [['a', 'b'], ["""X"Y'Z""", 'd']])
            stmt = stmt.replace("\\'", "''")
            c.execute(stmt)

    c.execute(query)
    res = [[x[0] for x in c.description]]
    res.extend(list(row) for row in c)
    return res
