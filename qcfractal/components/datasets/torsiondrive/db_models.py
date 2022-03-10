from sqlalchemy import select, Column, Integer, ForeignKey, String, ForeignKeyConstraint, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import JSONB, array_agg
from sqlalchemy.orm import relationship, column_property
from sqlalchemy.orm.collections import attribute_mapped_collection

from qcfractal.components.datasets.db_models import CollectionORM
from qcfractal.components.molecules.db_models import MoleculeORM
from qcfractal.components.records.optimization.db_models import OptimizationSpecificationORM
from qcfractal.components.records.torsiondrive.db_models import TorsiondriveRecordORM
from qcfractal.db_socket import BaseORM


class TorsiondriveDatasetMoleculeORM(BaseORM):
    """
    Association table torsiondrive -> initial molecules
    """

    __tablename__ = "torsiondrive_dataset_molecule"

    dataset_id = Column(Integer, primary_key=True)
    entry_name = Column(String, primary_key=True)
    molecule_id = Column(Integer, ForeignKey(MoleculeORM.id), primary_key=True)

    molecule = relationship(MoleculeORM)

    __table_args__ = (
        Index("ix_torsiondrive_dataset_molecule_dataset_id", "dataset_id"),
        Index("ix_torsiondrive_dataset_molecule_entry_name", "entry_name"),
        Index("ix_torsiondrive_dataset_molecule_molecule_id", "molecule_id"),
        ForeignKeyConstraint(
            ["dataset_id", "entry_name"],
            ["torsiondrive_dataset_entry.dataset_id", "torsiondrive_dataset_entry.name"],
            ondelete="cascade",
            onupdate="cascade",
        ),
    )


class TorsiondriveDatasetEntryORM(BaseORM):
    __tablename__ = "torsiondrive_dataset_entry"

    dataset_id = Column(Integer, ForeignKey("torsiondrive_dataset.id", ondelete="cascade"), primary_key=True)

    name = Column(String, primary_key=True)
    comment = Column(String)

    torsiondrive_keywords = Column(JSONB, nullable=False)
    additional_keywords = Column(JSONB, nullable=True)
    attributes = Column(JSONB, nullable=True)

    initial_molecule_ids = column_property(
        select(array_agg(TorsiondriveDatasetMoleculeORM.molecule_id))
        .where(TorsiondriveDatasetMoleculeORM.dataset_id == dataset_id)
        .where(TorsiondriveDatasetMoleculeORM.entry_name == name)
        .scalar_subquery()
    )

    molecules = relationship(TorsiondriveDatasetMoleculeORM)

    __table_args__ = (
        Index("ix_torsiondrive_dataset_entry_dataset_id", "dataset_id"),
        Index("ix_torsiondrive_dataset_entry_name", "name"),
    )


class TorsiondriveDatasetSpecificationORM(BaseORM):
    __tablename__ = "torsiondrive_dataset_specification"

    dataset_id = Column(Integer, ForeignKey("torsiondrive_dataset.id", ondelete="cascade"), primary_key=True)
    name = Column(String, primary_key=True)
    description = Column(String, nullable=True)
    specification_id = Column(Integer, ForeignKey(OptimizationSpecificationORM.id), nullable=False)

    specification = relationship(OptimizationSpecificationORM, uselist=False)

    __table_args__ = (
        Index("ix_torsiondrive_dataset_specification_dataset_id", "dataset_id"),
        Index("ix_torsiondrive_dataset_specification_name", "name"),
        Index("ix_torsiondrive_dataset_specification_specification_id", "specification_id"),
    )


class TorsiondriveDatasetRecordItemORM(BaseORM):
    __tablename__ = "torsiondrive_dataset_record"

    dataset_id = Column(Integer, ForeignKey("torsiondrive_dataset.id", ondelete="cascade"), primary_key=True)
    entry_name = Column(String, primary_key=True)
    specification_name = Column(String, primary_key=True)
    record_id = Column(Integer, ForeignKey(TorsiondriveRecordORM.id), nullable=False)

    record = relationship(TorsiondriveRecordORM)

    __table_args__ = (
        ForeignKeyConstraint(
            ["dataset_id", "entry_name"],
            ["torsiondrive_dataset_entry.dataset_id", "torsiondrive_dataset_entry.name"],
            ondelete="cascade",
            onupdate="cascade",
        ),
        ForeignKeyConstraint(
            ["dataset_id", "specification_name"],
            ["torsiondrive_dataset_specification.dataset_id", "torsiondrive_dataset_specification.name"],
            ondelete="cascade",
            onupdate="cascade",
        ),
        Index("ix_torsiondrive_dataset_record_record_id", "record_id"),
        UniqueConstraint(
            "dataset_id", "entry_name", "specification_name", name="ux_torsiondrive_dataset_record_unique"
        ),
    )


class TorsiondriveDatasetORM(CollectionORM):
    __tablename__ = "torsiondrive_dataset"

    id = Column(Integer, ForeignKey(CollectionORM.id, ondelete="cascade"), primary_key=True)

    specifications = relationship(
        TorsiondriveDatasetSpecificationORM, collection_class=attribute_mapped_collection("name")
    )

    entries = relationship(TorsiondriveDatasetEntryORM, collection_class=attribute_mapped_collection("name"))

    record_items = relationship(TorsiondriveDatasetRecordItemORM)

    entry_names = column_property(
        select(array_agg(TorsiondriveDatasetEntryORM.name))
        .where(TorsiondriveDatasetEntryORM.dataset_id == id)
        .scalar_subquery()
    )

    __mapper_args__ = {
        "polymorphic_identity": "torsiondrive",
    }