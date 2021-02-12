
from django.db import models

class PowerPlant(models.Model):
    name = models.CharField(max_length=100)

class PowerPlantInfo(models.Model):
    utc_timestamp = models.DateTimeField()
    powerplant = models.ForeignKey(PowerPlant, on_delete=models.CASCADE)
    actual = models.IntegerField()
    installed = models.IntegerField()

    @classmethod
    def get_all_timestamps_in_interval(cls, min_timestamp, max_timestamp, powerplant=None):
        query = cls.objects.filter(utc_timestamp__range=[min_timestamp, max_timestamp])
        if powerplant:
            query = query.filter(powerplant=powerplant)
        return query.values_list("utc_timestamp", flat=True)

    @classmethod
    def get_items_as_dataframe(cls, start_time, end_time, powerplant):
        import pandas as pd
        columns = ['utc_timestamp', powerplant.name + "_actual", powerplant.name + "_installed"]
        query = cls.objects.filter(utc_timestamp__range=[start_time, end_time])\
                            .filter(powerplant=powerplant).order_by('utc_timestamp')\
                            .values_list("utc_timestamp", "actual", "installed")
        df = pd.DataFrame(data=query, columns=columns)
        return df

    def __str__(self):
        return ", ".join([str(self.utc_timestamp), str(self.powerplant.name), str(self.actual), str(self.installed)])
