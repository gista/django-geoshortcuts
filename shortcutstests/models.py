from django.contrib.gis.db import models

class TestTable(models.Model):
	field0 = models.CharField(max_length = 50)

	def __unicode__(self):
		return self.field0

class TestPoint(models.Model):
	field0 = models.CharField(max_length = 50)
	field1 = models.IntegerField()
	field2 = models.DateTimeField()
	field3 = models.FloatField()
	field4 = models.BooleanField()
	field5 = models.ForeignKey(TestTable)

	the_geom = models.PointField()
	objects = models.GeoManager()

	def __unicode__(self):
		return self.field0

class TestLineString(models.Model):
	field0 = models.CharField(max_length = 50)
	field1 = models.IntegerField()
	field2 = models.DateTimeField()
	field3 = models.FloatField()
	field4 = models.BooleanField()
	field5 = models.ForeignKey(TestTable)

	the_geom = models.LineStringField()
	objects = models.GeoManager()

	def __unicode__(self):
		return self.field0

class TestPolygon(models.Model):
	field0 = models.CharField(max_length = 50)
	field1 = models.IntegerField()
	field2 = models.DateTimeField()
	field3 = models.FloatField()
	field4 = models.BooleanField()
	field5 = models.ForeignKey(TestTable)

	the_geom = models.PolygonField()
	objects = models.GeoManager()

	def __unicode__(self):
		return self.field0

