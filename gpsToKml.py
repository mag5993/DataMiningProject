#!/usr/bin/env python3

# gpsToKml.py
#                               OR any other Gps File V
#To run: python gpsToKml.py 2025_05_01__145019_gps_file.txt output.kml

#This file attempts to cover the 1st requirement:
#   Read GPS file
#   Parse NMEA sentences ($GPRMC)
#   Convert NMEA lat/lon
#   Emit a simple KML path, decorated with markers for stops and left turns

# Authors: Dylan Thumann and Marissa Gomes

import sys
import math
import datetime

import numpy as np

## PART 1: read in the GPS file, parse the lines, and emit a KML file
# TrackPoint object (lat, lon, speed, time)

class TrackPoint:
    def __init__(self, lat, lon, speed_knots=0.0, timestamp=None):
        self.lat = lat
        self.lon = lon
        self.speed_knots = speed_knots
        self.timestamp = timestamp


# NMEA coordinate conversion

def nmea_coord_to_decimal(value_str, direction):
    
    # Convert NMEA coordinate (ddmm.mmmm / dddmm.mmmm)
    # into decimal degrees.
    
    if not value_str:
        return None

    value_str = value_str.strip()
    if "." in value_str:
        integer_part, frac_part = value_str.split(".")
    else:
        integer_part, frac_part = value_str, "0"

    # Determine degree digits
    if direction in ("N", "S"):
        deg_digits = 2
    else:
        deg_digits = 3

    if len(integer_part) <= deg_digits:
        return None

    degrees = int(integer_part[:deg_digits])
    minutes = float(integer_part[deg_digits:] + "." + frac_part)

    decimal = degrees + minutes / 60.0

    if direction in ("S", "W"):
        decimal *= -1.0

    return decimal


def parse_datetime_from_rmc(time_str, date_str):
    
    # Convert RMC time+date fields into a Python datetime.
    
    try:
        hour = int(time_str[0:2])
        minute = int(time_str[2:4])
        second = int(time_str[4:6])

        day = int(date_str[0:2])
        month = int(date_str[2:4])
        year = int(date_str[4:6]) + 2000

        return datetime.datetime(year, month, day, hour, minute, second)
    except:
        return None



# Requirement 1: Parse GPS file


def parse_nmea_file(filename):
    
    # Read the GPS file and parse ONLY $GPRMC lines.
    # No stop detection, no turn analysis.
    
    points = []

    with open(filename, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("$GPRMC") or line.startswith("$GNRMC"):
                parts = line.split(",")
                if len(parts) < 10:
                    continue

                status = parts[2]
                if status != "A":
                    continue

                lat = nmea_coord_to_decimal(parts[3], parts[4])
                lon = nmea_coord_to_decimal(parts[5], parts[6])
                if lat is None or lon is None:
                    continue

                try:
                    speed_knots = float(parts[7]) if parts[7] else 0.0
                except:
                    speed_knots = 0.0

                timestamp = parse_datetime_from_rmc(parts[1], parts[9])
                points.append(TrackPoint(lat, lon, speed_knots, timestamp))

    return points

def checkStraight(a, b, c, tolerance = pow(10, -9.5), max_angle_cos_threshold = 0.999):
    ux = float(b[0]) - float(a[0])
    uy = float(b[1]) - float(a[1])
    vx = float(c[0]) - float(b[0])
    vy = float(c[1]) - float(b[1])   

    # magnitudes
    mag_u_sq = ux*ux + uy*uy
    mag_v_sq = vx*vx + vy*vy
    
    # if either vectors
    if mag_u_sq < tolerance or mag_v_sq < tolerance:
        return False
    
    # check colinearity
    wedge = ux * vy - uy * vx
    is_collinear = abs(wedge) < tolerance

    # check tight direction
    dot_product = ux * vx + uy * vy

    # cosine of angle between vectors
    mag_u = math.sqrt(mag_u_sq)
    mag_v = math.sqrt(mag_v_sq)

    # dot = cosine of angle
    cos_theta = dot_product / (mag_u * mag_v)

    # check if angle is very small
    is_tightly_aligned = cos_theta > max_angle_cos_threshold
    
    return is_collinear and is_tightly_aligned

# performs data cleaning on the points array and returns it
def clean(points):
    start_parked = 0
    clean_points = []
    minspeed = 5

    if not points:
        return []

    # Remove parked points at the end
    end_idx = len(points) - 1
    while end_idx >= 0 and points[end_idx].speed_knots <= minspeed:
        end_idx -= 1

    # nothing left?
    if end_idx <= 0:
        return []

    # Walk from start to end_idx, drop parked-before-start+big jumps
    last_kept = None

    for p in range(0, end_idx + 1):
        pt = points[p]

        # ignore starting points where car is parked
        if pt.speed_knots <= minspeed and start_parked == 0:
            continue
        start_parked = 1

        # if we have a previous kept point, check for crazy jumps
        if last_kept is not None:
            if (abs(last_kept.lat - pt.lat) > 0.25 or
                abs(last_kept.lon - pt.lon) > 0.25):
                continue
        if last_kept is not None and p < end_idx:
            a = points[p - 1] 
            axy = (a.lat, a.lon) 
            b = points[p] 
            bxy = (b.lat, b.lon) 
            c = points[p + 1] 
            cxy = (c.lat, c.lon) 
            straight = checkStraight(axy, bxy, cxy) 
            
            if (straight): 
                continue

        clean_points.append(pt)
        last_kept = pt

    return clean_points

# Basic KML output

def write_kml(stops, left_turns, points, output_file, altitude=3):
    
    # Writes ONLY the yellow path LineString.

    with open(output_file, "w", encoding="utf-8") as kml:
        kml.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        kml.write('<kml xmlns="http://www.opengis.net/kml/2.2">\n')
        kml.write('  <Document>\n')
        kml.write('    <name>GPS Route (Requirement 1 Only)</name>\n')

        # Yellow style (line only)
        kml.write('    <Style id="routeStyle">\n')
        kml.write('      <LineStyle>\n')
        kml.write('        <color>ff00ffff</color>\n')
        kml.write('        <width>3</width>\n')
        kml.write('      </LineStyle>\n')
        kml.write('    </Style>\n')

        # yellow marker (left turns)
        kml.write('    <Style id="yellowMarker">\n')
        kml.write('      <IconStyle>\n')
        kml.write('        <scale>1.2</scale>\n')
        kml.write('        <Icon>\n')
        kml.write('          <href>http://maps.google.com/mapfiles/kml/paddle/ylw-circle.png</href>\n')
        kml.write('        </Icon>\n')
        kml.write('      </IconStyle>\n')
        kml.write('      <LabelStyle>\n')
        kml.write('        <color>ff00ffff</color>\n')
        kml.write('        <scale>1.2</scale>\n')
        kml.write('      </LabelStyle>\n')
        kml.write('    </Style>\n')

        # red marker (stops)
        kml.write('    <Style id="redMarker">\n')
        kml.write('      <IconStyle>\n')
        kml.write('        <scale>1.2</scale>\n')
        kml.write('        <Icon>\n')
        kml.write('          <href>http://maps.google.com/mapfiles/kml/paddle/red-circle.png</href>\n')
        kml.write('        </Icon>\n')
        kml.write('      </IconStyle>\n')
        kml.write('      <LabelStyle>\n')
        kml.write('        <color>ff0000ff</color>\n')
        kml.write('        <scale>1.2</scale>\n')
        kml.write('      </LabelStyle>\n')
        kml.write('    </Style>\n')



        # Path placemark
        kml.write('    <Placemark>\n')
        kml.write('      <name>Route</name>\n')
        kml.write('      <styleUrl>#routeStyle</styleUrl>\n')
        kml.write('      <LineString>\n')
        kml.write('        <tessellate>1</tessellate>\n')
        kml.write('        <coordinates>\n')

        for p in points:
            kml.write(f'          {p.lon:.6f},{p.lat:.6f},{altitude}\n')

        kml.write('        </coordinates>\n')
        kml.write('      </LineString>\n')
        kml.write('    </Placemark>\n')

        
        if (len(stops) != 0):
            for s in stops:
                kml.write('  <Placemark>\n')
                kml.write(f'    <name>• </name>\n')
                kml.write(f'    <styleUrl>#redMarker</styleUrl>\n')
                kml.write('    <Point>\n')
                kml.write('        <coordinates>\n')
                kml.write(f'          {s[1]:.6f},{s[0]:.6f},{altitude}\n')
                kml.write('        </coordinates>\n')
                kml.write('    </Point>\n')
                kml.write('  </Placemark>\n')


                
        if (len(left_turns) != 0):
            for l in left_turns:
                kml.write('  <Placemark>\n')
                kml.write(f'    <name>• </name>\n')
                kml.write(f'    <styleUrl>#yellowMarker</styleUrl>\n')
                kml.write('    <Point>\n')
                kml.write('        <coordinates>\n')
                kml.write(f'          {l[1]:.6f},{l[0]:.6f},{altitude}\n')
                kml.write('        </coordinates>\n')
                kml.write('    </Point>\n')
                kml.write('  </Placemark>\n')




        kml.write('  </Document>\n')
        kml.write('</kml>\n')

## PART 2: decorate kml file

# returns a tuple of lists holding coordinates: (stops, left_turns)
def decorate(points):
    print("decorating, points after clean():", len(points))
    stops = []
    stop_sight = []
    left_turns = []
    left_sight = []

    minspeed = 5          # speed threshold for "stopped"
    turn_min_speed = 3    # consider turns even at slow rlling speed

    raw_left_count = 0

    n = len(points)
    if n < 5:
        return [], []

    for i in range(2, n - 2):
        b = points[i]

        # for stop detection
        if b.speed_knots <= minspeed:
            stop_sight.append((b.lat, b.lon))
        elif b.speed_knots > minspeed and len(stop_sight) != 0:
            stop_sight_array = np.array(stop_sight)
            mean_lat, mean_lon = np.mean(stop_sight_array, axis=0)
            stops.append((mean_lat, mean_lon))
            stop_sight.clear()

        # for left turn
        a = points[i - 2]
        c = points[i + 2]

        if b.speed_knots < turn_min_speed:
            left = False
        else:
            axy = (a.lon, a.lat)
            bxy = (b.lon, b.lat)
            cxy = (c.lon, c.lat)
            left = calculateLeft(axy, bxy, cxy)

        if left:
            raw_left_count += 1
            left_sight.append((b.lat, b.lon))
        elif not left and len(left_sight) != 0:
            left_sight_array = np.array(left_sight)
            mean_lat, mean_lon = np.mean(left_sight_array, axis=0)
            left_turns.append((mean_lat, mean_lon))
            left_sight.clear()

    # Flush any remaining stop cluster
    if len(stop_sight) != 0:
        stop_sight_array = np.array(stop_sight)
        mean_lat, mean_lon = np.mean(stop_sight_array, axis=0)
        stops.append((mean_lat, mean_lon))

    # Flush any remaining left-turn cluster
    if len(left_sight) != 0:
        left_sight_array = np.array(left_sight)
        mean_lat, mean_lon = np.mean(left_sight_array, axis=0)
        left_turns.append((mean_lat, mean_lon))

    return stops, left_turns


   

# calculates left turns, return boolean
def calculateLeft(a, b, c, min_sin=0.3, min_segment_length=0.00005):

    ux = float(b[0]) - float(a[0])
    uy = float(b[1]) - float(a[1])
    vx = float(c[0]) - float(b[0])
    vy = float(c[1]) - float(b[1])

    len_u = math.hypot(ux, uy)
    len_v = math.hypot(vx, vy)

    # ignore very small moves
    if len_u < min_segment_length or len_v < min_segment_length:
        return False

    cross = ux * vy - uy * vx
    cross_norm = cross / (len_u * len_v)

    # left turn if positive and large enough
    return cross_norm > min_sin



def moving_duration(points):
    if not points or len(points) < 2:
        return 0
    moving_duration = 0

    for p in range(1, len(points)):
        a = points[p - 1]
        b = points[p]

        if a.timestamp is None or b.timestamp is None:
            continue
        elif a.speed_knots > 2 or b.speed_knots > 2:
            difference = (b.timestamp - a.timestamp).total_seconds()
            moving_duration += difference


    hours, remainder = divmod(moving_duration, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(secs):02}"

def total_duration(points):
    if not points or len(points) < 2:
        return 0

    start = points[0].timestamp
    end = points[-1].timestamp

    duration = (end - start).total_seconds()

    hours, remainder = divmod(duration, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{int(hours):02}:{int(minutes):02}:{int(secs):02}"

# Main program 

def main():
    if len(sys.argv) != 3:
        print("Usage: python gpsToKml.py input.txt output.kml")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]

    points = parse_nmea_file(input_file)
    if not points:
        print("Error: No valid points found.")
        sys.exit(1)
    
    points = clean(points)
    
    stops, left_turns = decorate(points)

    write_kml(stops, left_turns, points, output_file)
    print("Moving duration of journey: ", moving_duration(points))
    print("Total duration of journey: ", total_duration(points))
    print(f"Requirement 1 KML created: {output_file}")


if __name__ == "__main__":
    main()
