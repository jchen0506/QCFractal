"""
Tests the wavefunction store socket
"""

from qcfractal.db_socket import SQLAlchemySocket
from qcfractal.portal.records.singlepoint import (
    SinglePointInputSpecification,
    SinglePointDriver,
    SinglePointProtocols,
)
from qcfractal.portal.records.optimization import (
    OptimizationInputSpecification,
    OptimizationSinglePointInputSpecification,
    OptimizationProtocols,
)
from qcfractal.portal.keywords import KeywordSet


def test_optimizationrecord_socket_basic_specification(storage_socket: SQLAlchemySocket):

    spec1 = OptimizationInputSpecification(
        program="optprog1",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(trajectory="final"),
        singlepoint_specification=OptimizationSinglePointInputSpecification(
            program="prog2",
            method="b3lyp",
            basis="6-31g",
            keywords=KeywordSet(values={"k2": "values2"}),
            protocols=SinglePointProtocols(wavefunction="all"),
        ),
    )

    spec2 = OptimizationInputSpecification(
        program="optprog2",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(),
        singlepoint_specification=OptimizationSinglePointInputSpecification(
            program="prog2",
            driver=SinglePointDriver.hessian,
            method="hf",
            basis="def2-tzvp",
            keywords=KeywordSet(values={"k": "value"}),
            protocols=SinglePointProtocols(wavefunction="all"),
        ),
    )

    spec3 = OptimizationInputSpecification(
        program="optprog2",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(trajectory="none"),
        singlepoint_specification=OptimizationSinglePointInputSpecification(
            program="prog2",
            driver=SinglePointDriver.hessian,
            method="hf",
            basis="def2-tzvp",
            keywords=KeywordSet(values={"k": "value"}),
            protocols=SinglePointProtocols(wavefunction="orbitals_and_eigenvalues"),
        ),
    )

    meta1, id1 = storage_socket.records.optimization.add_specification(spec1)
    meta2, id2 = storage_socket.records.optimization.add_specification(spec2)
    meta3, id3 = storage_socket.records.optimization.add_specification(spec3)
    assert meta1.success
    assert meta2.success
    assert meta3.success
    assert meta1.inserted_idx == [0]
    assert meta2.inserted_idx == [0]
    assert meta3.inserted_idx == [0]
    assert meta1.existing_idx == []
    assert meta2.existing_idx == []
    assert meta3.existing_idx == []

    sp1 = storage_socket.records.optimization.get_specification(id1)
    sp2 = storage_socket.records.optimization.get_specification(id2)
    sp3 = storage_socket.records.optimization.get_specification(id3)

    for sp in [sp1, sp2, sp3]:
        assert sp["singlepoint_specification_id"] == sp["singlepoint_specification"]["id"]
        assert sp["singlepoint_specification"]["keywords_id"] == sp["singlepoint_specification"]["keywords"]["id"]
        sp.pop("id")
        sp.pop("singlepoint_specification_id")
        sp["singlepoint_specification"].pop("id")
        sp["singlepoint_specification"].pop("keywords_id")
        sp["singlepoint_specification"]["keywords"].pop("id")

        assert sp["singlepoint_specification"]["driver"] == SinglePointDriver.deferred

    assert OptimizationInputSpecification(**sp1) == spec1
    assert OptimizationInputSpecification(**sp2) == spec2
    assert OptimizationInputSpecification(**sp3) == spec3


common_sp_spec = OptimizationSinglePointInputSpecification(
    program="prog1",
    driver=SinglePointDriver.energy,
    method="b3lyp",
    basis="6-31G*",
    keywords=KeywordSet(values={"k": "value"}),
    protocols=SinglePointProtocols(),
)


def test_optimizationrecord_socket_add_specification_same_0(storage_socket: SQLAlchemySocket):

    spec1 = OptimizationInputSpecification(
        program="optprog1",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(),
        singlepoint_specification=common_sp_spec,
    )

    meta, id = storage_socket.records.optimization.add_specification(spec1)
    assert meta.success
    assert meta.inserted_idx == [0]
    assert meta.existing_idx == []
    assert id is not None

    # Try inserting again
    meta, id2 = storage_socket.records.optimization.add_specification(spec1)
    assert meta.success
    assert meta.inserted_idx == []
    assert meta.existing_idx == [0]
    assert id == id2

    # Change keywords
    spec1 = OptimizationInputSpecification(
        program="optprog1",
        keywords={"k": "value2"},
        protocols=OptimizationProtocols(),
        singlepoint_specification=common_sp_spec,
    )

    meta, id3 = storage_socket.records.optimization.add_specification(spec1)
    assert meta.success
    assert meta.inserted_idx == [0]
    assert meta.existing_idx == []
    assert id3 != id


def test_optimizationrecord_socket_add_specification_same_1(storage_socket: SQLAlchemySocket):
    # Test case sensitivity
    spec = OptimizationInputSpecification(
        program="optprog1",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(),
        singlepoint_specification=common_sp_spec,
    )

    meta, id = storage_socket.records.optimization.add_specification(spec)
    assert meta.inserted_idx == [0]

    spec = OptimizationInputSpecification(
        program="optPRog1",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(),
        singlepoint_specification=common_sp_spec,
    )

    meta, id2 = storage_socket.records.optimization.add_specification(spec)
    assert meta.existing_idx == [0]
    assert id == id2


def test_optimizationrecord_socket_add_specification_same_2(storage_socket: SQLAlchemySocket):
    # Test keywords defaults
    spec = OptimizationInputSpecification(
        program="optprog1", keywords={}, protocols=OptimizationProtocols(), singlepoint_specification=common_sp_spec
    )

    meta, id = storage_socket.records.optimization.add_specification(spec)
    assert meta.inserted_idx == [0]

    spec = OptimizationInputSpecification(
        program="optprog1", protocols=OptimizationProtocols(), singlepoint_specification=common_sp_spec
    )

    meta, id2 = storage_socket.records.optimization.add_specification(spec)
    assert meta.existing_idx == [0]
    assert id == id2


def test_optimizationrecord_socket_add_specification_same_3(storage_socket: SQLAlchemySocket):
    # Test protocols defaults
    spec = OptimizationInputSpecification(program="optprog1", keywords={}, singlepoint_specification=common_sp_spec)

    meta, id = storage_socket.records.optimization.add_specification(spec)
    assert meta.inserted_idx == [0]

    spec = OptimizationInputSpecification(
        program="optprog1", keywords={}, protocols=OptimizationProtocols(), singlepoint_specification=common_sp_spec
    )

    meta, id2 = storage_socket.records.optimization.add_specification(spec)
    assert meta.existing_idx == [0]
    assert id == id2


def test_optimizationrecord_socket_add_specification_same_4(storage_socket: SQLAlchemySocket):
    # Test protocols defaults (due to exclude_defaults)
    spec = OptimizationInputSpecification(program="optprog1", keywords={}, singlepoint_specification=common_sp_spec)

    meta, id = storage_socket.records.optimization.add_specification(spec)
    assert meta.inserted_idx == [0]

    spec = OptimizationInputSpecification(
        program="optprog1",
        keywords={},
        protocols=OptimizationProtocols(trajectory="all"),
        singlepoint_specification=common_sp_spec,
    )

    meta, id2 = storage_socket.records.optimization.add_specification(spec)
    assert meta.existing_idx == [0]
    assert id == id2


def test_optimizationrecord_socket_add_diff_1(storage_socket: SQLAlchemySocket):
    # Test different protocols
    spec = OptimizationInputSpecification(
        program="optprog1",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(),
        singlepoint_specification=common_sp_spec,
    )

    meta, id = storage_socket.records.optimization.add_specification(spec)
    assert meta.inserted_idx == [0]

    spec = OptimizationInputSpecification(
        program="optprog1",
        keywords={"k": "value"},
        protocols=OptimizationProtocols(trajectory="initial_and_final"),
        singlepoint_specification=common_sp_spec,
    )

    meta, id2 = storage_socket.records.optimization.add_specification(spec)
    assert meta.n_inserted == 1
    assert meta.inserted_idx == [0]
    assert meta.existing_idx == []
    assert id != id2