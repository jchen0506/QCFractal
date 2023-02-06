from flask import current_app

from qcfractal import __version__ as qcfractal_version
from qcfractal.app import main, wrap_route, storage_socket
from qcfractal.client_versions import client_version_lower_limit, client_version_upper_limit
from qcportal.serverinfo import (
    AccessLogSummaryFilters,
    AccessLogQueryFilters,
    ServerStatsQueryFilters,
    ErrorLogQueryFilters,
    DeleteBeforeDateBody,
)
from qcportal.utils import calculate_limit


@main.route("/v1/information", methods=["GET"])
@wrap_route("READ")
def get_information():
    qcf_cfg = current_app.config["QCFRACTAL_CONFIG"]

    # TODO FOR RELEASE - change lower and upper version limits?
    public_info = {
        "name": qcf_cfg.name,
        "manager_heartbeat_frequency": qcf_cfg.heartbeat_frequency,
        "version": qcfractal_version,
        "api_limits": qcf_cfg.api_limits.dict(),
        "client_version_lower_limit": client_version_lower_limit,
        "client_version_upper_limit": client_version_upper_limit,
    }

    return public_info


@main.route("/v1/access_logs/query", methods=["POST"])
@wrap_route("READ")
def query_access_log_v1(body_data: AccessLogQueryFilters):
    max_limit = current_app.config["QCFRACTAL_CONFIG"].api_limits.get_access_logs
    body_data.limit = calculate_limit(max_limit, body_data.limit)
    return storage_socket.serverinfo.query_access_log(body_data)


@main.route("/v1/access_logs/bulkDelete", methods=["POST"])
@wrap_route("DELETE")
def delete_access_log_v1(body_data: DeleteBeforeDateBody):
    return storage_socket.serverinfo.delete_access_logs(before=body_data.before)


@main.route("/v1/access_logs/summary", methods=["GET"])
@wrap_route("READ")
def query_access_summary_v1(url_params: AccessLogSummaryFilters):
    return storage_socket.serverinfo.query_access_summary(url_params)


@main.route("/v1/server_stats/query", methods=["POST"])
@wrap_route("READ")
def query_server_stats_v1(body_data: ServerStatsQueryFilters):
    max_limit = current_app.config["QCFRACTAL_CONFIG"].api_limits.get_server_stats
    body_data.limit = calculate_limit(max_limit, body_data.limit)
    return storage_socket.serverinfo.query_server_stats(body_data)


@main.route("/v1/server_stats/bulkDelete", methods=["POST"])
@wrap_route("DELETE")
def delete_server_stats_v1(body_data: DeleteBeforeDateBody):
    return storage_socket.serverinfo.delete_server_stats(before=body_data.before)


@main.route("/v1/server_errors/query", methods=["POST"])
@wrap_route("READ")
def query_error_log_v1(body_data: ErrorLogQueryFilters):
    max_limit = current_app.config["QCFRACTAL_CONFIG"].api_limits.get_error_logs
    body_data.limit = calculate_limit(max_limit, body_data.limit)
    return storage_socket.serverinfo.query_error_log(body_data)


@main.route("/v1/server_errors/bulkDelete", methods=["POST"])
@wrap_route("DELETE")
def delete_server_error_log_v1(body_data: DeleteBeforeDateBody):
    return storage_socket.serverinfo.delete_error_logs(before=body_data.before)