class Bytes:
    def __init__(self, data):
        self.data = int(data)
        if not -128 <= self.data <= 127:
            raise TypeError("")
