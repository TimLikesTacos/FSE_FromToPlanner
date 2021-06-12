
from sqlalch import Airport, Assignment

class Planner:
    def __init__ (self, flightpath, assignments):
        self.flightpath = flightpath
        # self.fromassignments = assignments['from']
        # self.toassignments = assignments['to']
        self.assignments = assignments

    # class FromAP:
    #     def __init__(self, from_icao):
    #         self.from_icao = from_icao
    #         self.to_icao = []
    #
    #     class ToAp:
    #         def __init__(self, to_icao, dist):
    #             self.to_icao = to_icao
    #             self.dist = dist
    #
    #     def append(self, to_icao, dist):
    #         self.to_icao.append(self.ToAp(to_icao, dist))
    #
    #     def __iter__(self):
    #         self.iter_ind = 0
    #         return self
    #
    #     def __next__(self):
    #         if self.iter_ind < len(self.to_icao):
    #             x = self.to_icao[self.iter_ind]
    #             self.iter_ind += 1
    #             return x
    #         else:
    #             raise StopIteration

# Calculates best trips from Point A to Point B flights, such as when travelling long distances.
class FromToPlanner (Planner):


    def __init__(self, assignments):
        super(self, assignments)
        self.assignments_from_to_within_fp = self.__calculateFromTo()
        self.distances = self.__calculateDistances()

    # Filters the assignments so that every origin and destination are within the flightpath
    def __calculateFromTo(self):
        airport_titles = [a.icao for a in self.flightpath.airports_in_fp]

        self.assignments = list(
            filter(lambda assign: True if assign.to_icao in airport_titles and assign.from_icao in airport_titles else False, self.fromassignments))
        return self.assignments


