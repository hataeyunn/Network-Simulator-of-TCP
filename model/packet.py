class Packet:
    """
    Attributes:
        [송신자 IP 주소, 송신자 포트 번호], [수신자 IP 주소, 수신자 포트 번호], 시퀀스 번호, 프로토콜 버전, 플래그 (ACK)

    Methods:

    """

    def __init__(
        self,
        _destination_ip: str,
        _destination_port: int,
        _source_ip: str,
        _source_port: int,
        _squence_num: int,
        _protocol: str,
        _is_ack: bool = False,
        _ack_num: int = -1,
    ) -> None:
        self.header = {
            "destination": [_destination_ip, _destination_port],
            "source": [_source_ip, _source_port],
            "squence_num": _squence_num,
            "protocol": _protocol,
            "is_ack": _is_ack,
            "ack_num": _ack_num,
        }

    def set_ack_status(self, _is_ack: bool = True) -> None:
        self.header["is_ack"] = _is_ack

    def get_is_ack(
        self,
    ) -> bool:
        if self.header["is_ack"] is True and self.header["ack_num"] != -1:
            return True
        return False

    def set_ack_num(self, _ack_num: int) -> None:
        self.header["ack_num"] = _ack_num

    def get_destination_address(
        self,
    ) -> tuple:
        return tuple(self.header["destination"][0], self.header["destination"][1])

    def get_source_address(
        self,
    ) -> tuple:
        return tuple(self.header["source"][0], self.header["source"][1])

    def get_protocol(
        self,
    ) -> str:
        return self.header["protocol"]

    def get_ack_num(
        self,
    ) -> int:
        return self.header["ack_num"]
