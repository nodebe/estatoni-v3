from django.core.cache import cache
from django.utils import timezone
from account.models import VerificationStatusOption, KYCVerificationService, KYCVerificationServiceOptions, \
    IDTypeLabelOptions, KYCVerificationData, IDType
from account.tasks import background_verify_user
from account.v1.services.user import AccountService
from utils.constants.messages import ResponseMessages
from utils.errors import UserError
from utils.models import ModelService
from utils.third_party_connection import PremblyAPIService
from utils.util import CustomApiRequest


class KYCService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)
        self.model_service = ModelService(request)

    def fetch_user_status(self):
        return {
            "status": self.auth_user.kyc_verification_status,
            "comment": self.auth_user.kyc_verification_comment,
            "verified_at": self.auth_user.kyc_verified_at
        }

    def collect_data(self, payload):
        user_instance = self.auth_user

        if (user_instance.kyc_verification_status not in
                [VerificationStatusOption.not_started, VerificationStatusOption.failed,
                 VerificationStatusOption.pending]):

            raise UserError(ResponseMessages.kyc_status_already_verb.format(user_instance.kyc_verification_status))

        user = self.model_service.update_model_instance(model_instance=user_instance, **payload)

        _ = background_verify_user.delay(user_id=user.user_id)

        return ResponseMessages.kyc_data_submitted_successfully

    def get_kyc_verification_service(self):
        verification_service = KYCVerificationService.active_objects.first()

        if verification_service.name == KYCVerificationServiceOptions.prembly:
            return PremblyAPIService()
        return None

    def __names_match(self, name1, name2):
        if name1 is None or name2 is None:
            return False

        # Split the names into lists of individual components
        name1_parts = name1.lower().split()
        name2_parts = name2.lower().split()

        # Convert lists to sets for easier comparison
        name1_set = set(name1_parts)
        name2_set = set(name2_parts)

        # Find the intersection of the two sets
        common_names = name1_set.intersection(name2_set)

        # Check if the number of common names is less than 2
        return len(common_names) >= 2

    def verify_user(self, user, verification_data, response_data):
        # TODO: Hash the id_number
        verification_data["user"] = user
        kyc_verification_data = self.model_service.create_model_instance(model=KYCVerificationData,
                                                                         payload=verification_data)

        user_names = f"{user.first_name} {user.last_name}"
        verified_names = f"{verification_data.get('first_name')} {verification_data.get('last_name')}"

        names_match = self.__names_match(user_names, verified_names)

        if not names_match:
            user.kyc_verification_status = VerificationStatusOption.failed
            user.kyc_verification_comment = ResponseMessages.names_do_not_match
        else:
            kyc_verification_data.status = True
            kyc_verification_data.save()
            user.kyc_verification_status = VerificationStatusOption.verified
            user.kyc_verification_comment = response_data.get("detail", "Verification Complete")

        user.kyc_verification_response_data = response_data
        user.kyc_verified_at = timezone.now()
        user.save(update_fields=["kyc_verification_status", "kyc_verification_response_data",
                                 "kyc_verification_comment", "kyc_verified_at"])

        return True

    def fetch_verification_data_from_service(self, user_id):
        # Background
        account_service = AccountService(self.request)
        user = account_service.fetch_user_by_user_id(user_id=user_id, is_background=True)

        if not user:
            return False

        user.kyc_verification_status = VerificationStatusOption.processing
        user.save(update_fields=["kyc_verification_status"])

        id_type = user.id_type.label
        id_number = user.id_number

        verification_service = self.get_kyc_verification_service()

        if not verification_service:
            user.kyc_verification_status = VerificationStatusOption.pending
            user.kyc_verification_comment = ResponseMessages.verification_service_issues
            user.save(update_fields=["kyc_verification_status", "kyc_verification_comment"])

            return None

        if verification_service:
            if id_type == IDTypeLabelOptions.bvn:
                verification_data, response_data = verification_service.verify_bvn(id_number)
            elif id_type == IDTypeLabelOptions.nin:
                verification_data, response_data = verification_service.verify_nin(id_number)
            else:
                verification_data, response_data = None, None

            if verification_data:
                self.verify_user(user, verification_data, response_data)
            else:
                user.kyc_verification_status = VerificationStatusOption.failed
                user.kyc_verification_response_data = response_data
                user.kyc_verification_comment = response_data.get("detail", "Unknown reason")
                user.save(update_fields=["kyc_verification_status", "kyc_verification_response_data",
                                         "kyc_verification_comment"])

        return None


class IdTypeService(CustomApiRequest):
    def __init__(self, request):
        super().__init__(request)

    def fetch_list(self, filter_params, **extra_args):
        user = self.auth_user
        country = user.country

        def __do_fetch():
            id_types = IDType.active_available_objects.filter(country=country).values("id", "name")

            return id_types

        cache_key = self.generate_cache_key("country", country.id, model=IDType)
        return cache.get_or_set(cache_key, __do_fetch, 300)
