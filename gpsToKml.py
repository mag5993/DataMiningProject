#!/usr/bin/env python3

# gpsToKml.py
#                               OR any other Gps File V
#To run: python gpsToKml.py 2025_05_01__145019_gps_file.txt output.kml

#This file attempts to cover the 1st requirement:
#   Read GPS file
#   Parse NMEA sentences ($GPRMC)
#   Convert NMEA lat/lon
#   Emit a simple KML path



import sys
import math
import datetime


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



# Basic KML output

def write_kml(points, output_file, altitude=3):
    
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

        kml.write('  </Document>\n')
        kml.write('</kml>\n')



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

    write_kml(points, output_file)
    print(f"Requirement 1 KML created: {output_file}")


if __name__ == "__main__":
    main()
