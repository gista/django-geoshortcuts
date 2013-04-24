from datetime import datetime
import time
import tempfile
import shutil

from django.test import TestCase
from django.contrib.gis.geos import Polygon, LineString, Point
from django.contrib.gis.gdal import DataSource

from geoshortcuts import find_geom_field
from geoshortcuts.geojson import render_to_geojson
from test_app.models import *


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
	"""Tests of functions render_to_geojson() in shortcuts module.
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


	def __generate_data_source_from_json(self, query_set, proj_transform=None, geom_simplify=None,
					     extent=None, maxfeatures=None, properties=None):
		"""Generates DataSource based on json generated with render_to_geojson() shortcut.
		Has the same parameters as render_to_geojson()
		"""
		json = render_to_geojson(query_set, projection=proj_transform, simplify=geom_simplify, extent=extent, maxfeatures=maxfeatures, properties=properties)
		json_fname = '%s/test_poi_render_to_json%s.geojson' % (self.TMP_DIR, int(time.time()))

		json_file = open(json_fname, 'w')
		try:
			json_file.write(json)
		finally:
			json_file.close()
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
