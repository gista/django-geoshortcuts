from django.contrib.gis.db.models.fields import GeometryField

def find_geom_field(queryset):
	"""Function returns geometry field name in model of query set. If doesn't exist, raise ValueError"""
	for field in queryset.model._meta.fields:
		geom_field = field.name if isinstance(field, GeometryField) else None
	if geom_field is None:
		raise ValueError
	else:
		return geom_field
