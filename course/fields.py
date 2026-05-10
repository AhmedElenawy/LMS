from django.core.exceptions import ObjectDoesNotExist
from django.db import models



class OrderField(models.PositiveIntegerField):
    def __init__(self, *args, for_fields = None, **kwargs):
        self.for_fields = for_fields
        super().__init__(*args, **kwargs)

    def pre_save(self, model_instance, add):
        if getattr(model_instance, self.attname) is None:
            try:
                qs = self.model.objects.select_for_update().all() #it locks raw until update
                if self.for_fields:
                    filters = {field:getattr(model_instance, field) for field in self.for_fields}
                    qs = qs.filter(**filters)
                    # last_item = qs.last()
                    # self.order = last_item.order + 1
                last_item = qs.latest(self.attname) #order by the orde field
                value = getattr(last_item, self.attname) + 1
            except ObjectDoesNotExist:
                value = 0
            setattr(model_instance, self.attname, value)
            return value
        else:
            return super().pre_save(model_instance, add)