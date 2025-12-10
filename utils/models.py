from errors import ServerError
from utils.util import CustomApiRequest
from django.core.cache import cache


class ModelService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def create_model_instance(self, model=None, payload=None):
        """Creates a model instance of the model passed using the payload data"""
        if payload is None:
            payload = {}

        try:
            if model is None:
                error = "Invalid model instance"
                raise ServerError(error=error, error_position="ModelService.create_model_instance")

            has_created_by_attr = hasattr(model, "created_by")

            if isinstance(payload, list):
                payload_list = []
                for data in payload:
                    if has_created_by_attr:
                        data["created_by"] = self.auth_user
                    payload_list.append(
                        model(**data)
                    )
                main_object = model.objects.bulk_create(payload_list, ignore_conflicts=True)
            else:
                if has_created_by_attr:
                    payload["created_by"] = self.auth_user
                main_object = model.objects.create(**payload)

            main_object.save()

            return main_object

        except Exception as e:
            raise ServerError(error=e, error_position="ModelService.create_model_instance")

    def update_model_instance(self, model_instance=None, cache_keys=None, **kwargs):
        try:
            cache_util = CustomApiRequest(request=None)
            if model_instance is None:
                error = "Invalid model instance"
                raise ServerError(error, error_position="ModelService.update_model_instance")

            base_model_attributes = ["updated_by", "updated_at"]

            update_fields = []

            for attr in base_model_attributes:
                if hasattr(model_instance, attr):
                    if attr == "updated_at":
                        update_fields.append(attr)
                    elif attr == "updated_by":
                        kwargs[attr] = self.auth_user

            for field, value in kwargs.items():
                setattr(model_instance, field, value)
                update_fields.append(field)

            model_instance.save(update_fields=update_fields)

            # Update cache value
            if cache_keys is None:
                cache_keys = []

            if not isinstance(cache_keys, list):
                cache_keys = [cache_keys]

            cache_keys.append("id")

            for cache_key in cache_keys:
                cache_key_value = getattr(model_instance, cache_key, None)
                if cache_key_value:
                    cache_key = cache_util.generate_cache_key(model_instance.model_name(), cache_key_value)
                    cache.delete(cache_key, model_instance)

            return model_instance

        except Exception as e:
            raise ServerError(error=e, error_position="ModelService.update_model_instance")
