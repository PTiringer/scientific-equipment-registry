from nomad.datamodel.data import ArchiveSection, EntryData, UserReference
from nomad.datamodel.metainfo.annotations import ELNAnnotation
from nomad.metainfo import Datetime, MEnum, Quantity, SchemaPackage, Section, SubSection

m_package = SchemaPackage()

TEXT = 'StringEditQuantity'
SELECT = 'EnumEditQuantity'
PERSON = 'AuthorEditQuantity'
DATETIME = 'DateTimeEditQuantity'
DATE = 'DateEditQuantity'


def field(data_type, label, editor, *, description=None, **props):
    return Quantity(
        type=data_type,
        label=label,
        description=description,
        a_eln=ELNAnnotation(component=editor, props=props),
    )


class PrimaryOwnershipPeriod(ArchiveSection):
    m_def = Section(label='Primary ownership period')

    primary_owner = field(UserReference(), 'Primary owner', PERSON, required=True)
    project_description = field(
        str, 'Project description', TEXT, required=True, multiline=True
    )
    start_date = field(Datetime, 'Start date', DATE, required=True)
    end_date = field(
        Datetime,
        'End date',
        DATE,
        description='Last day of the assignment. Leave blank for the current assignment.',
    )
    recorded_on = field(
        Datetime,
        'Recorded on',
        DATETIME,
        description='Date and time when the assignment or change was recorded.',
    )


class EquipmentContact(ArchiveSection):
    m_def = Section(label='Equipment contact')

    person = field(UserReference(), 'Person', PERSON, required=True)
    role = field(
        MEnum('Expert', 'Technical contact', 'Current user'),
        'Role',
        SELECT,
        required=True,
    )


class EquipmentRecord(EntryData):
    m_def = Section(label='Equipment record', label_quantity='equipment_name')

    equipment_id = field(
        str,
        'Equipment ID',
        TEXT,
        description='Permanent identifier assigned by the registry administrator.',
        required=True,
    )
    equipment_name = field(str, 'Equipment name', TEXT, required=True)
    category = field(
        MEnum('Instrument', 'Sensor', 'Computer', 'Laboratory equipment', 'Other'),
        'Category',
        SELECT,
    )
    manufacturer_model = field(str, 'Manufacturer / model', TEXT)
    serial_inventory_number = field(str, 'Serial / inventory number', TEXT)
    department = field(str, 'Department', TEXT, required=True)
    location = field(str, 'Location', TEXT, required=True)
    status = field(
        MEnum('In use', 'In storage', 'Under repair', 'Retired'),
        'Status',
        SELECT,
        required=True,
    )
    primary_owner = Quantity(
        type=UserReference(),
        label='Primary owner',
        description='Taken from the sole primary ownership period without an end date.',
    )
    current_owner = field(UserReference(), 'Current owner', PERSON)
    equipment_group = field(str, 'Equipment group', TEXT)
    accessories_notes = field(str, 'Accessories / notes', TEXT, multiline=True)

    primary_ownership_history = SubSection(
        section_def=PrimaryOwnershipPeriod, repeats=True
    )
    other_contacts = SubSection(section_def=EquipmentContact, repeats=True)

    def normalize(self, archive, logger):
        super().normalize(archive, logger)
        if self.equipment_name and archive.metadata is not None:
            archive.metadata.entry_name = self.equipment_name

        for quantity in ('equipment_id', 'equipment_name', 'department', 'location', 'status'):
            if not (getattr(self, quantity) or '').strip():
                logger.warning('Missing required equipment field.', quantity=quantity)

        open_periods = []
        dated_periods = []
        for index, period in enumerate(self.primary_ownership_history, start=1):
            if (
                not period.primary_owner
                or not (period.project_description or '').strip()
                or period.start_date is None
            ):
                logger.warning('Incomplete primary ownership period.', period=index)
            if period.end_date is None:
                open_periods.append(period)
            if period.start_date is None:
                continue
            start = period.start_date.date()
            end = period.end_date.date() if period.end_date else None
            if end is not None and end < start:
                logger.warning('Ownership end date precedes start date.', period=index)
                continue
            dated_periods.append((start, end))

        ordered_periods = sorted(dated_periods, key=lambda period: period[0])
        for (_, previous_end), (start, _) in zip(ordered_periods, ordered_periods[1:]):
            if previous_end is None or start <= previous_end:
                logger.warning('Primary ownership periods overlap.')
                break

        self.primary_owner = None
        if len(open_periods) > 1:
            logger.warning('Only one primary ownership period may be open.')
        elif open_periods and open_periods[0].start_date is not None:
            self.primary_owner = open_periods[0].primary_owner

        for index, contact in enumerate(self.other_contacts, start=1):
            if not contact.person or not contact.role:
                logger.warning('Equipment contact needs a person and role.', contact=index)


m_package.__init_metainfo__()
