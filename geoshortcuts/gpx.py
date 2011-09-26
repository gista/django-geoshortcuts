import StringIO

from geoshortcuts import find_geom_field
from geoshortcuts.gpx_parser import *


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
		func_name = 'set_%s' % gpx_field
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
		func_name = 'set_%s' % gpx_field
		path_value = getattr(path, path_field)
		if path_value is None:
			continue
		gpx_value = gpx_fields[gpx_field](path_value)
		getattr(rte, func_name)(gpx_value)
	return rte


def render_to_gpx(creator, poi_queryset=None, path_queryset=None, meta=None, poi_mapping = None,
		  path_mapping = None):
	"""Renders querysets to GPX format. Parameters:
	creator       - string name of creator of the GPX file
	poi_queryset  - Queryset of points
	path_queryset - Queryset of LineStrings
	meta          - Dict with metainformations of GPX
	poi_mapping   - Dict defining mapping between POI model and GPX Waypoint fields
	path_mapping  - Dict defining mapping between POI model and GPX Route fields

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

	if poi_queryset is None and path_queryset is None:
		raise ValueError
	str_out = StringIO.StringIO()
	gpx = gpxType(version=1.1, creator=creator)

	"""
	extent() returns tuple: (xmin, ymin, xmax, ymax), where:
	x -- longitude
	y -- latitude
	"""
	poi_bounds = (float('inf'), float('inf'), float('-inf'), float('-inf')) \
			if poi_queryset is None or not poi_queryset.exists() else poi_queryset.extent()
	path_bounds = (float('inf'), float('inf'), float('-inf'), float('-inf')) \
			if path_queryset is None or not path_queryset.exists() else path_queryset.extent()
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

	if poi_queryset is not None:
		gfield_name = find_geom_field(poi_queryset)
		for poi in poi_queryset:
			wpt = wptType(
				lon=getattr(poi, gfield_name).get_x(),
				lat=getattr(poi, gfield_name).get_y(),
				ele=getattr(poi, gfield_name).get_z())
			if poi_mapping is not None:
				wpt = __decorate_waypoint(poi, poi_mapping, wpt)
			gpx.add_wpt(wpt)
	if path_queryset is not None:
		gfield_name = find_geom_field(path_queryset)
		for path in path_queryset:
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
