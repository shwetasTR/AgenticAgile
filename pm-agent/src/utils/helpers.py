def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)

def format_data(data):
    return str(data).strip()

def validate_file_extension(file_path, valid_extensions):
    if not any(file_path.endswith(ext) for ext in valid_extensions):
        raise ValueError(f"Invalid file extension for {file_path}. Expected one of {valid_extensions}.")