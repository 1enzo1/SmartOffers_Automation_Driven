class CustomerBuilder:

    def __init__(self):
        self.data = {}

    def with_msisdn(self, msisdn):
        self.data["msisdn"] = msisdn
        return self

    def with_profile(self, profile):
        self.data["profile"] = profile
        return self

    def ativo(self):
        self.data["account_state"] = "1"
        return self

    def pre_pago(self):
        self.data["type"] = "PRE"
        return self

    def pos_pago(self):
        self.data["type"] = "POS"
        return self

    def build(self):
        return self.data