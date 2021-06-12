class FromAP:
    def __init__(self, from_icao):
        self.from_icao = from_icao
        self.destinations = []

    class ToAp:
        def __init__(self, to_icao, dist):
            self.to_icao = to_icao
            self.dist = dist

    def append(self, to_icao, dist):
        self.destinations.append(self.ToAp(to_icao, dist))

    def __iter__(self):
        self.iter_ind = 0
        return self

    def __next__(self):
        if self.iter_ind < len(self.destinations):
            x = self.destinations[self.iter_ind]
            self.iter_ind += 1
            return x
        else:
            raise StopIteration