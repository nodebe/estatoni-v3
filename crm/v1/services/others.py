from utils.util import CustomApiRequest


class OtherService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def fetch_options(self, filter_params):
        options = filter_params.get('options') or ""
        not_options = len(options) == 0

        if options:
            options = options.split(',')

        system_options = {}

        if "gender" in options or not_options:
            options_items = []
            system_options["options_items"] = options_items

        return system_options
