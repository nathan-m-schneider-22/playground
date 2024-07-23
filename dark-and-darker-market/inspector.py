from scapy.all import rdpcap, TCP, IP
import item_pb2


# I'm away from my DnD computer, so I had to do this with a pre-recorded stream of traffic
# If you replace the read from file logic with direct packet sniffing, it should work live
def parse_recorded_stream(pcap_file, ip_address):
    packets = rdpcap(pcap_file)
    for packet in packets:

        if (
            packet.haslayer(IP)
            and packet[IP].src == ip_address
            and packet.haslayer(TCP)
        ):

            try:
                data = bytes(packet[TCP].payload)

            except:
                pass


# Dark and Darker server IP
ip_address = "52.223.44.23"
pcap_file = "mixed_capture.pcap"
parse_recorded_stream(pcap_file, ip_address)
