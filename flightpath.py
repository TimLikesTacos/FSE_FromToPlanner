from geographiclib.geodesic import Geodesic
from shapely.geometry import Polygon, Point, LineString
from shapely import speedups
import matplotlib.pyplot as plt
import math
import SupportClasses.FromAP as FromAP
from sqlalch import Airport, AirportDistance, Db, Assignment
import sqlalchemy.sql.expression
from filegetter import FileGetter



class FlightPath:
    # Nautical miles to meters
    def nm_m(self, nautical_miles):
        return nautical_miles * 1852

    # Meters to natical miles
    def m_nm(self, meters):
        return meters / float(1852)

    def __init__(self, from_airport, to_airport, width=25, **kwargs):
        self.db = Db()
        self.session = self.db.sessionmaker()
        # Types of airports to exclude.
        self.filegetter = FileGetter()

        # If only one string is passed for exclude, make it a list
        exclude = kwargs.get('exclude', [])
        if type(exclude) == str:
            exclude = list(exclude)

        # Get and import airport data
        print('Getting airports')
        self.filegetter.update_airports(self.db)

        # Get airport data for the selected airports
        self.from_airport: Airport = self.session.query(Airport).get(from_airport)
        self.to_airport: Airport = self.session.query(Airport).get(to_airport)

        if self.from_airport is None:
            raise ValueError(f'{from_airport} is not a valid airport ICAO')
        if self.to_airport is None:
            raise ValueError(f'{to_airport} is not a valid airport ICAO')


        def calc_polygon():
            self.geod = Geodesic.WGS84
            center_path = self.geod.InverseLine(self.from_airport.lat, self.from_airport.lon,
                                                self.to_airport.lat, self.to_airport.lon)
            self.distance = center_path.s13

            def get_bearing_with_offset(distance, offset):
                a = center_path.Position(distance, Geodesic.STANDARD | Geodesic.LONG_UNROLL)['azi2'] + offset
                return a

            left_start = self.geod.Direct(self.from_airport.lat, self.from_airport.lon, get_bearing_with_offset(0, -115), self.width)
            left_end = self.geod.Direct(self.to_airport.lat, self.to_airport.lon, get_bearing_with_offset(center_path.s13, -65),
                                        self.width)
            right_start = self.geod.Direct(self.from_airport.lat, self.from_airport.lon, get_bearing_with_offset(0, 115), self.width)
            right_end = self.geod.Direct(self.to_airport.lat, self.to_airport.lon, get_bearing_with_offset(center_path.s13, 65),
                                    self.width)

            left_line = self.geod.InverseLine(left_start['lat2'], left_start['lon2'], left_end['lat2'], left_end['lon2'])
            right_line = self.geod.InverseLine(right_start['lat2'], right_start['lon2'], right_end['lat2'],
                                          right_end['lon2'])

            INTERVAL = 1e5  # 100km
            def create_line(line, param):
                points = []
                for i in range(math.ceil(line.s13 / INTERVAL) + 1):
                    pos = min(i * INTERVAL, line.s13)
                    coord = line.Position(pos, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
                    points.append(coord[param])
                return points

            xleft_poly_line = create_line(left_line, 'lat2')
            yleft_poly_line = create_line(left_line, 'lon2')
            xright_poly_line = create_line(right_line, 'lat2')
            yright_poly_line = create_line(right_line, 'lon2')
            xcenter = create_line(center_path, 'lat2')
            ycenter = create_line(center_path, 'lon2')


            for r in reversed(xright_poly_line):
                xleft_poly_line.append(r)
            for r in reversed(yright_poly_line):
                yleft_poly_line.append(r)

            speedups.disable()
            ptuples = [(xleft_poly_line[i], yleft_poly_line[i]) for i in range(len(xleft_poly_line))]
            string = LineString(ptuples)
            ctuples = [(xcenter[i], ycenter[i]) for i in range(len(xcenter))]
            return LineString(ctuples), Polygon(string)

        self.width = self.nm_m(width)

        self.path, self.poly = calc_polygon()

        #Find airports that are in the flight area, except ones that match the type passed in kwargs
        airports = self.session.query(Airport).filter(~Airport.type.in_(exclude)).all()
        self.airports = [airport for airport in airports if self.poly.contains(Point(airport.lat, airport.lon))]
        self.airport_names = [airport.icao for airport in self.airports]
        print(f'Flight path loaded with {len(self.airports)} airports in the selected area')



    def get_poly(self):
        return self.poly

    def calc_dist_from_start (self, airport):
        return self.geod.InverseLine(self.from_airport.lat, self.from_airport.lon, airport.lat, airport.lon).s13

    def calc_between_airports(self, port1, port2) -> AirportDistance:
        if port1 == port2:
            return AirportDistance(port1.icao, port2.icao, 0, 0)
        # Get from database
        res = self.session.query(AirportDistance).filter(AirportDistance.from_airport == port1, AirportDistance.to_airport == port2).first()
        if res:
            return res

        # If not in database, calculate and add.  This lets the DB act as a cache and does not require populating the
        # database with all possible combinations at once.
        else:
            line = self.geod.InverseLine(port1.lat, port1.lon, port2.lat, port2.lon)
            bearing = line.Position(0, Geodesic.STANDARD | Geodesic.LONG_UNROLL)['azi2']
            distance = AirportDistance(port1.icao, port2.icao, self.m_nm(line.s13), bearing)
            self.session.add(distance)
            self.session.commit()

            return distance


    # def airports_in(self, airports=None):
    #     if airports is None:
    #         return self.airports_in_fp
    #     # inside = {}
    #     # for airport in airports:
    #     #     if self.poly.contains(Point(airport.lat, airport.lon)):
    #     #         dist = self.calc_dist_from_start(airport)
    #     #         inside[airport] = dist
    #     # self.airports_in_fp = inside
    #     airports = [airport for airport in airports if self.poly.contains(Point(airport.lat, airport.lon))]
    #     for airport in airports:
    #         if self.poly.contains(Point(airport.lat, airport.lon)):
    #

    def calculate_airport_distances(self, db=None):
        self.airport_distances = []
        if db is None:
            # Calculate ranges for each airport in the flightpath
            for port1 in self.airports_in_fp:
                d1 = FromAP()
                for port2 in self.airports_in_fp:
                    if port1 == port2:
                        continue
                    dist = self.calc_between_airports(port1, port2)
                    d1.append(port2.icao, dist)
                self.airport_distances.append(d1)


        else:
            session = db.sessionmaker()
            self.airport_distances = session.query(AirportDistance)\
                .filter(AirportDistance.from_icao.in_(self.airports_in_fp),
                        AirportDistance.to_icao.in_(self.airports_in_fp))
            need_to_calc = set(self.airports_in_fp) - set(self.airport_distances['from'])


    def add_assignments(self):
        self.filegetter.update_to_assignments(self.airports, self.db)
        assignments = self.session.query(Assignment).all()

        # At this point, this is all assignments TO airports in the FP.  There may be some that are not in the flight path.

        self.assignments = [assign for assign in assignments if assign.from_icao in self.airport_names]



    def plot(self, plt, **kwargs):

        x, y = self.poly.exterior.xy
        cx, cy = self.path.xy
        plt.plot(y, x)
        plt.plot(cy, cx)

        plt.plot(self.from_airport.lon, self.from_airport.lat, marker='X')
        plt.text(self.from_airport.lon, self.from_airport.lat, self.from_airport.icao)

        plt.plot(self.to_airport.lon, self.to_airport.lat, marker='X')
        plt.text(self.to_airport.lon, self.to_airport.lat, self.to_airport.icao)

        include_airports = kwargs.get('include_airports')
        if include_airports:
            for port in self.airports:
                plt.plot(port.lon, port.lat, marker='o')

        return plt
