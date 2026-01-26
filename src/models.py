from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, ForeignKey, Column, Table
from sqlalchemy.orm import DeclarativeBase


class Model(DeclarativeBase):
    pass


class Building(Model):

    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    address: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]
    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        back_populates="building",
        lazy="selectin"
    )


class Activity(Model):
    __tablename__ = 'activities'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str]

    # Внешний ключ на родительскую деятельность
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("activities.id"),
        nullable=True
    )

    # Связь с родителем
    parent: Mapped[Optional["Activity"]] = relationship(
        "Activity",
        back_populates="children",
        remote_side=[id],
        lazy="selectin"
    )

    # Связь с дочерними элементами
    children: Mapped[list["Activity"]] = relationship(
        "Activity",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    organizations: Mapped[list["Organization"]] = relationship(
        "Organization",
        secondary="organization_activities",
        back_populates="activities",
        lazy="selectin"
    )

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<Activity(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"


class Organization(Model):
    __tablename__ = 'organizations'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)  # Название организации

    # Связь с зданием (одно здание — одна организация)
    building_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("buildings.id"),
        nullable=False
    )
    building: Mapped["Building"] = relationship("Building", back_populates="organizations", lazy="joined")

    # Связь с деятельностью (многие-ко-многим: организация может иметь несколько видов деятельности)
    activities: Mapped[list["Activity"]] = relationship(
        "Activity",
        secondary="organization_activities",
        back_populates="organizations",
        lazy="selectin"
    )

    # Телефоны — отдельная таблица для множества номеров
    phones: Mapped[list["Phone"]] = relationship(
        "Phone",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )


# Таблица связи многие-ко-многим между организациями и видами деятельности
organization_activities = Table(
    "organization_activities",
    Model.metadata,
    Column("organization_id", Integer, ForeignKey("organizations.id"), primary_key=True),
    Column("activity_id", Integer, ForeignKey("activities.id"), primary_key=True)
)


class Phone(Model):
    __tablename__ = 'phones'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    number: Mapped[str] = mapped_column(String, nullable=False)  # Номер телефона

    # Связь с организацией
    organization_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("organizations.id"),
        nullable=False
    )
    organization: Mapped["Organization"] = relationship("Organization", back_populates="phones", lazy="selectin")
