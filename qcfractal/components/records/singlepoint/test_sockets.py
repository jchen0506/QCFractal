"""
Tests the singlepoint record socket
"""

import pytest

from qcfractal.db_socket import SQLAlchemySocket
from qcfractal.exceptions import MissingDataError
from qcfractal.portal.components.wavefunctions.models import WavefunctionProperties
from qcfractal.testing import load_wavefunction_data
from qcfractal.portal.components.records.singlepoint import (
    SinglePointSpecification,
    SinglePointDriver,
    SinglePointInput,
    AtomicResultProtocols,
)
from qcfractal.portal.components.keywords import KeywordSet
from qcfractal.components.records.singlepoint.db_models import ResultORM
from qcelemental.models import Molecule
from qcfractal.testing import load_molecule_data, load_procedure_data

_test_specs = [
    SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis="6-31G*",
        keywords=KeywordSet(values={"k": "value"}),
        protocols=AtomicResultProtocols(wavefunction="all"),
    ),
    SinglePointSpecification(
        program="Prog2",
        driver=SinglePointDriver.gradient,
        method="Hf",
        basis="def2-TZVP",
        keywords=KeywordSet(values={"k": "v"}),
    ),
    SinglePointSpecification(
        program="Prog3",
        driver=SinglePointDriver.hessian,
        method="pbe0",
        basis="",
        keywords=KeywordSet(values={"o": 1, "v": 2.123}),
        protocols=AtomicResultProtocols(stdout=False, wavefunction="orbitals_and_eigenvalues"),
    ),
    SinglePointSpecification(
        program="ProG4",
        driver=SinglePointDriver.hessian,
        method="pbe",
        basis=None,
        protocols=AtomicResultProtocols(stdout=False, wavefunction="return_results"),
    ),
]


@pytest.mark.parametrize("spec", _test_specs)
def test_singlepoint_add_get(storage_socket: SQLAlchemySocket, spec: SinglePointSpecification):
    water = load_molecule_data("water_dimer_minima")
    hooh = load_molecule_data("hooh")
    ne4 = load_molecule_data("neon_tetramer")
    all_mols = [water, hooh, ne4]

    meta, id = storage_socket.records.singlepoint.add(spec, all_mols)
    recs = storage_socket.records.get(id, include=["*", "task"])

    assert len(recs) == 3
    for r in recs:
        assert r["specification"]["program"] == spec.program.lower()
        assert r["specification"]["driver"] == spec.driver
        assert r["specification"]["method"] == spec.method.lower()
        assert r["specification"]["basis"] == (spec.basis.lower() if spec.basis is not None else "")
        assert r["specification"]["keywords"]["hash_index"] == spec.keywords.hash_index
        assert r["specification"]["protocols"] == spec.protocols.dict(exclude_defaults=True)
        assert r["task"]["spec"]["args"][0]["model"] == {"method": spec.method, "basis": spec.basis}
        assert r["task"]["spec"]["args"][0]["protocols"] == spec.protocols.dict(exclude_defaults=True)
        assert r["task"]["spec"]["args"][0]["keywords"] == spec.keywords.values
        assert r["task"]["spec"]["args"][1] == spec.program

    mol1 = storage_socket.molecules.get([recs[0]["molecule_id"]])[0]
    mol2 = storage_socket.molecules.get([recs[1]["molecule_id"]])[0]
    mol3 = storage_socket.molecules.get([recs[2]["molecule_id"]])[0]
    assert mol1["identifiers"]["molecule_hash"] == water.get_hash()
    assert Molecule(**recs[0]["task"]["spec"]["args"][0]["molecule"]) == water
    assert mol2["identifiers"]["molecule_hash"] == hooh.get_hash()
    assert Molecule(**recs[1]["task"]["spec"]["args"][0]["molecule"]) == hooh
    assert mol3["identifiers"]["molecule_hash"] == ne4.get_hash()
    assert Molecule(**recs[2]["task"]["spec"]["args"][0]["molecule"]) == ne4


def test_singlepoint_add_existing_molecule(storage_socket: SQLAlchemySocket):
    spec = _test_specs[0]

    water = load_molecule_data("water_dimer_minima")
    hooh = load_molecule_data("hooh")
    ne4 = load_molecule_data("neon_tetramer")
    all_mols = [water, hooh, ne4]

    # Add a molecule separately
    _, mol_ids = storage_socket.molecules.add([ne4])

    # Now add records
    meta, id = storage_socket.records.singlepoint.add(spec, all_mols)
    recs = storage_socket.records.get(id)

    assert len(recs) == 3
    assert recs[2]["molecule_id"] == mol_ids[0]


def test_singlepoint_add_same_1(storage_socket: SQLAlchemySocket):
    spec = SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis="6-31G*",
        keywords=KeywordSet(values={"k": "value"}),
        protocols=AtomicResultProtocols(wavefunction="all"),
    )

    water = load_molecule_data("water_dimer_minima")
    meta, id1 = storage_socket.records.singlepoint.add(spec, [water])
    assert meta.n_inserted == 1
    assert meta.inserted_idx == [0]

    meta, id2 = storage_socket.records.singlepoint.add(spec, [water])
    assert meta.n_inserted == 0
    assert meta.n_existing == 1
    assert meta.existing_idx == [0]
    assert id1 == id2


def test_singlepoint_add_same_2(storage_socket: SQLAlchemySocket):
    # Test case sensitivity
    spec1 = SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis="6-31G*",
        keywords=KeywordSet(values={"k": "value"}),
        protocols=AtomicResultProtocols(wavefunction="all"),
    )

    spec2 = SinglePointSpecification(
        program="pRog1",
        driver=SinglePointDriver.energy,
        method="b3lYp",
        basis="6-31g*",
        keywords=KeywordSet(values={"k": "value"}),
        protocols=AtomicResultProtocols(wavefunction="all"),
    )

    water = load_molecule_data("water_dimer_minima")
    meta, id1 = storage_socket.records.singlepoint.add(spec1, [water])
    assert meta.n_inserted == 1
    assert meta.inserted_idx == [0]

    meta, id2 = storage_socket.records.singlepoint.add(spec2, [water])
    assert meta.n_inserted == 0
    assert meta.n_existing == 1
    assert meta.existing_idx == [0]
    assert id1 == id2


def test_singlepoint_add_same_3(storage_socket: SQLAlchemySocket):
    # Test default keywords and protocols
    spec1 = SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis="6-31G*",
        keywords=KeywordSet(values={}),
        protocols=AtomicResultProtocols(wavefunction="none"),
    )

    spec2 = SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis="6-31G*",
    )

    water = load_molecule_data("water_dimer_minima")
    meta, id1 = storage_socket.records.singlepoint.add(spec1, [water])
    assert meta.n_inserted == 1
    assert meta.inserted_idx == [0]

    meta, id2 = storage_socket.records.singlepoint.add(spec2, [water])
    assert meta.n_inserted == 0
    assert meta.n_existing == 1
    assert meta.existing_idx == [0]
    assert id1 == id2


def test_singlepoint_add_same_4(storage_socket: SQLAlchemySocket):
    # Test None basis
    spec1 = SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis=None,
    )

    spec2 = SinglePointSpecification(
        program="prog1",
        driver=SinglePointDriver.energy,
        method="b3lyp",
        basis="",
    )

    water = load_molecule_data("water_dimer_minima")
    meta, id1 = storage_socket.records.singlepoint.add(spec1, [water])
    assert meta.n_inserted == 1
    assert meta.inserted_idx == [0]

    meta, id2 = storage_socket.records.singlepoint.add(spec2, [water])
    assert meta.n_inserted == 0
    assert meta.n_existing == 1
    assert meta.existing_idx == [0]
    assert id1 == id2


def test_singlepoint_add_same_5(storage_socket: SQLAlchemySocket):
    # Test adding keywords and molecule by id

    kw = KeywordSet(values={"a": "value"})
    _, kw_ids = storage_socket.keywords.add([kw])

    spec1 = SinglePointSpecification(
        program="prog1", driver=SinglePointDriver.energy, method="b3lyp", basis=None, keywords=kw
    )

    spec2 = SinglePointSpecification(
        program="prog1", driver=SinglePointDriver.energy, method="b3lyp", basis="", keywords=kw_ids[0]
    )

    water = load_molecule_data("water_dimer_minima")
    meta, id1 = storage_socket.records.singlepoint.add(spec1, [water])
    assert meta.n_inserted == 1
    assert meta.inserted_idx == [0]

    meta, id2 = storage_socket.records.singlepoint.add(spec2, [water])
    assert meta.n_inserted == 0
    assert meta.n_existing == 1
    assert meta.existing_idx == [0]
    assert id1 == id2


def test_singlepoint_add_update(storage_socket: SQLAlchemySocket):
    input_spec_1, molecule_1, result_data_1 = load_procedure_data("psi4_benzene_energy_1")
    input_spec_2, molecule_2, result_data_2 = load_procedure_data("psi4_peroxide_energy_wfn")
    input_spec_3, molecule_3, result_data_3 = load_procedure_data("rdkit_water_energy")

    meta1, id1 = storage_socket.records.singlepoint.add(input_spec_1, [molecule_1])
    meta2, id2 = storage_socket.records.singlepoint.add(input_spec_2, [molecule_2])
    meta3, id3 = storage_socket.records.singlepoint.add(input_spec_3, [molecule_3])

    with storage_socket.session_scope() as session:
        rec_orm = session.query(ResultORM).where(ResultORM.id == id1[0]).one()
        storage_socket.records.update_completed(session, rec_orm, result_data_1, None)

        rec_orm = session.query(ResultORM).where(ResultORM.id == id2[0]).one()
        storage_socket.records.update_completed(session, rec_orm, result_data_2, None)

        rec_orm = session.query(ResultORM).where(ResultORM.id == id3[0]).one()
        storage_socket.records.update_completed(session, rec_orm, result_data_3, None)