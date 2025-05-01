import xml.etree.ElementTree as ET


def parse_kml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Define the KML namespace
    kml_namespace = {"kml": "http://www.opengis.net/kml/2.2"}

    # Find all Placemark elements with LineString in the KML file
    placemarks = root.findall(
        ".//kml:Placemark[kml:LineString]", namespaces=kml_namespace
    )

    inner_london = []
    central_london = []
    orbital_london = []
    greater_london = []
    outer_london = []
    outer_london_circle_one = []
    outer_london_circle_two = []
    mapper = {
        "Inner London": inner_london,
        "Orbital London": orbital_london,
        "Central London": central_london,
        "Greater London": greater_london,
        "Outer London": outer_london,
        "Outer London Circle One": outer_london_circle_one,
        "Outer London Circle Two": outer_london_circle_two,
    }

    # Extract and print coordinates for each LineString and its associated Placemark name
    for placemark in placemarks:
        name = placemark.find(".//kml:name", namespaces=kml_namespace).text.strip()
        linestring = placemark.find(".//kml:LineString", namespaces=kml_namespace)
        coordinates = (
            linestring.find(".//kml:coordinates", namespaces=kml_namespace)
            .text.strip()
            .split()
        )

        List = mapper[name]
        for coord in coordinates:
            lon, lat, _ = map(float, coord.split(","))
            List.append((lat, lon))
    return mapper
