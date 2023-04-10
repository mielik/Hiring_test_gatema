import logging
import re
import sys

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s, %(levelname)s, %(message)s",
)

FILENAME = "D327971_fc1.i"
WRITE_FILE = "cnc.txt"
Y_CONSTANT = 10
X_CONSTANT_MORE_THAN = 50


def read(filename):
    """Read the G-code file."""
    with open(filename, "r") as f:
        lines = f.readlines()
    return lines


def extract_coordinates(lines):
    """Extract valid coordinates."""
    list_coordinates = []
    start = False
    for line_number, line in enumerate(lines):
        if line.startswith("%%"):
            logging.info(f"Found format of G-file: {line.replace('%%', '')}")
        if all(c in line for c in ["X", "Y", "T"]):
            start = True
        if start:
            if line == "\n" or line == "$":
                logging.info(f"The end of coordinate data: {line_number}")
                break
            if all(c in line for c in ["X", "Y", "T"]) or all(
                c in line for c in ["X", "Y"]
            ):
                if not line.startswith("X"):
                    raise ValueError(f"Coordinate must start with X: {line}")
                list_coordinates.append(line)
            else:
                raise ValueError(f"Invalid coordinate format: {line}")
    return list_coordinates


def get_coordinates(list_coordinates):
    """Split the line into its components"""
    list_split_coordinates = []
    # Split the line into its components
    for coordinate in list_coordinates:
        split_coordinate = re.split(r"X|Y|T|\n", coordinate)
        while "" in split_coordinate:
            split_coordinate.remove("")
        list_split_coordinates.append(split_coordinate)
    return list_split_coordinates


def parse_coordinate(list_split_coordinates):
    """Parsing data of tool number, x and y coordinates."""
    data_structure = {}
    tool_number = None
    for coordinate in list_split_coordinates:
        coordinate_dict = {}
        try:
            x_coordinate = float(coordinate[0])
            y_coordinate = float(coordinate[1])
        except (ValueError, IndexError):
            raise ValueError(f"Not parseable data {coordinate}")
        # If we find 3 numbers, that means that it is a new key
        if len(coordinate) == 3:
            try:
                tool_number = int(coordinate[2])
            except ValueError:
                raise ValueError(
                    f"Tool number cant be parsed to integer: {coordinate[2]}"
                )
            if 1 > tool_number > 99:
                raise ValueError(
                    "Tool number in format 5000 must be in range 1 to 99."
                )
            data_structure[tool_number] = []
        coordinate_dict = edit_y_coordinate(
            x_coordinate,
            y_coordinate,
            coordinate_dict
        )
        if tool_number is None:
            raise ValueError("Missing tool number")
        data_structure[tool_number].append(coordinate_dict)
    return data_structure


def edit_y_coordinate(x_coordinate, y_coordinate, coordinate_dict):
    """If x more than constant, add to y another constant."""
    if x_coordinate > X_CONSTANT_MORE_THAN:
        coordinate_dict["X"] = x_coordinate
        coordinate_dict["Y"] = y_coordinate + Y_CONSTANT
    else:
        coordinate_dict["X"] = x_coordinate
        coordinate_dict["Y"] = y_coordinate
    return coordinate_dict


def sort_coordinates(data_structure):
    """Sort coordinates by tool value."""
    sorted_dictionary = dict(sorted(data_structure.items()))
    return sorted_dictionary


def max_and_min_x_and_y_value(sorted_dictionary):
    """Print min and max of x and y values."""
    list_of_x_values = []
    list_of_y_values = []
    for coordinates in sorted_dictionary.values():
        for values_of_coordinates in coordinates:
            values_of_x = values_of_coordinates.get("X")
            values_of_y = values_of_coordinates.get("Y")
            list_of_x_values.append(values_of_x)
            list_of_y_values.append(values_of_y)
    max_x, min_x = max(list_of_x_values), min(list_of_x_values)
    max_y, min_y = max(list_of_y_values), min(list_of_y_values)
    return max_x, min_x, max_y, min_y


def save_header(lines):
    """Save header block."""
    for i, line in enumerate(lines):
        if all(c in line for c in ["X", "Y", "T"]):
            end_header_block = i
            break
    header_block = lines[:end_header_block]
    header_block_string = "".join(header_block)
    return header_block_string


def save_footer(lines):
    """Save footer block."""
    for i, line in enumerate(lines):
        if all(c in line for c in ["$"]):
            start_footer_block = i
            break
    footer_block = lines[start_footer_block:]
    footer_block_string = "".join(footer_block)
    return footer_block_string


def unpack_sorted_dictionary(sorted_dictionary):
    """Unpacking data structure and converting to string data."""
    converted = ""
    for tool_number, list_dictionary_of_coordinates in sorted_dictionary.items():
        for i, dictionary in enumerate(
            list_dictionary_of_coordinates
        ):
            string_coordinates = (
                "X"
                + "{:.3f}".format(dictionary["X"])
                + "Y"
                + "{:.3f}".format(dictionary["Y"])
            )
            if i == 0:
                converted += string_coordinates + "T0" + str(tool_number) + "\n"
            else:
                converted += string_coordinates + "\n"
    return converted


def create_new_file_with_edited_values(header_block, converted, footer_block):
    """Create new file with edited and sorted values."""
    with open(WRITE_FILE, "w") as f:
        f.write(header_block + converted + "\n" + footer_block)


def print_max_min_x_y(max_x, min_x, max_y, min_y):
    """Print min and max of x and y values."""
    print(f"Min_X: {min_x}")
    print(f"Max_X: {max_x}")
    print(f"Min_Y: {min_y}")
    print(f"Max_Y: {max_y}")


def main():
    """Command line user interface."""
    lines = read(FILENAME)
    extraction = extract_coordinates(lines)
    list_split_coordinates = get_coordinates(extraction)
    data_structure = parse_coordinate(list_split_coordinates)
    sorted_dictionary = sort_coordinates(data_structure)
    arguments = sys.argv
    if arguments[1] == "-funkce1":
        converted = unpack_sorted_dictionary(sorted_dictionary)
        header_block = save_header(lines)
        footer_block = save_footer(lines)
        create_new_file_with_edited_values(
            header_block,
            converted,
            footer_block
        )
    elif arguments[1] == "-funkce2":
        max_x, min_x, max_y, min_y = max_and_min_x_and_y_value(sorted_dictionary)
        print_max_min_x_y(max_x, min_x, max_y, min_y)
    else:
        raise ValueError(f"Invalid argument: {arguments[1]}")


if __name__ == "__main__":
    main()
