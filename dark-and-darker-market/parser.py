from scapy.all import rdpcap, TCP, IP
import item_pb2
import subprocess


MESSAGE_PREFIXES = {}


def inspect(inputBytes):

    testfile = "testdata/bindata.bin"
    open(testfile, "wb").write(inputBytes[8:])
    command = ["protobuf_inspector", "<", testfile]

    # Run the command
    result = subprocess.run(
        " ".join(command), shell=True, capture_output=True, text=True
    )
    if not "ERROR" in result.stdout:
        # Print the output
        print(inputBytes[:8].hex())

        print(result.stdout[:400])


# I'm away from my DnD computer, so I had to do this with a pre-recorded stream of traffic
# If you replace the read from file logic with direct packet sniffing, it should work live
def parse_recorded_stream(pcap_file, ip_address):
    packet_buffer = []
    packets = rdpcap(pcap_file)
    parsed_responses = 0
    packetnum = 0

    for packet in packets:
        packetnum += 1

        if (
            packet.haslayer(IP)
            and packet[IP].src == ip_address
            and packet.haslayer(TCP)
        ):

            bytedata = bytes(packet[TCP].payload)
            # Listings can get split between multiple TCP packets, this is a messy workaround
            packet_buffer.append(packet)
            ascii_data = bytedata.decode("ascii", errors="ignore")

            print("===================")
            print(packetnum, packet[TCP].seq)

            print(bytedata[:8].hex())
            print(ascii_data[:8])
            print(len(bytedata))

            packet_buffer.sort(key=lambda pkt: pkt.time)

            for start_packet_index in range(len(packet_buffer)):

                bytes_buffer = [bytes(p[TCP].payload) for p in packet_buffer]
                combined_bytes = b"".join(bytes_buffer[start_packet_index:])

                try:

                    # inspect(combined_bytes)

                    parsed_listings = item_pb2.MarketResponse()

                    # first 8 bytes are specific to the DnD game client, and should be ignore
                    # Later work should go into deciphering these prefixes
                    parsed_listings.ParseFromString(combined_bytes[8:])
                    # print(parsed_listings)
                    parsed_responses += 1

                    packet_buffer = []
                    break

                except:
                    pass
    print("Parsed listings: ", parsed_responses)


# Dark and Darker server IP
ip_address = "52.223.44.23"
pcap_file = "mixed_capture.pcap"
parse_recorded_stream(pcap_file, ip_address)
