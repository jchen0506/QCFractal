from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import and_, func, text, select, delete

import qcfractal
from qcfractal.components.datasets.db_models import CollectionORM
from qcfractal.components.molecules.db_models import MoleculeORM
from qcfractal.components.outputstore.db_models import OutputStoreORM
from qcfractal.components.records.db_models import BaseRecordORM
from qcfractal.components.services.db_models import ServiceQueueORM
from qcfractal.components.tasks.db_models import TaskQueueORM
from qcfractal.db_socket.helpers import get_query_proj_options, get_count
from qcportal.metadata_models import QueryMetadata
from .db_models import BackgroundJobORM

if TYPE_CHECKING:
    from sqlalchemy.orm.session import Session
    from qcfractal.db_socket.socket import SQLAlchemySocket
    from typing import Dict, Any, List, Optional, Tuple, Iterable


class BackgroundJobSocket:
    def __init__(self, root_socket: SQLAlchemySocket):
        self.root_socket = root_socket
        self._logger = logging.getLogger(__name__)

        self._nproc = root_socket.qcf_config.background_processes
        self._background_enabled = self._nproc > 0



    def add_job(self, function: str, args, kwargs, user: Optional[str]):
        pass

    def run(self):
        pass