from sqlalch import Assignment


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
    def __init__(self, depart, land, passcap, payloadcap, assignments: [Assignment] = None):
        self.depart = depart
        self.land = land
        self.passcap = passcap
        self.payloadcap = payloadcap    # kilograms
        self.assignments = assignments  # kilograms
        self.current_payload = 0
        self.current_pax = 0

        for a in assignments:
            successful = self.add_assignment(a)
            if not successful:
                raise ValueError('Assignments exceed passenger / weight capacity')

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
                return False

            return True
        else:
            if self.current_payload + assignment.amount > self.payloadcap:
                return False
            return True
