from src.support.sqlalch import Assignment
from src.support.util import log



WEIGHT_OF_PASSENGER = 77   # kilograms

def room_avail(payloadcap, passcap, assignment: Assignment) -> bool:
    # unit type is either 'passengers' or 'kg'
    if assignment.unit_type == 'passengers':
        weight_to_add = assignment.amount * WEIGHT_OF_PASSENGER
        if weight_to_add > payloadcap or \
                assignment.amount > passcap:
            return False

        return True
    else:
        if assignment.amount > payloadcap:
            return False
        return True
    
class Leg:
    def __init__(self, passcap, payloadcap, assignments: [Assignment] = None, **kwargs):
        if kwargs.get('depart'):
            self.depart = kwargs['depart']
        else:
            self.depart = None

        if kwargs.get('land'):
            self.land = kwargs['land']
        else:
            self.land = None

        self.passcap = passcap
        self.payloadcap = payloadcap    # kilograms
        self.assignments = assignments  # kilograms
        self.current_payload = 0
        self.current_pax = 0

        if assignments:
            for a in assignments:
                successful = self.add_assignment(a)
                if not successful:
                    raise ValueError('Assignments exceed passenger / weight capacity')
        else:
            self.assignments = []

    def __format__(self, format_spec):
        the_str = f'{"": {format_spec}}Leg\n' \
                  f'{"": {format_spec}}Depart: {self.depart.icao}\n{"": {format_spec}}Land: {self.land.icao}\n' \
                  f'{"": {format_spec}}Number of Passengers: {self.current_pax}' \
                  f'\n{"": {format_spec}}Payload: {self.current_payload}'
        if len(format_spec) > 1 and format_spec[0] == '<':
            justify = int(format_spec[1:])
        else:
            justify = 0
        justify += 4
        for assignment in self.assignments:
            the_str += f'\n{assignment:{f"<{justify}"}}'

        return the_str

    # Adds cargo load to payload, if capable.  Returns true if within capacity, false if not.
    def add_cargo(self, cargo_weight):
        # Check if added weight will exceed current capacity levels
        if self.payloadcap - self.current_payload < cargo_weight:
            return False

        self.current_payload += cargo_weight
        return True

    def remove_cargo(self, cargo_weight):
        self.current_payload -= cargo_weight

    def remove_pax(self, number_of_passengers):
        self.current_payload -= number_of_passengers * WEIGHT_OF_PASSENGER
        self.current_pax -= number_of_passengers

    def add_pax(self, number_of_passengers):
        # Check if pass cap or weight cap will be exceeded
        if self.passcap - self.current_pax < number_of_passengers:
            return False

        if self.add_cargo(number_of_passengers * WEIGHT_OF_PASSENGER):
            self.current_pax += number_of_passengers
            return True

        else:
            return False

    def add_assignment(self, to_add: Assignment) -> bool:
        if not self.room_avail(to_add):
            return False
        self.assignments.append(to_add)
        if to_add.unit_type == 'passengers':
            self.add_pax(to_add.amount)
        else:
            self.add_cargo(to_add.amount)
        return True

    def remove_assignment(self, to_remove: Assignment):
        self.assignments.remove(to_remove)
        if to_remove.unit_type == 'passengers':
            self.remove_pax(to_remove.amount)
        else:
            self.remove_cargo(to_remove.amount)


    def room_avail(self, assignment: Assignment) -> bool:
        # unit type is either 'passengers' or 'kg'
        if assignment.unit_type == 'passengers':
            weight_to_add = assignment.amount * WEIGHT_OF_PASSENGER
            if self.current_payload + weight_to_add > self.payloadcap or \
                    self.current_pax + assignment.amount > self.passcap:
                log.debug(f'Insufficent capacity: {self.current_pax, self.current_payload}')
                return False

            return True
        else:
            if self.current_payload + assignment.amount > self.payloadcap:
                return False
            return True

    def set_destination_to_shortest(self):
        if self.assignments is None:
            return self
        if len(self.assignments) == 0:
            self.land = self.depart
            return self

        _sorted = sorted(self.assignments, key=lambda a: a.dist_bear.distance)
        shortest = _sorted[0]
        self.land = shortest.to_airport
        return self

    # Creates a new leg and deep copies all assignments except those whose destination
    # was the landing location for the previous leg
    def land_disembark(self):
        new_leg = Leg(self.passcap, self.payloadcap, depart=self.land)
        # Transfer assignments that do not terminate at the previous leg arrival airport
        for a in self.assignments:
            if a.to_airport != self.land:
                new_leg.add_assignment(a)

        return new_leg