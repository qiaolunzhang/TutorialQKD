def write_set(f, elements_list, identifier):
    f.write("set " + identifier + " :=")
    for e in elements_list:
        f.write(" " + e)
    f.write(";\n")


def write_param_one_index(f, row_name, data, identifier):
    f.write("param " + identifier + " :=\n")
    for idx, row in enumerate(row_name):
        f.write(row)
        if type(data[idx]) == list:
            for i in data[idx]:
                f.write(" ")
                f.write(i)
        else:
            f.write(" ")
            f.write(data[idx])
        f.write("\n")

    f.write(";")
    f.write("\n")


def write_param_two_index(f, row_name, column_name, data, identifier):
    f.write("param " + identifier + " :\n")
    for column in column_name:
        f.write(" ")
        f.write(column)
    f.write(" :=")
    f.write("\n")

    for idx, row in enumerate(row_name):
        f.write(row)
        if type(data[idx]) == list:
            for i in data[idx]:
                f.write(" ")
                f.write(i)
        else:
            f.write(" ")
            f.write(data[idx])
        f.write("\n")

    f.write(";")
    f.write("\n")
