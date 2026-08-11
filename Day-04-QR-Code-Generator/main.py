FORMAT_MASK = 0x5412
FORMAT_GENERATOR = 0x537
QR_SIZE = 21
DATA_CODEWORDS = 19
ERROR_CODEWORDS = 7
MASK_PATTERN = 0


def gf_multiply(left, right):
    result = 0

    while right:
        if right & 1:
            result ^= left

        left <<= 1
        if left & 0x100:
            left ^= 0x11D

        right >>= 1

    return result


def gf_power(base, power):
    result = 1

    for _ in range(power):
        result = gf_multiply(result, base)

    return result


def multiply_polynomials(first, second):
    result = [0] * (len(first) + len(second) - 1)

    for first_index, first_value in enumerate(first):
        for second_index, second_value in enumerate(second):
            result[first_index + second_index] ^= gf_multiply(first_value, second_value)

    return result


def create_generator_polynomial(error_count):
    generator = [1]

    for power in range(error_count):
        generator = multiply_polynomials(generator, [1, gf_power(2, power)])

    return generator


def create_error_codewords(data_codewords, error_count):
    generator = create_generator_polynomial(error_count)
    error_codewords = [0] * error_count

    for codeword in data_codewords:
        factor = codeword ^ error_codewords[0]
        error_codewords = error_codewords[1:] + [0]

        for index in range(error_count):
            error_codewords[index] ^= gf_multiply(generator[index + 1], factor)

    return error_codewords


def text_to_data_codewords(text):
    data = text.encode("utf-8")

    if len(data) > 17:
        raise ValueError("This simple QR generator supports up to 17 UTF-8 bytes.")

    bits = []
    bits.extend([0, 1, 0, 0])
    bits.extend(integer_to_bits(len(data), 8))

    for byte in data:
        bits.extend(integer_to_bits(byte, 8))

    remaining_bits = DATA_CODEWORDS * 8 - len(bits)
    bits.extend([0] * min(4, remaining_bits))

    while len(bits) % 8 != 0:
        bits.append(0)

    codewords = bits_to_codewords(bits)
    padding = [0xEC, 0x11]
    padding_index = 0

    while len(codewords) < DATA_CODEWORDS:
        codewords.append(padding[padding_index % 2])
        padding_index += 1

    return codewords


def integer_to_bits(value, length):
    return [(value >> bit) & 1 for bit in range(length - 1, -1, -1)]


def bits_to_codewords(bits):
    codewords = []

    for start in range(0, len(bits), 8):
        value = 0
        for bit in bits[start:start + 8]:
            value = (value << 1) | bit
        codewords.append(value)

    return codewords


def create_empty_matrix(size):
    modules = [[False for _ in range(size)] for _ in range(size)]
    reserved = [[False for _ in range(size)] for _ in range(size)]
    return modules, reserved


def set_function_module(modules, reserved, row, column, is_dark):
    modules[row][column] = is_dark
    reserved[row][column] = True


def draw_finder_pattern(modules, reserved, top, left):
    for row_offset in range(-1, 8):
        for column_offset in range(-1, 8):
            row = top + row_offset
            column = left + column_offset

            if not (0 <= row < QR_SIZE and 0 <= column < QR_SIZE):
                continue

            inside_finder = 0 <= row_offset <= 6 and 0 <= column_offset <= 6
            border = row_offset in (0, 6) or column_offset in (0, 6)
            center = 2 <= row_offset <= 4 and 2 <= column_offset <= 4
            set_function_module(modules, reserved, row, column, inside_finder and (border or center))


def draw_function_patterns(modules, reserved):
    draw_finder_pattern(modules, reserved, 0, 0)
    draw_finder_pattern(modules, reserved, 0, QR_SIZE - 7)
    draw_finder_pattern(modules, reserved, QR_SIZE - 7, 0)

    for index in range(8, QR_SIZE - 8):
        is_dark = index % 2 == 0
        set_function_module(modules, reserved, 6, index, is_dark)
        set_function_module(modules, reserved, index, 6, is_dark)

    set_function_module(modules, reserved, QR_SIZE - 8, 8, True)
    draw_format_bits(modules, reserved)


def create_format_bits():
    error_level_low = 0b01
    data = (error_level_low << 3) | MASK_PATTERN
    bits = data << 10

    for bit in range(14, 9, -1):
        if (bits >> bit) & 1:
            bits ^= FORMAT_GENERATOR << (bit - 10)

    return ((data << 10) | bits) ^ FORMAT_MASK


def get_bit(value, index):
    return (value >> index) & 1 == 1


def draw_format_bits(modules, reserved):
    bits = create_format_bits()

    for index in range(6):
        set_function_module(modules, reserved, index, 8, get_bit(bits, index))

    set_function_module(modules, reserved, 7, 8, get_bit(bits, 6))
    set_function_module(modules, reserved, 8, 8, get_bit(bits, 7))
    set_function_module(modules, reserved, 8, 7, get_bit(bits, 8))

    for index in range(9, 15):
        set_function_module(modules, reserved, 8, 14 - index, get_bit(bits, index))

    for index in range(8):
        set_function_module(modules, reserved, 8, QR_SIZE - 1 - index, get_bit(bits, index))

    for index in range(8, 15):
        set_function_module(modules, reserved, QR_SIZE - 15 + index, 8, get_bit(bits, index))

    set_function_module(modules, reserved, QR_SIZE - 8, 8, True)


def should_apply_mask(row, column):
    return (row + column) % 2 == 0


def place_data_bits(modules, reserved, codewords):
    bits = []

    for codeword in codewords:
        bits.extend(integer_to_bits(codeword, 8))

    bit_index = 0
    upward = True
    column = QR_SIZE - 1

    while column > 0:
        if column == 6:
            column -= 1

        rows = range(QR_SIZE - 1, -1, -1) if upward else range(QR_SIZE)

        for row in rows:
            for current_column in (column, column - 1):
                if reserved[row][current_column]:
                    continue

                bit = bit_index < len(bits) and bits[bit_index] == 1

                if should_apply_mask(row, current_column):
                    bit = not bit

                modules[row][current_column] = bit
                bit_index += 1

        upward = not upward
        column -= 2


def create_qr_matrix(text):
    modules, reserved = create_empty_matrix(QR_SIZE)
    draw_function_patterns(modules, reserved)

    data_codewords = text_to_data_codewords(text)
    error_codewords = create_error_codewords(data_codewords, ERROR_CODEWORDS)
    place_data_bits(modules, reserved, data_codewords + error_codewords)

    return modules


def save_pbm(modules, filename, scale=10, quiet_zone=4):
    pixel_size = (len(modules) + quiet_zone * 2) * scale

    with open(filename, "w", encoding="ascii") as file:
        file.write("P1\n")
        file.write(f"{pixel_size} {pixel_size}\n")

        for row in range(-quiet_zone, len(modules) + quiet_zone):
            expanded_row = []

            for column in range(-quiet_zone, len(modules) + quiet_zone):
                is_dark = 0 <= row < len(modules) and 0 <= column < len(modules) and modules[row][column]
                expanded_row.extend(["1" if is_dark else "0"] * scale)

            line = " ".join(expanded_row)

            for _ in range(scale):
                file.write(line + "\n")


def save_svg(modules, filename, scale=10, quiet_zone=4):
    image_size = (len(modules) + quiet_zone * 2) * scale

    with open(filename, "w", encoding="utf-8") as file:
        file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        file.write(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{image_size}" '
            f'height="{image_size}" viewBox="0 0 {image_size} {image_size}">\n'
        )
        file.write('<rect width="100%" height="100%" fill="white"/>\n')

        for row, module_row in enumerate(modules):
            for column, is_dark in enumerate(module_row):
                if is_dark:
                    x = (column + quiet_zone) * scale
                    y = (row + quiet_zone) * scale
                    file.write(f'<rect x="{x}" y="{y}" width="{scale}" height="{scale}" fill="black"/>\n')

        file.write("</svg>\n")


def get_output_filename(filename):
    cleaned_filename = filename.strip()

    if not cleaned_filename:
        return "qr_code.svg"

    if "." not in cleaned_filename:
        cleaned_filename += ".svg"

    return cleaned_filename


def save_qr_code(modules, filename):
    if filename.lower().endswith(".pbm"):
        save_pbm(modules, filename)
    else:
        save_svg(modules, filename)


def main():
    print("Simple QR Code Generator")
    print("Enter short text or a short URL. Maximum: 17 UTF-8 bytes.")

    text = input("Text to encode: ").strip()

    if not text:
        print("No text entered. Please run the program again with some text.")
        return

    filename = get_output_filename(input("Output file name (default: qr_code.svg): "))

    try:
        matrix = create_qr_matrix(text)
    except ValueError as error:
        print(error)
        return

    save_qr_code(matrix, filename)
    print(f"Done! Your QR code was saved as {filename}.")
    print("Open the file in a browser and scan it with your phone.")


if __name__ == "__main__":
    main()
