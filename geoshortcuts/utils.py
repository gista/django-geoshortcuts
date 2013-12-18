from django.contrib.gis.db.models.fields import GeometryField

def find_geom_field(queryset):
	"""Function returns geometry field name in model of query set. If doesn't exist, raise ValueError"""
	for field in queryset.model._meta.fields:
		if isinstance(field, GeometryField):
			return field.name
	raise ValueError
