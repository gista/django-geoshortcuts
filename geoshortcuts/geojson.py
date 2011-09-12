
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
	else:
		return str(obj)

def render_to_geojson(queryset, transform=None, simplify=None, bbox=None, maxfeatures=None, properties=None, prettyprint=False):
	'''
	Shortcut to render a GeoJson FeatureCollection from a Django QuerySet.
	Currently computes a bbox and adds a crs member as a sr.org link.
	* maxfeatures parameter gives maximum number of rendered features based on priority field.
	Parameter should be instance of collections.namedtuple('MaxFeatures', ['maxfeatures', 'priority_field'])
	* bbox is boundary box (django.contrib.gis.geos.Polygon instance) which bounds rendered features
	'''

	geom_field = find_geom_field(queryset)

	if bbox is not None:
		#queryset.filter(<geom_field>__intersects=bbox)
		queryset = queryset.filter(**{'%s__intersects' % geom_field: bbox})

	if maxfeatures is not None:
		queryset.order_by(maxfeatures.priority_field)
		queryset = queryset[:maxfeatures.maxfeatures]

	srid = None
	if len(queryset) > 0:
		srid = getattr(queryset[0], geom_field).srid

	if transform is not None:
		to_srid = transform
		queryset = queryset.transform(to_srid)
	else:
		to_srid = srid

	if properties is None:
		properties = queryset.model._meta.get_all_field_names()

	features = list()
	collection = dict()
	if srid is not None:
		crs = dict()
		crs[GEOJSON_FIELD_TYPE] = GEOJSON_VALUE_LINK
		crs_properties = dict()
		crs_properties[GEOJSON_FIELD_HREF] = '%s%s/' % (SPATIAL_REF_SITE, to_srid)
		crs_properties[GEOJSON_FIELD_TYPE] = 'proj4'
		crs[GEOJSON_FIELD_PROPERTIES] = crs_properties
		collection[GEOJSON_FIELD_CRS] = crs
		collection[GEOJSON_FIELD_SRID] = to_srid
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

	if len(queryset) > 0:
		if transform is not None:
			poly = Polygon.from_bbox(queryset.extent())
			poly.srid = srid
			poly.transform(to_srid)
			collection[GEOJSON_FIELD_BBOX] = poly.extent
		else:
			collection[GEOJSON_FIELD_BBOX] = queryset.extent()

	if prettyprint == True:
		return simplejson.dumps(collection, indent=4)
	else:
		return simplejson.dumps(collection)

