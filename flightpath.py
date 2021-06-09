from geographiclib.geodesic import Geodesic
from shapely.geometry import Polygon, Point, LineString
from shapely import speedups
import matplotlib.pyplot as plt
import math


class FlightPath:
    def __init__(self, from_airport, to_airport, width=25):
        def nm_m(nautical_miles):
            return nautical_miles * 1852

        def calc_polygon (self):
            self.geod = Geodesic.WGS84
            center_path = self.geod.InverseLine(self.start_lat, self.start_lon, self.end_lat, self.end_lon)
            self.distance = center_path.s13

            def get_bearing_with_offset(distance, offset):
                a =  center_path.Position(distance, Geodesic.STANDARD | Geodesic.LONG_UNROLL)['azi2'] + offset
                return a

            left_start = self.geod.Direct(self.start_lat, self.start_lon, get_bearing_with_offset(0, -115), self.width)
            left_end = self.geod.Direct(self.end_lat, self.end_lon, get_bearing_with_offset(center_path.s13, -65),
                                   self.width)
            right_start = self.geod.Direct(self.start_lat, self.start_lon, get_bearing_with_offset(0, 115), self.width)
            right_end = self.geod.Direct(self.end_lat, self.end_lon, get_bearing_with_offset(center_path.s13, 65),
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

        if isinstance(from_airport, dict):
            self.start_lat = from_airport['lat']
            self.start_lon = from_airport['lon']
            self.start_icao = None
            if from_airport.get('icao'):
                self.start_icao = from_airport['icao']
        else:
            self.start_lat = from_airport.lat
            self.start_lon = from_airport.lon
            self.start_icao = from_airport.icao
            
        if isinstance(to_airport, dict):
            self.end_lat = to_airport['lat']
            self.end_lon = to_airport['lon']
            self.end_icao = None
            if to_airport.get('icao'):
                self.end_icao = to_airport['icao']
        else:
            self.end_lat = to_airport.lat
            self.end_lon = to_airport.lon
            self.end_icao = to_airport.icao

        self.width = nm_m(width)

        self.path, self.poly = calc_polygon(self)


    def get_poly(self):
        return self.poly

    def calc_dist_from_start (self, airport):
        return self.geod.InverseLine(self.start_lat, self.start_lon, airport.lat, airport.lon).s13

    def airports_in(self, airports):
        inside = {}
        for airport in airports:
            if self.poly.contains(Point(airport.lat, airport.lon)):
                dist = self.calc_dist_from_start(airport)
                inside[airport] = dist

        return inside

    def print(self):
        x, y = self.poly.exterior.xy
        cx, cy = self.path.xy
        plt.plot(y, x)
        plt.plot(cy, cx)

        if self.start_icao:
            plt.plot(self.start_lon, self.start_lat, marker='o', label='some')
            plt.text(self.start_lon, self.start_lat, self.start_icao)

        if self.end_icao:
            plt.plot(self.end_lon, self.end_lat, marker='o', label='some')
            plt.text(self.end_lon, self.end_lat, self.end_icao)

        plt.show()
