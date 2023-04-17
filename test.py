from model import buffer, packet, node

client = node.Node()
server = node.Node()
for i in range(0, 1000):
    b1 = packet.Packet(
        _destination_ip="localhost",
        _destination_port=5000,
        _source_ip="localhost",
        _source_port=5000,
        _squence_num=100,
        _protocol="TCP",
    )
    b2 = packet.Packet(
        _destination_ip="localhost",
        _destination_port=5000,
        _source_ip="localhost",
        _source_port=5000,
        _squence_num=20,
        _protocol="TCP",
    )
    b3 = packet.Packet(
        _destination_ip="localhost",
        _destination_port=5000,
        _source_ip="localhost",
        _source_port=5000,
        _squence_num=4,
        _protocol="TCP",
    )

a.put(b1)
a.put(b2)
a.put(b3)


a.print_queue("squence_num")