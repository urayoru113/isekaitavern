import base64


class B64:
    @staticmethod
    def encode(**kwargs: str) -> bytes:
        return b";".join(
            [base64.b64encode(k.encode()) + b"," + base64.b64encode(v.encode()) for k, v in kwargs.items()],
        )

    @staticmethod
    def decode(codes: bytes) -> dict[str, str]:
        d = {}
        for k, v in [item.split(b",") for item in codes.split(b";")]:
            d[base64.b64decode(k).decode()] = base64.b64decode(v).decode()
        return d
