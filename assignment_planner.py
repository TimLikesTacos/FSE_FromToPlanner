from sqlalch import Airport, Assignment, AirportDistance
from SupportClasses.leg import Leg, room_avail
from itertools import takewhile
from copy import deepcopy
from util import log


class __Planner:

    def __init__(self, flightpath, weight_capacity, passenger_capacity):
        self.flightpath = flightpath
        self.weightcap = weight_capacity
        self.passcap = passenger_capacity
        # filter assignments that only originate and terminate in the flightpath, along with max leg length and capacity
        self.assignments = self.filter_assignments()
        self.legs: [Leg] = []
        self.total_payout = 0

    def filter_assignments(self):
        MIN_PAY = 200
        assign = filter(
            lambda a: room_avail(self.weightcap, self.passcap, a) and a.pay > MIN_PAY, self.flightpath.assignments) \
                # self.flightpath.calc_between_airports(a.from_airport, a.to_airport).distance < self.max_leg and


        return list(assign)

    def __format__(self, format_spec):
        if format_spec == "":
            format_spec = '<0'

        the_str = f'{"": {format_spec}}{self.__class__}:\n' \
                  f'{"": {format_spec}}From: {self.flightpath.from_airport.icao}, To: {self.flightpath.to_airport.icao}\n' \
                  f'{"": {format_spec}}Weight Capacity: {self.weightcap}\n' \
                  f'{"": {format_spec}}Passenger Capacity: {self.passcap}\n'

        if len(format_spec) > 1 and format_spec[0] == '<':
            justify = int(format_spec[1:])
        else:
            justify = 0

        justify += 4
        for leg in self.legs:
            the_str += f'\n{leg:{f"<{justify}"}}'

        the_str += f'\n\n{"": {format_spec}}Total Payout : {self.total_payout}'

        return the_str




# Calculates best trips from Point A to Point B flights, such as when travelling long distances.
class FromToPlanner(__Planner):

    def __init__(self, flightpath, weight_capacity, passenger_capacity):
        super(FromToPlanner, self).__init__(flightpath, weight_capacity, passenger_capacity)
        # Assignments sorted by closest to departure first

        self.distance_from_start = sorted(
            [x for x in self.assignments],
            key=lambda a: self.flightpath.calc_between_airports(self.flightpath.from_airport, a.from_airport).distance)

        self.__calc_greedy()


    # Gets the best using greedy method (largest payout available takes priority)
    def __calc_greedy(self):
        if len(self.distance_from_start) == 0:
            no_assignments = Leg(self.passcap, self.weightcap, depart=self.flightpath.from_airport)
            no_assignments.land = self.flightpath.to_airport
            self.legs.append(no_assignments)

        # prev_airport will be used to construct the legs
        prev_airport = self.flightpath.from_airport
        incoming_leg = Leg(self.passcap, self.weightcap, depart=self.flightpath.from_airport)
        incoming_leg.set_destination_to_shortest()

        log.debug(self.flightpath.from_airport.icao)

        while len(self.distance_from_start) > 0:
            # Get the closest assignment
            closest = [self.distance_from_start.pop(0)]

            # While at the airport with the closest assignment, get other assignments at the same airport
            while len(self.distance_from_start) > 0 and \
                    self.distance_from_start[0].from_icao == closest[0].from_icao:
                log.debug(f'Assignment is same as closest: {self.distance_from_start[0].from_icao} and {closest[0].from_icao}')
                closest.append(self.distance_from_start.pop(0))

            # Now sort to get the highest paying job from this airport
            closest.sort(key=lambda a: a.pay, reverse=True)

            # Create an empty leg if travel needed from current airport to the airport with the assignment
            if closest[0].from_airport != prev_airport:

                # The destination of this empty leg is the location of the closest assignment
                incoming_leg.land = closest[0].from_airport
                self.legs.append(incoming_leg)
                # Complete the empty leg, and set up for the next leg.
                incoming_leg = incoming_leg.land_disembark()

            # Keep adding the next highest paying assignment if room allows
            while len(closest) > 0:
                next_assignment = closest.pop(0)
                if incoming_leg.add_assignment(next_assignment):
                    # Add pay to total
                    self.total_payout += next_assignment.pay
                    log.debug(
                        f'Assignment from {next_assignment.from_icao} to {next_assignment.to_icao} paying {next_assignment.pay} has been added')
                else:
                    log.debug(
                        f'Assignment from {next_assignment.from_icao} to {next_assignment.to_icao} paying {next_assignment.pay} cannot be added')

            # Find the shortest assignment in the leg.  This will be the destination for the first leg.
            incoming_leg.set_destination_to_shortest()
            # Add this leg to the planner
            self.legs.append(incoming_leg)

            # Adjust the incoming leg for the next trip
            if incoming_leg.land == self.flightpath.to_airport:
                # If arrived at destination, end the planner
                break
            incoming_leg = incoming_leg.land_disembark()
            prev_airport = incoming_leg.depart

            # remove all available assignments that get flown over
            distance_at_landing = self.flightpath.calc_dist_from_start(incoming_leg.depart)
            for a in self.distance_from_start:
                if self.flightpath.calc_dist_from_start(a.from_airport) < distance_at_landing:
                    self.distance_from_start.remove(a)

        # If not at the final destination, complete the trip
        if incoming_leg.depart != self.flightpath.to_airport:
            incoming_leg.land = self.flightpath.to_airport
            self.legs.append(incoming_leg)


