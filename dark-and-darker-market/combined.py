import item_pb2


def read_bytes_from_file(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()

        data = data[8:]

        # print(bytes(data))
        # for byte in data:
        #     if 32 <= byte <= 126:
        #         print(chr(byte), end='')
        #     else:
        #         print(f' 0x{byte:02x}', end=' ')
        # print()

        proto_message = item_pb2.MarketResponse()  # Replace with your actual message class
        proto_message.ParseFromString(data)
        print(proto_message)

        return data


# Example usage
file_path = 'testdata/items_4_full.bin'
data = read_bytes_from_file(file_path)
