Geoshortcuts is a library containing set of shortcuts that can be used in
GeoDjango applications. It also contains Django application that provides
unit tests of the library, and which is not required in final installation.

It provides two main functions:
* render_to_geojson - generates Geojson string from query set of model
  containing point, line or polygon geometry column
* render_to_gpx - generates GPX string from query set of model containing
  point or line geometry column


Generating of gpx_parser.py (GPX data stuctures and parser):
============================================================
It is required to install generateDS 2.5a (version 2.6a will generate
gYear type differently and unit tests will not pass successfully).

python generateDS.py -o gpx_parser.py --external-encoding='utf-8' gpx.xsd
