def sql_to_pydantic(sql):
    lines = [line.strip() for line in sql.split('\n') if line.strip() and not line.strip().startswith(("CREATE", ")"))]
    table_name = sql.split('CREATE TABLE')[-1].split('(')[0].strip()
    py_representation = f"class {table_name}(BaseModel):"
    for line in lines:
        parts = line.split()
        col_name = parts[0]
        col_type = parts[1]
        if "AUTOINCREMENT" in col_type or "INT" in col_type:
            py_type = "int"
        elif "TEXT" in col_type:
            py_type = "str"
        elif "BOOLEAN" in col_type:
            py_type = "bool"
        elif "DATE" in col_type:
            py_type = "date"
        elif "TIME" in col_type:
            py_type = "time"
        elif "DECIMAL" in col_type:
            py_type = "float"
        else:
            py_type = "str" 
        if "NOT NULL" in line:
            py_representation += f"\n    {col_name}: {py_type}"
        else:
            py_representation += f"\n    {col_name}: Optional[{py_type}]"
        # if col_name == 'ID':
        py_representation += f" = None"
    return py_representation