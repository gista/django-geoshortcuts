from mapdata.models import *
import StringIO
from datetime import datetime
from gpx import *

from django.contrib.gis.db.models.fields import GeometryField
from django.contrib.gis.geos import Polygon
from django.utils import simplejson

SPATIAL_REF_SITE = 'http://spatialreference.org/ref/epsg/'

#Gpx fields
GPX_FIELD_NAME		= 'name'
GPX_FIELD_DESC		= 'desc'
GPX_FIELD_AUTHOR	= 'author'
GPX_FIELD_EMAIL		= 'email'
GPX_FIELD_LINK		= 'link'
GPX_FIELD_HREF		= 'href'
GPX_FIELD_TEXT		= 'text'
GPX_FIELD_TYPE		= 'type'
GPX_FIELD_TIME		= 'time'
GPX_FIELD_COPYRIGHT	= 'copyright'
GPX_FIELD_YEAR		= 'year'
GPX_FIELD_LICENSE	= 'license'
GPX_FIELD_KEYWORDS	= 'keywords'
GPX_FIELD_GEOIDHEIGHT	= 'geoidheight'
GPX_FIELD_SRC		= 'src'
GPX_FIELD_CMT		= 'cmt'
GPX_FIELD_SYM		= 'sym'
GPX_FIELD_HDOP		= 'hdop'
GPX_FIELD_VDOP		= 'vdop'
GPX_FIELD_PDOP		= 'pdop'
GPX_FIELD_SAT		= 'sat'
GPX_FIELD_NUMBER	= 'number'
GPX_FIELD_ELE		= 'ele'
GPX_XML_HEADER		= '<?xml version="1.0" encoding="UTF-8"?>'

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

def find_geom_field(queryset):
	"""Function returns geometry field name in model of query set. If doesn't exist, raise ValueError"""
	for field in queryset.model._meta.fields:
		geom_field = field.name if isinstance(field, GeometryField) else None
	if geom_field is None:
		raise ValueError
	else:
		return geom_field

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
		queryset = queryset.filter(**{'{0}__intersects'.format(geom_field):bbox})

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
		crs_properties[GEOJSON_FIELD_HREF] = '{0}{1}/'.format(SPATIAL_REF_SITE, to_srid)
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
			feat[GEOJSON_FIELD_PROPERTIES][fname] =				\
					__simple_render_to_json(getattr(item, fname))
		feat[GEOJSON_FIELD_TYPE] = GEOJSON_VALUE_FEATURE
		g = getattr(item, geom_field)
		if simplify is not None:
			g = g.simplify(simplify)
		feat[GEOJSON_FIELD_GEOMETRY] = simplejson.loads(g.geojson)
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


def __parse_meta(meta):
	"""Parses metadataType from dictionary"""
	name = None if meta.setdefault(GPX_FIELD_NAME, None) is None else meta[GPX_FIELD_NAME]
	desc = None if meta.setdefault(GPX_FIELD_DESC, None) is None else meta[GPX_FIELD_DESC]
	# AUTHOR
	dauthor = None if meta.setdefault(GPX_FIELD_AUTHOR, None) is None else meta[GPX_FIELD_AUTHOR]
	if dauthor is not None:
		if GPX_FIELD_EMAIL in dauthor.keys():
			email_tuple = dauthor[GPX_FIELD_EMAIL].split('@')
			author_email = emailType(id = email_tuple[0], domain=email_tuple[1])
		else:
			author_email = None
		dlink = None if dauthor.setdefault(GPX_FIELD_LINK, None) is None else dauthor[GPX_FIELD_LINK]
		if dlink is not None:
			dlink_href = dlink[GPX_FIELD_HREF]
			dlink_text = None if dlink.setdefault(GPX_FIELD_TEXT, None) is None else dlink[GPX_FIELD_TEXT]
			dlink_type = None if dlink.setdefault(GPX_FIELD_TYPE, None) is None else dlink[GPX_FIELD_TYPE]
			link = linkType(href=dlink_href, text=dlink_text, type_=dlink_type)
		else:
			link = None

		author = personType(name = dauthor.setdefault(GPX_FIELD_NAME),
				    email = author_email,
				    link = link)
	else:
		author = None
	# END AUTHOR
	time = None if meta.setdefault(GPX_FIELD_TIME, None) is None else meta[GPX_FIELD_TIME]
	# COPYRIGHT
	dcpright = None if meta.setdefault(GPX_FIELD_COPYRIGHT, None) is None else meta[GPX_FIELD_COPYRIGHT]
	if dcpright is not None:
		cpr_author = dcpright[GPX_FIELD_AUTHOR]
		cpr_year = None if dcpright.setdefault(GPX_FIELD_YEAR, None) is None else dcpright[GPX_FIELD_YEAR].year
		cpr_license = None if dcpright.setdefault(GPX_FIELD_LICENSE, None) is None else dcpright[GPX_FIELD_LICENSE]
		copyright = copyrightType(author=cpr_author, year=cpr_year, license=cpr_license)
	else:
		copyright = None
	# END COPYRIGHT
	# LINKS
	dlinks = None if meta.setdefault(GPX_FIELD_LINK, None) is None else meta[GPX_FIELD_LINK]
	if dlinks is not None:
		links = list()
		for dlink in dlinks:
			link_href = dlink[GPX_FIELD_HREF]
			link_text = None if dlink.setdefault(GPX_FIELD_TEXT, None) is None else dlink[GPX_FIELD_TEXT]
			link_type = None if dlink.setdefault(GPX_FIELD_TYPE, None) is None else dlink[GPX_FIELD_TYPE]
		links.append(linkType(href=link_href, text=link_text, type_=link_type))
	else:
		links = None
	# END LINKS
	time = None if meta.setdefault(GPX_FIELD_TIME, None) is None else \
			meta[GPX_FIELD_TIME].replace(microsecond=0).isoformat()
	keywords = None if meta.setdefault(GPX_FIELD_KEYWORDS, None) is None else meta[GPX_FIELD_KEYWORDS]
	return metadataType(name=name, desc=desc, author=author, copyright=copyright,
			    link=links, time=time, keywords=keywords)

def __decorate_waypoint(poi, poi_mapping, wpt):
	"""Adds aditional informations to waypoint wpt based on mapping poi_mapping of DB
	fields to GPX fields
	"""
	def time_constr(val):
		return val.replace(microsecond=0).isoformat()

	def pos_int_constr(val):
		val = int(val)
		if val < 0:
			raise ValueError
		return val

	gpx_fields = {GPX_FIELD_TIME:time_constr, GPX_FIELD_GEOIDHEIGHT:float, GPX_FIELD_NAME:unicode, GPX_FIELD_CMT:unicode,
		      GPX_FIELD_DESC:unicode, GPX_FIELD_SRC:unicode, GPX_FIELD_SYM:unicode, GPX_FIELD_TYPE:unicode,
		      GPX_FIELD_SAT:pos_int_constr, GPX_FIELD_HDOP:float, GPX_FIELD_VDOP:float, GPX_FIELD_PDOP:float}
	for gpx_field, poi_field in poi_mapping.items():
		func_name = 'set_{0}'.format(gpx_field)
		poi_value = getattr(poi, poi_field)
		if poi_value is None:
			continue
		gpx_value = gpx_fields[gpx_field](poi_value)
		getattr(wpt, func_name)(gpx_value)
	return wpt


def __decorate_route(path, path_mapping, rte):
	"""Adds aditional informations to route rte based on mapping path_mapping of DB
	fields to GPX fields
	"""

	def pos_int_constr(val):
		val = int(val)
		if val < 0:
			raise ValueError
		return val

	gpx_fields = {GPX_FIELD_NAME:unicode, GPX_FIELD_CMT:unicode, GPX_FIELD_DESC:unicode, GPX_FIELD_SRC:unicode,
		      GPX_FIELD_NUMBER:pos_int_constr, GPX_FIELD_TYPE:unicode}
	for gpx_field, path_field in path_mapping.items():
		func_name = 'set_{0}'.format(gpx_field)
		path_value = getattr(path, path_field)
		if path_value is None:
			continue
		gpx_value = gpx_fields[gpx_field](path_value)
		getattr(rte, func_name)(gpx_value)
	return rte


def render_to_gpx(creator, poi_qs=None, path_qs=None, meta=None, poi_mapping = None,
		  path_mapping = None):
	"""Renders querysets to GPX format. Parameters:
	creator     - string name of creator of the GPX file
	poi_qs      - Queryset of points
	path_qs     - Queryset of LineStrings
	meta        - Dict with metainformations of GPX
	poi_mapping - Dict defining mapping between POI model and GPX Waypoint fields
	path_mapping - Dict defining mapping between POI model and GPX Route fields

	Schema of dictionary meta (based on http://www.topografix.com/gpx/1/1/):
	metadata = {
		'name':,			#xsd:string - The name of the GPX file.
		'desc':,			#xsd:string - A description of the contents of the GPX file.
		'author': { 			# The person or organization who created the GPX file.
			'name':,		#xsd:string - Name of person or organization.
			'email':,		#xsd:string - Email address format: 'somebody@somewhere.com'
			'link':{		# Link to Web site or other external information about person.
				'href':,	#xsd:anyURI (mandatory) - URL of hyperlink.
				'text':,	#xsd:string - Text of hyperlink.
				'type':,	#xsd:string - Mime type of content (e.g. image/jpeg)
			}
		},
		'copyright':{			# Copyright and license information governing use of the file.
			'author':,		#xsd:string - Copyright holder
			'year':,		#xsd:gYear  - Year of copyright.
			'license':,		#xsd:anyURI - Link to external file containing license text.
		},
		'link':[{			# URLs associated with the location described in the file.
				'href':,	#xsd:anyURI (mandatory) - URL of hyperlink.
				'text':,	#xsd:string - Text of hyperlink.
				'type':,	#xsd:string - Mime type of content (e.g. image/jpeg)
				}
		],
		'time':,			#xsd:dateTime - The creation date of the file.
		'keywords':			#xsd:string - Keywords associated with the file.
						#Search engines or databases can use
						#this information to classify the data.
	}

	poi_mapping = {'<GPX waypoint field name>':'<Model field name>'}
	Supported GPX waypoint field names (based on http://www.topografix.com/gpx/1/1/):
	'time' 		- xsd:dateTime - Creation/modification timestamp for element.
	'geoidheight' 	- xsd:decimal - Height (in meters) of geoid (mean sea level) above WGS84
					earth ellipsoid. As defined in NMEA GGA message.
	'name' 		- xsd:string - The GPS name of the waypoint. This field will be
					transferred to and from the GPS.
	'cmt' 		- xsd:string - GPS waypoint comment. Sent to GPS as comment.
	'desc' 		- xsd:string - A text description of the element. Holds additional information
					about the element intended for the user, not the GPS.
	'src' 		- xsd:string - Source of data. Included to give user some idea
					of reliability and accuracy of data.
	'sym' 		- xsd:string - Text of GPS symbol name. For interchange with other programs,
					use the exact spelling of the symbol as displayed on the GPS.
					If the GPS abbreviates words, spell them out.
	'type' 		- xsd:string - Type (classification) of the waypoint.
	'sat' 		- xsd:nonNegativeInteger - Number of satellites used to calculate the GPX fix.
	'hdop' 		- xsd:decimal - Horizontal dilution of precision.
	'vdop' 		- xsd:decimal - Vertical dilution of precision.
	'pdop' 		- xsd:decimal - Position dilution of precision.

	path_mapping = {'<GPX route field name>':'<Model field name>'}
	Supported GPX route field names (based on http://www.topografix.com/gpx/1/1/):
	name 	- xsd:string - GPS name of route.
	cmt 	- xsd:string - GPS comment for route.
	desc 	- xsd:string - Text description of route for user. Not sent to GPS.
	src 	- xsd:string - Source of data. Included to give user some idea
				of reliability and accuracy of data.
	number 	- xsd:nonNegativeInteger - GPS route number.
	type 	- xsd:string - Type (classification) of route.
	"""

	if poi_qs is None and path_qs is None:
		raise ValueError
	str_out = StringIO.StringIO()
	gpx = gpxType(version=1.1, creator=creator)

	"""
	extent() returns tuple: (xmin, ymin, xmax, ymax), where:
	x -- longitude
	y -- latitude
	"""
	poi_bounds = (float('inf'), float('inf'), float('-inf'), float('-inf')) \
			if poi_qs is None else poi_qs.extent()
	path_bounds = (float('inf'), float('inf'), float('-inf'), float('-inf')) \
			if path_qs is None else path_qs.extent()
	bounds = boundsType(minlon=min(poi_bounds[0], path_bounds[0]),
			    minlat=min(poi_bounds[1], path_bounds[1]),
			    maxlon=max(poi_bounds[2], path_bounds[2]),
			    maxlat=max(poi_bounds[3], path_bounds[3]))

	if meta is not None:
		metadata = __parse_meta(meta)
		metadata.set_bounds(bounds)
	else:
		metadata = metadataType(bounds = bounds)
	gpx.set_metadata(metadata)

	if poi_qs is not None:
		gfield_name = find_geom_field(poi_qs)
		for poi in poi_qs:
			wpt = wptType(
				lon=getattr(poi, gfield_name).get_x(),
				lat=getattr(poi, gfield_name).get_y(),
				ele=getattr(poi, gfield_name).get_z())
			if poi_mapping is not None:
				wpt = __decorate_waypoint(poi, poi_mapping, wpt)
			gpx.add_wpt(wpt)
	if path_qs is not None:
		gfield_name = find_geom_field(path_qs)
		for path in path_qs:
			rte = rteType()
			if len(getattr(path, gfield_name)[0]) == 3:
				rte.set_rtept([wptType(lon=p[0], lat=p[1], ele=p[2]) \
						for p in getattr(path, gfield_name)])
			else:
				rte.set_rtept([wptType(lon=p[0], lat=p[1]) \
						for p in getattr(path, gfield_name)])
			if path_mapping is not None:
				rte = __decorate_route(path, path_mapping, rte)
			gpx.add_rte(rte)
	str_out.write(GPX_XML_HEADER + '\n')
	gpx.export(outfile=str_out, level=0, name_='gpx')
	return str_out.getvalue()
