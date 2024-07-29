import subprocess
import time
from enum import Enum
from scapy.all import IP, TCP, rdpcap

import item_pb2
from mongoClient import MarketDataClient


class MessageTypes(Enum):
    MARKET_LISTINGS_RES = "Market listings response"
    MARKET_LISTINGS_REQ = "Market listings request"


MESSAGE_PREFIXES = {
    bytes.fromhex("b80d"): MessageTypes.MARKET_LISTINGS_RES,
    bytes.fromhex("b70d"): MessageTypes.MARKET_LISTINGS_REQ,
}

MESSAGE_SCHEMAS = {
    MessageTypes.MARKET_LISTINGS_RES: item_pb2.MarketResponse(),
    MessageTypes.MARKET_LISTINGS_REQ: item_pb2.MarketListingRequest(),
}


def inspect(inputBytes):
    testfile = "testdata/bindata.bin"
    open(testfile, "wb").write(inputBytes)
    command = ["protobuf_inspector", "<", testfile]

    # Run the command
    result = subprocess.run(
        " ".join(command), shell=True, capture_output=True, text=True
    )
    if not "ERROR" in result.stdout:
        # Print the output
        print(inputBytes[:8].hex())
        print(result.stdout)
    else:
        print(result.stdout)


class GameTrafficParser:
    def __init__(self, event_callback):
        self.bytes_to_read = 0
        self.byte_buffer = bytes()
        self.event_callback = event_callback
        self.message_type: MessageTypes = None

        self.packets_received = 0

    def receive(self, packet):
        self.packets_received += 1
        if not (packet.haslayer(IP) and packet.haslayer(TCP)):
            print("Packet has no TCP data")
            return
        byte_data = bytes(packet[TCP].payload)

        if self.bytes_to_read < 0:
            print("Failed: number of bytes to read: = ", self.bytes_to_read)
            self.reset()
            return

        if self.bytes_to_read > 0:
            print("Continuing to read bytes")
            self.byte_buffer += byte_data
            self.bytes_to_read -= len(byte_data)

            if self.bytes_to_read == 0:
                self.publish()
            return

        length_prefix = byte_data[:2]
        flag_prefix = byte_data[2:4]
        type_prefix = byte_data[4:6]
        flag_prefix_2 = byte_data[6:8]
        print(type_prefix.hex())

        print(byte_data[:8])

        if not type_prefix in MESSAGE_PREFIXES:
            print("Message type not known: ", type_prefix.hex())
            inspect(byte_data[8:])
            self.reset()
            return

        self.message_type = MESSAGE_PREFIXES[type_prefix]
        self.bytes_to_read = int.from_bytes(length_prefix, byteorder="little")
        self.byte_buffer += byte_data[8:]
        self.bytes_to_read -= len(byte_data)

        if self.bytes_to_read == 0:
            self.publish()

    def publish(self):
        inspect(self.byte_buffer)
        parsed_data = MESSAGE_SCHEMAS.get(self.message_type)

        # inspect(self.byte_buffer)
        response = parsed_data.ParseFromString(self.byte_buffer)
        self.event_callback(self.message_type, parsed_data)
        self.reset()

    def reset(self):
        print("Resetting")
        self.byte_buffer = bytes()
        self.bytes_to_read = 0
        self.message_type = None


# I'm away from my DnD computer, so I had to do this with a pre-recorded stream of traffic
# If you replace the read from file logic with direct packet sniffing, it should work live
def parse_recorded_stream(pcap_file, server_ip):
    packets = rdpcap(pcap_file)
    packetnum = 0

    for packet in packets:
        packetnum += 1
        print("Packets received: ", packetnum)

        try:

            if packet[IP].src == server_ip:
                server_parser.receive(packet)
            # elif packet[IP].dst == server_ip:
            #     client_parser.receive(packet)

        except Exception as e:
            raise e


def handler(message_type, data):
    print("handling: ", message_type)
    if message_type == MessageTypes.MARKET_LISTINGS_RES:

        for listing in data.listingArray:

            suggested_price = data_client.get_suggested_price(listing)
            if suggested_price != 0:
                print("Suggested price: ", suggested_price)
                print("Actual price: ", listing.price)

            data_client.put_listing(listing)

    if message_type == MessageTypes.MARKET_LISTINGS_REQ:
        print(data)


server_parser = GameTrafficParser(handler)
client_parser = GameTrafficParser(handler)

data_client = MarketDataClient()
data_client.wipe_listings()

# Dark and Darker server IP
server_ip = "52.223.44.23"
pcap_file = "mixed_capture.pcap"
parse_recorded_stream(pcap_file, server_ip)
# 77	23.775890	192.168.4.29	52.223.44.23	TCP	54	64260 → 20206 [ACK] Seq=279 Ack=39379 Win=51120 Len=0	20206
# data_client.show_listings()
