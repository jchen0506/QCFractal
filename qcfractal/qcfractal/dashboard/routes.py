from flask import current_app
from qcfractal.app import main, wrap_route, storage_socket

@main.route("/v1/dashboard", methods=["GET"])
@wrap_route("READ")
def dashboard_home():
	return "Hello, World!"