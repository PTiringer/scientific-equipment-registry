from nomad.config.models.plugins import SchemaPackageEntryPoint


class EquipmentSchemaEntryPoint(SchemaPackageEntryPoint):
    def load(self):
        from .schema import m_package

        return m_package


equipment_schema = EquipmentSchemaEntryPoint(
    name='Scientific Equipment Registry schema',
    description='Equipment records, primary ownership periods, and contacts.',
)
