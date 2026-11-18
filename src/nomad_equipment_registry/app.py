from nomad.config.models.plugins import AppEntryPoint
from nomad.config.models.ui import (
    App,
    Column,
    Dashboard,
    Layout,
    Menu,
    MenuItemTerms,
    MenuItemVisibility,
    SearchQuantities,
    WidgetTerms,
)

SCHEMA = 'nomad_equipment_registry.schema.EquipmentRecord'
FIELDS = {
    'equipment_id': 'Equipment ID',
    'equipment_name': 'Equipment name',
    'category': 'Category',
    'department': 'Department',
    'location': 'Location',
    'status': 'Status',
    'equipment_group': 'Equipment group',
    'manufacturer_model': 'Manufacturer / model',
    'serial_inventory_number': 'Serial / inventory number',
}


def search_quantity(field):
    return f'data.{field}#{SCHEMA}'


def widget_layout(index):
    grids = {'sm': (2, 6), 'md': (4, 4), 'lg': (4, 6), 'xl': (4, 7), 'xxl': (4, 9)}
    return {
        breakpoint: Layout(w=width, h=5, x=(index % columns) * width, y=(index // columns) * 5)
        for breakpoint, (columns, width) in grids.items()
    }


equipment_app = AppEntryPoint(
    name='Scientific Equipment Registry app',
    description='Browse and filter scientific equipment records.',
    app=App(
        label='Scientific Equipment Registry',
        path='scientific-equipment-registry',
        category='CBS',
        description='Find equipment by ID, department, location, category, and status.',
        search_quantities=SearchQuantities(
            include=[search_quantity(field) for field in FIELDS],
            exclude=['mainfile', 'entry_name', 'combine'],
        ),
        filters_locked={'section_defs.definition_qualified_name': [SCHEMA]},
        columns=[
            Column(
                search_quantity=search_quantity(field),
                label=label,
                selected=field not in {'manufacturer_model', 'serial_inventory_number'},
            )
            for field, label in FIELDS.items()
        ],
        dashboard=Dashboard(
            widgets=[
                WidgetTerms(
                    type='terms',
                    search_quantity=search_quantity(field),
                    title=FIELDS[field],
                    show_input=True,
                    layout=widget_layout(index),
                )
                for index, field in enumerate(
                    ('equipment_name', 'department', 'category', 'status')
                )
            ],
        ),
        menu=Menu(
            title='Filters',
            size='sm',
            items=[
                Menu(
                    title='Equipment',
                    items=[
                        MenuItemTerms(
                            search_quantity=search_quantity(field),
                            title=FIELDS[field],
                        )
                        for field in (
                            'equipment_id', 'category', 'department', 'location',
                            'status', 'equipment_group',
                        )
                    ],
                ),
                Menu(title='Visibility', items=[MenuItemVisibility()]),
            ],
        ),
    ),
)
