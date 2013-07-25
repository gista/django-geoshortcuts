from datetime import datetime
import time
import tempfile
import shutil
import numpy
import json

from django.test import TestCase
from django.contrib.gis.geos import Polygon, LineString, Point
from django.contrib.gis.gdal import DataSource

from geoshortcuts import find_geom_field
from geoshortcuts.geojson import render_to_geojson
from test_app.models import *


class ShortcutsTest(TestCase):
	"""Tests of functions render_to_geojson() in shortcuts module.
	Tests use testing database.
	"""
	fixtures = ["test_app.json"]

	def setUp(self):
		self.TMP_DIR = tempfile.mkdtemp()


	def _generate_data_source_from_json(self, query_set, **kwargs):
		"""Generates DataSource based on json generated with render_to_geojson() shortcut.
		Has the same parameters as render_to_geojson()
		"""
		json = render_to_geojson(query_set, **kwargs)
		json_fname = '%s/test_poi_render_to_json%s.geojson' % (self.TMP_DIR, int(time.time()))
		self.geojson = json

		json_file = open(json_fname, 'w')
		try:
			json_file.write(json)
		finally:
			json_file.close()
		return DataSource(json_fname)

	def _check_geometry(self, layer, geom_query, projection=None, simplify=None, **kwargs):
		model_projection = geom_query.model._meta.get_field(find_geom_field(geom_query)).srid
		if projection is not None and projection != model_projection:
			# prepare geometry for comparing in requested projection
			geom_query = geom_query.transform(projection)

		features_data = {}
		for feature in geom_query:
			if simplify:
				features_data[feature.pk] = feature.the_geom.simplify(simplify)
			else:
				features_data[feature.pk] = feature.the_geom

		for feature in layer:
			gid = feature["gid"].as_int()
			self.assertTrue(feature.geom.geos.equals_exact(features_data[gid], tolerance=0.001))

	def _check_extent(self, layer, geom_query, projection=None, **kwargs):
		model_projection = geom_query.model._meta.get_field(find_geom_field(geom_query)).srid
		if projection is not None and projection != model_projection:
			poly = Polygon.from_bbox(geom_query.extent())
			poly.srid = model_projection
			poly.transform(projection)
			query_extent = poly.extent
		else:
			query_extent = geom_query.extent()
		# layer.extent is useless, cause it computes extents from geometry, so it bypass geojson's value
		numpy.testing.assert_almost_equal(json.loads(self.geojson)["bbox"], query_extent, decimal=3)

	def _check_attributes(self, layer, geom_query, properties=(), **kwargs):
		properties_names = [prop_name for prop_name, attrib_name in properties]
		self.assertListEqual(sorted(list(layer.fields)), sorted(list(properties_names)))

		features_data = {}
		for feature in geom_query:
			feature_attrib_values = []
			for title, attrib_name in properties:
				if callable(attrib_name):
					value = attrib_name(feature)
				else:
					value = getattr(feature, attrib_name)
				# gdal treat boolean as integer (returns 1/0 instead of True/False)
				if type(value) == bool:
					value = int(value)
				value = str(value)
				feature_attrib_values.append(value)
			features_data[feature.pk] = feature_attrib_values

		for feature in layer:
			gid = feature["gid"].as_int()
			feature_attribs = [feature[prop_name].as_string() for prop_name in properties_names]
			self.assertEqual(feature_attribs, features_data[gid])

	def _test_render_to_json(self, geom_query, properties=(), **kwargs):
		"Generic testing function of rendering json from queryset geom_query"""
		geom_field = find_geom_field(geom_query)

		self.assertGreater(len(geom_query), 0)

		ds = self._generate_data_source_from_json(geom_query, properties=properties, **kwargs)
		self.assertEqual(ds.layer_count, 1)
		layer = ds[0]
		self.assertEqual(layer.num_feat, geom_query.count())

		self._check_extent(layer, geom_query, **kwargs)
		self._check_geometry(layer, geom_query, **kwargs)
		self._check_attributes(layer, geom_query, properties=properties)

	def test_path_render_to_geojson(self):
		"""Tests rendering Paths to geojson with render_to_geojson()."""
		dbpaths = TestLineString.objects.all()
		properties = (('gid', 'pk'), ('Field 0', 'field0'), ('Field 1', 'field1'), ('Field 2', 'field2'),
					('Field 3', 'field3'), ('Field 4', 'field4'), ('Field 5', 'field5'))
		self._test_render_to_json(dbpaths, properties=properties)

	def test_poi_render_to_geojson(self):
		"""Tests rendering POIs to geojson with render_to_geojson()."""
		dbpois = TestPoint.objects.all()
		def computed_field(feature):
			return feature.field1 + feature.field3
		properties = (('gid', 'pk'), ('Field 0', 'field0'), ('Field 1', 'field1'), ('Field 2', 'field2'),
					('Field 3', 'field3'), ('Field 4', 'field4'), ('Field 5', 'field5'), ("Computed", computed_field))
		self._test_render_to_json(dbpois, properties=properties, projection=4326)

	def test_area_render_to_geojson(self):
		"""Tests rendering Areas to geojson with render_to_geojson()."""
		dbareas = TestPolygon.objects.all()
		properties = (('gid', 'pk'), ('Field 0', 'field0'), ('Field 1', 'field1'), ('Field 2', 'field2'),
					('Field 3', 'field3'), ('Field 4', 'field4'), ('Field 5', 'field5'))
		self._test_render_to_json(dbareas, properties=properties)

	def test_geometry_simplify(self):
		dbareas = TestPolygon.objects.filter(pk=1)
		self._test_render_to_json(dbareas, simplify=0.5, properties=(("gid", "pk"),))

	def tearDown(self):
		shutil.rmtree(self.TMP_DIR)
