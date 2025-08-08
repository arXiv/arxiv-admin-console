export enum UserVetoStatus {
    UNKNOWN = "",
    OK = "ok",
    NO_UPLOAD = "no-upload",
    NO_REPLACE = "no-replace",
    NO_ENDORSE = "no-endorse",
}

export enum UserFlags {
    UNKNOWN_FLAG = "?",
    ARXIV_FLAG_GROUP_TEST = "arXiv_demographics.flag_group_test",
    ARXIV_FLAG_PROXY = "arXiv_demographics.flag_proxy",
    ARXIV_FLAG_SUSPECT = "arXiv_demographics.flag_suspect",
    ARXIV_FLAG_XML = "arXiv_demographics.flag_xml",
    ARXIV_ENDORSEMENT_FLAG_VALID = "arXiv_endorsements.flag_valid",
    ARXIV_ENDORSEMENT_POINT_VALUE = "arXiv_endorsements.point_value",
    ARXIV_ENDORSEMENT_REQUEST_FLAG_VALID = "arXiv_endorsement_requests.flag_valid",
    TAPIR_EMAIL_BOUNCING = "tapir_users.email_bouncing",
    TAPIR_FLAG_BANNED = "tapir_users.flag_banned",
    TAPIR_FLAG_EDIT_SYSTEM = "tapir_users.flag_edit_system",
    TAPIR_FLAG_EDIT_USERS = "tapir_users.flag_edit_users",
    TAPIR_FLAG_EMAIL_VERIFIED = "tapir_users.flag_email_verified",
}