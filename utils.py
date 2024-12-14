def extract_number(data_string):
    # In case this method is called on an int
    if type(data_string) is int:
        return data_string
    number = "".join(filter(str.isdigit, data_string))
    return int(number)