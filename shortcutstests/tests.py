from django.test import TestCase
from models import *

from shortcuts import *
from django.contrib.gis.geos import Polygon, LineString, Point
from django.contrib.gis.gdal import DataSource
from functools import reduce
from datetime import datetime, date
import time
import operator
import tempfile
import shutil

GPX_LAYERS = ("waypoints", "routes", "tracks", "route_points", "track_points")

METADATA = {
	'name':'test.gpx',
	'desc':'Testing GPX file',
	'author': {
		'name':'Foo Bar',
		'email':'nobody@somesite.com',
		'link':{
			'href':'www.somesite.com',
			'text':'www.gpxauthor.com',
			'type':'text/html',
		}
	},
	'copyright':{
		'author':'Foo Bar',
		'year':date.today(),
		'license':'/license/',
	},
	'link':[{
		'href':'www.somesite.com',
		'text':'Metadata source',
		'type':'text/html',
	}],
	'time':datetime.today(),
	'keywords':'testing, unstable',
}

POI_MAPPING = {
	'time': 'field2',
	'geoidheight': 'field3',
	'name': 'field0',
	'cmt' : 'field0',
	'desc': 'field0',
	'src' : 'field0',
	'sym' : 'field0',
	'type': 'field1',
	'sat' : 'field1',
	'hdop': 'field3',
	'vdop': 'field3',
	'pdop': 'field3'
}

PATH_MAPPING = {
	'name': 'field0',
	'cmt' : 'field0',
	'desc': 'field0',
	'src' : 'field0',
	'number' : 'field1',
	'type' : 'field1',
}

TTABLES = (
('Nizke Tatry'),
('Vysoke Tatry'),
('Slanske vrchy'),
('Kremnicke vrchy')
)

TLINE_STRINGS = (
('Nizke Tatry', 1, datetime.now(), 3.14, True, 1, LineString((0, 0), (0, 50), (50, 50), (50, 0), (0, 0))),
('Vysoke Tatry', 1, datetime.now(), 2.53, False, 2, LineString((1, 3), (1, 4), (1, 5), (1, 6), (1, 7))),
('Slanske vrchy', 1, datetime.now(), 5.63, False, 3, LineString((2, 0), (3, 50), (4, 50), (5, 0), (6, 0))),
('Kremnicke vrchy', 1, datetime.now(), 7.84, True, 0, LineString((0, 0), (60, 50), (5, 5), (5, 0), (1, 0))),
('Nizke Tatry', 1, datetime.now(), 45.4, False, 0, LineString((1, 0), (0, 5), (5, 5), (5, 0), (0, 0)))
)

TPOINTS = (
('Kralova Hola', 1, datetime.now(), 5.3, False, 0, Point(0,0)),
('Krivan',  1, datetime.now(), 7.6,  True, 1, Point(5,0)),
('Simonka', 1, datetime.now(), 3.9,  False, 2, Point(1,0)),
('Tajov',  1, datetime.now(), 4.1, True, 3, Point(0,2)),
('Jasna',  1, datetime.now(), 1.2, False, 1, Point(5,5)),
('Gerlach', 1, datetime.now(), 9.1, True, 0, Point(1,1))
)


TEST_POLYS = (
('area1', 1, datetime.now(), 1.2, True, 0, Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))),
('area2', 2, datetime.now(), 2.3, True, 1, Polygon(((2, 0), (2, 2), (0, 0), (0, 2), (2, 0)))),
('area3', 3, datetime.now(), 3.4, False, 2, Polygon(((0, 0), (0, 3), (3, 3), (3, 0), (0, 0)))),
('area4', 4, datetime.now(), 4.5, False, 3, Polygon(((0, 0), (0, 4), (4, 4), (4, 0), (0, 0)))),
('area5', 5, datetime.now(), 5.6, False, 0, Polygon(((0, 0), (0, 5), (5, 5), (5, 0), (0, 0)))),
)


GPX_DATETIME_FORMAT = '%Y/%m/%d %H:%M:%S'

class ShortcutsTest(TestCase):
	"""Tests of functions render_to_gpx() and render_to_geojson() in shortcuts module.
	Tests use testing database.
	"""

	def setUp(self):

		for tt in TTABLES:
			TestTable(field0=tt[0]).save()

		for ls in TLINE_STRINGS:
			TestLineString(field0=ls[0], field1=ls[1], field2=ls[2], field3=ls[3], field4=ls[4],
					field5=TestTable.objects.all()[ls[5]], the_geom=ls[6]).save()

		for p in TPOINTS:
			TestPoint(field0=p[0], field1=p[1], field2=p[2], field3=p[3], field4=p[4],
				  field5=TestTable.objects.all()[ls[5]], the_geom=p[6]).save()

		for tp in TEST_POLYS:
			TestPolygon(field0=tp[0], field1=tp[1], field2=tp[2], field3=tp[3], field4=tp[4],
				    field5=TestTable.objects.all()[ls[5]], the_geom=tp[6]).save()
		self.TMP_DIR = tempfile.mkdtemp()

	def __generate_data_source_from_gpx(self, poi_qs=None, path_qs=None):
		"""Generates DataSource from GPX. Uses render_to_gpx() shortcut.
		It has the same parameters as render_to_gpx()"""
		gpx = render_to_gpx('Matus Valo', poi_qs, path_qs, METADATA, POI_MAPPING, PATH_MAPPING)
		gpx_fname = '{0}/test_render_to_gpx{1}.xml'.format(self.TMP_DIR, int(time.time()))

		with open(gpx_fname, 'w') as gpx_file:
			gpx_file.write(gpx)

		return DataSource(gpx_fname)

	def test_poi_render_to_gpx(self):
		"""Tests rendering POIs to GPX with render_to_gpx()."""
		dbpois = TestPoint.objects.all()
		self.assertGreater(len(dbpois), 0)

		ds = self.__generate_data_source_from_gpx(poi_qs=dbpois)

		self.assertEqual(len(ds), len(GPX_LAYERS))
		for layer in ds:
			self.assertIn(layer.name, GPX_LAYERS)
			if layer.name == 'waypoints':
				wp_layer = layer
				self.assertEqual(len(layer), len(dbpois))
			else:
				self.assertEqual(len(layer), 0)

		self.assertEqual(wp_layer.geom_type.name, 'Point')

		dbflist = list()
		for poi in dbpois:
			geom_field = find_geom_field(dbpois)
			dbflist.append([
				    getattr(poi,POI_MAPPING[GPX_FIELD_TIME]).replace(microsecond=0),
				    float(getattr(poi,POI_MAPPING[GPX_FIELD_GEOIDHEIGHT])),
				    str(getattr(poi,POI_MAPPING[GPX_FIELD_NAME])),
				    str(getattr(poi,POI_MAPPING[GPX_FIELD_CMT])),
				    str(getattr(poi,POI_MAPPING[GPX_FIELD_DESC])),
				    str(getattr(poi,POI_MAPPING[GPX_FIELD_SRC])),
				    str(getattr(poi,POI_MAPPING[GPX_FIELD_SYM])),
				    str(getattr(poi,POI_MAPPING[GPX_FIELD_TYPE])),
				    int(getattr(poi,POI_MAPPING[GPX_FIELD_SAT])),
				    float(getattr(poi,POI_MAPPING[GPX_FIELD_HDOP])),
				    float(getattr(poi,POI_MAPPING[GPX_FIELD_VDOP])),
				    float(getattr(poi,POI_MAPPING[GPX_FIELD_PDOP])),
				    getattr(poi, geom_field)
				    ])
		for feature in wp_layer:
			gpxflist = [datetime.strptime(feature[GPX_FIELD_TIME].as_string(), GPX_DATETIME_FORMAT),
				    feature[GPX_FIELD_GEOIDHEIGHT].as_double(),
				    feature[GPX_FIELD_NAME].as_string(),
				    feature[GPX_FIELD_CMT].as_string(),
				    feature[GPX_FIELD_DESC].as_string(),
				    feature[GPX_FIELD_SRC].as_string(),
				    feature[GPX_FIELD_SYM].as_string(),
				    feature[GPX_FIELD_TYPE].as_string(),
				    feature[GPX_FIELD_SAT].as_int(),
				    feature[GPX_FIELD_HDOP].as_double(),
				    feature[GPX_FIELD_VDOP].as_double(),
				    feature[GPX_FIELD_PDOP].as_double(),
				    Point(feature.geom.tuple, feature[GPX_FIELD_ELE].as_double())
				    ]
			self.assertIn(gpxflist, dbflist)

			dbflist.remove(gpxflist)

	def test_path_render_to_gpx(self):
		"""Tests rendering Paths to GPX with render_to_gpx()."""
		dbpaths = TestLineString.objects.all()
		self.assertGreater(len(dbpaths), 0)

		ds = self.__generate_data_source_from_gpx(path_qs=dbpaths)
		self.assertEqual(len(ds), len(GPX_LAYERS))

		geom_field = find_geom_field(dbpaths)
		for layer in ds:
			self.assertIn(layer.name, GPX_LAYERS)
			if layer.name == 'routes':
				wp_layer = layer
				self.assertEqual(len(layer), len(dbpaths))
			elif layer.name == 'route_points':
				waypoints_num = reduce(operator.add, (len(getattr(path,geom_field)) for path in dbpaths))
				self.assertEqual(len(layer), waypoints_num)
			else:
				self.assertEqual(len(layer), 0)

		self.assertEqual(wp_layer.geom_type.name, 'LineString')
		dbflist = list()
		for path in dbpaths:
			dbflist.append([
				    str(getattr(path,PATH_MAPPING[GPX_FIELD_NAME])),
				    str(getattr(path,PATH_MAPPING[GPX_FIELD_CMT])),
				    str(getattr(path,PATH_MAPPING[GPX_FIELD_DESC])),
				    str(getattr(path,PATH_MAPPING[GPX_FIELD_SRC])),
				    int(getattr(path,PATH_MAPPING[GPX_FIELD_NUMBER])),
				    str(getattr(path,PATH_MAPPING[GPX_FIELD_TYPE])),
				    getattr(path, geom_field)
				])
		for feature in wp_layer:
			gpxflist = [
				    feature[GPX_FIELD_NAME].as_string(),
				    feature[GPX_FIELD_CMT].as_string(),
				    feature[GPX_FIELD_DESC].as_string(),
				    feature[GPX_FIELD_SRC].as_string(),
				    feature[GPX_FIELD_NUMBER].as_int(),
				    feature[GPX_FIELD_TYPE].as_string(),
				    LineString(feature.geom.tuple)
				]
			self.assertIn(gpxflist, dbflist)

			dbflist.remove(gpxflist)

	def test_poi_render_to_gpx_fail(self):
		"""Tests failing render_to_gpx() when no data passed."""
		with self.assertRaises(ValueError):
			render_to_gpx('Matus Valo')

	def __generate_data_source_from_json(self, query_set, proj_transform=None, geom_simplify=None,
					     bbox=None, maxfeatures=None, properties=None):
		"""Generates DataSource based on json generated with render_to_geojson() shortcut.
		Has the same parameters as render_to_geojson()
		"""
		json = render_to_geojson(query_set, proj_transform, geom_simplify, bbox, maxfeatures, properties)
		json_fname = '{0}/test_poi_render_to_json{1}.geojson'.format(self.TMP_DIR, int(time.time()))

		with open(json_fname, 'w') as json_file:
			json_file.write(json)
		return DataSource(json_fname)

	def __test_render_to_json(self, geom_query, properties=None):
		"Generic testing function of rendering json from queryset geom_query"""
		geom_field = find_geom_field(geom_query)

		self.assertGreater(len(geom_query), 0)

		ds = self.__generate_data_source_from_json(geom_query, properties=properties)


		self.assertEqual(ds.layer_count, 1)
		layer = ds[0]
		self.assertEqual(layer.num_feat, len(geom_query))

		self.assertListEqual(sorted(list(layer.fields)), sorted(list(properties)))
		self.assertTupleEqual(layer.extent.tuple, geom_query.extent())

		#We must check wether getattr(p, fname) is bool, because geojson returns 1(0) instead of True(False)
		geom_list = [[str(getattr(p, fname)) if type(getattr(p, fname)) != bool else str(int(getattr(p, fname))) \
				for fname in properties] for p in geom_query]
		for feature in layer:
			fgeom = [feature[fname].as_string() for fname in properties]
			self.assertIn(fgeom, geom_list)
			geom_list.remove(fgeom)

	def test_path_render_to_geojson(self):
		"""Tests rendering Paths to geojson with render_to_geojson()."""
		dbpaths = TestLineString.objects.all()
		self.__test_render_to_json(dbpaths, properties=('field0', 'field1', 'field2',			\
														'field3', 'field4', 'field5'))

	def test_poi_render_to_geojson(self):
		"""Tests rendering POIs to geojson with render_to_geojson()."""
		dbpois = TestPoint.objects.all()
		self.__test_render_to_json(dbpois, properties=('field0', 'field1', 'field2',			\
														'field3', 'field4', 'field5'))

	def test_area_render_to_geojson(self):
		"""Tests rendering Areas to geojson with render_to_geojson()."""
		dbareas = TestPolygon.objects.all()
		self.__test_render_to_json(dbareas, properties=('field0', 'field1', 'field2',			\
														'field3', 'field4', 'field5'))

	def tearDown(self):
		shutil.rmtree(self.TMP_DIR)
