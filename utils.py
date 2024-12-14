def extract_number(data_string):
    number = "".join(filter(str.isdigit, data_string))
    return int(number)