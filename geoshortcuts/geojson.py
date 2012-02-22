
from django.contrib.gis.geos import Polygon
from django.utils import simplejson

from geoshortcuts import find_geom_field


SPATIAL_REF_SITE = 'http://spatialreference.org/ref/epsg/'

#Geojson field names
GEOJSON_FIELD_TYPE	 = 'type'
GEOJSON_FIELD_HREF	 = 'href'
GEOJSON_FIELD_PROPERTIES = 'properties'
GEOJSON_FIELD_CRS	 = 'crs'
GEOJSON_FIELD_SRID	 = 'srid'
GEOJSON_FIELD_GEOMETRY	 = 'geometry'
GEOJSON_FIELD_FEATURES	 = 'features'
GEOJSON_FIELD_BBOX	 = 'bbox'
GEOJSON_FIELD_ID	 = 'id'

#Geojson field values
GEOJSON_VALUE_LINK		 = 'link'
GEOJSON_VALUE_FEATURE		 = 'Feature'
GEOJSON_VALUE_FEATURE_COLLECTION = 'FeatureCollection'

def __simple_render_to_json(obj):
	"""Converts python objects to simple json objects (int, float, string)"""
	if type(obj) == int or type(obj) == float or type(obj) == bool:
		return obj
	elif type(obj) == unicode:
		return obj.encode("utf-8")
	else:
		return str(obj)

def render_to_geojson(queryset, projection=None, simplify=None, extent=None, maxfeatures=None, priorityfield=None, properties=None, prettyprint=False):
	'''
	Shortcut to render a GeoJson FeatureCollection from a Django QuerySet.
	Currently computes a bbox and adds a crs member as a sr.org link.
	Parameters:
	* queryset of models containing geometry data
	* projection used when geometry data should be transformed to other projection
	* simplify (float) value specifies tolerance in Douglas-Peucker algorithm for simplifying geometry
	* extent (django.contrib.gis.geos.Polygon instance) that which bounds rendered features
	* maxfeatures parameter gives maximum number of rendered features based on priority field.
	* priorityfield (string) - name of the priority field used for reducing features
	* properties - list of model's non geometry fields names included in geojson
	* prettyprint flag influencing indentation used in geojson (for better readability)
	'''

	geom_field = find_geom_field(queryset)

	if extent is not None:
		#queryset.filter(<geom_field>__intersects=extent)
		queryset = queryset.filter(**{'%s__intersects' % geom_field: extent})

	if maxfeatures is not None:
		if priorityfield is None:
			raise RuntimeError("priorityfield must be defined")
		queryset.order_by(priority_field)
		queryset = queryset[:maxfeatures]

	src_projection = None
	if queryset.exists():
		src_projection = getattr(queryset[0], geom_field).srid

	if projection is None:
		projection = src_projection

	if projection is not None and src_projection != projection:
		queryset = queryset.transform(projection)

	if properties is None:
		properties = [field.name for field in queryset.model._meta.fields]

	features = list()
	collection = dict()
	if src_projection is not None:
		crs = dict()
		crs[GEOJSON_FIELD_TYPE] = GEOJSON_VALUE_LINK
		crs_properties = dict()
		crs_properties[GEOJSON_FIELD_HREF] = '%s%s/' % (SPATIAL_REF_SITE, projection)
		crs_properties[GEOJSON_FIELD_TYPE] = 'proj4'
		crs[GEOJSON_FIELD_PROPERTIES] = crs_properties
		collection[GEOJSON_FIELD_CRS] = crs
		collection[GEOJSON_FIELD_SRID] = projection
	for item in queryset:
		feat = dict()
		feat[GEOJSON_FIELD_ID] = item.pk

		#filling feature properties with dict: {<field_name>:<field_value>}
		feat[GEOJSON_FIELD_PROPERTIES] = dict()
		for fname in properties:
			if fname == geom_field:
				continue
			feat[GEOJSON_FIELD_PROPERTIES][fname] = __simple_render_to_json(getattr(item, fname))
		feat[GEOJSON_FIELD_TYPE] = GEOJSON_VALUE_FEATURE
		geom = getattr(item, geom_field)
		if simplify is not None:
			geom = geom.simplify(simplify)
		feat[GEOJSON_FIELD_GEOMETRY] = simplejson.loads(geom.geojson)
		features.append(feat)

	collection[GEOJSON_FIELD_TYPE] = GEOJSON_VALUE_FEATURE_COLLECTION
	collection[GEOJSON_FIELD_FEATURES] = features

	if queryset.exists():
		if projection is not None and src_projection != projection:
			poly = Polygon.from_bbox(queryset.extent())
			poly.srid = src_projection
			poly.transform(projection)
			collection[GEOJSON_FIELD_BBOX] = poly.extent
		else:
			collection[GEOJSON_FIELD_BBOX] = queryset.extent()

	if prettyprint == True:
		return simplejson.dumps(collection, indent=4)
	else:
		return simplejson.dumps(collection)

