from sqlalch import Airport, Assignment, AirportDistance
from SupportClasses.leg import Leg, room_avail


class Planner:

    def __init__(self, flightpath, weight_capacity, passenger_capacity, max_leg):
        # value used by FSE for the weight of a passenger, in kg
        self.flightpath = flightpath
        self.weightcap = weight_capacity
        self.passcap = passenger_capacity
        self.max_leg = max_leg
        self.assignments = self.filter_assignments()


    def filter_assignments(self):
        assign = filter(
            lambda a: self.flightpath.calc_between_airports(a.from_airport, a.to_airport).distance < self.max_leg and
                      room_avail(self.weightcap, self.passcap, a), self.flightpath.assignments)

        return list(assign)

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
class FromToPlanner(Planner):

    def __init__(self, flightpath, weight_capacity, passenger_capacity, max_leg):
        super(FromToPlanner, self).__init__(flightpath, weight_capacity, passenger_capacity, max_leg)
        self.distance_from_start = sorted(
            [self.flightpath.calc_between_airports(self.flightpath.from_airport, x.from_airport) for x in self.assignments],
            key = lambda a: a.distance)

        # self.best_deal = self.calc_greedy()

    # Gets the best using greedy method (largest payout takes priority)
    def calc_greedy(self):
        highest_pay_list = sorted(self.assignments, key=lambda p: p.pay, reverse=True)
        while len(highest_pay_list) > 0:
            top_job = highest_pay_list.pop(0)
            print(top_job.pay)

