from flask import current_app

from qcfractal import __version__ as qcfractal_version
from qcfractal.app import main, storage_socket
from qcfractal.app.routes import wrap_route
from qcfractal.client_versions import client_version_lower_limit, client_version_upper_limit
from qcportal.serverinfo import (
    AccessLogSummaryParameters,
    AccessLogQueryBody,
    ServerStatsQueryParameters,
    ErrorLogQueryBody,
    DeleteBeforeDateBody,
)
from qcportal.utils import calculate_limit


#@main.route("/v1/information", methods=["GET"])
#@wrap_route(None, None, "READ")
#def get_information():
#    qcf_cfg = current_app.config["QCFRACTAL_CONFIG"]
#
#    # TODO FOR RELEASE - change lower and upper version limits?
#    public_info = {
#        "name": qcf_cfg.name,
#        "manager_heartbeat_frequency": qcf_cfg.heartbeat_frequency,
#        "version": qcfractal_version,
#        "api_limits": qcf_cfg.api_limits.dict(),
#        "client_version_lower_limit": client_version_lower_limit,
#        "client_version_upper_limit": client_version_upper_limit,
#    }
#
#    return public_info