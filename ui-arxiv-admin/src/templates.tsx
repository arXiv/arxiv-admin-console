import {
    List,
    Datagrid,
    TextField,
    ReferenceField,
    EditButton,
    Edit,
    Create,
    SimpleForm,
    ReferenceInput,
    TextInput,
    useRecordContext, DateField,
} from 'react-admin';

const templateFilters = [
    <TextInput source="long_name" label="Search" alwaysOn />,
    <ReferenceInput source="last_name" label="User" reference="users" />,
];

export const TemplateList = () => (
    <List filters={templateFilters}>
        <Datagrid rowClick={false}>
            <TextField source="id" />
            <TextField source="short_name" />
            <TextField source="long_name" />
            <TextField source="data" />
            <DateField source="update_date" />
            <TextField source="updater_last_name"  />
            <EditButton />
        </Datagrid>
    </List>
);

const TemplateTitle = () => {
    const record = useRecordContext();
    return <span>Template {record ? `"${record.short_name}"` : ''}</span>;
};

export const TemplateEdit = () => (
    <Edit title={<TemplateTitle />}>
        <SimpleForm>
            <TextInput source="id" disabled />
            <TextInput source="short_name" />
            <TextInput source="long_name" />
            <TextInput source="data" multiline rows={20} />
        </SimpleForm>
    </Edit>
);

export const TemplateCreate = () => (
    <Create>
        <SimpleForm>
            <TextInput source="short_name" />
            <TextInput source="long_name" />
            <TextInput source="data" multiline rows={20} />
        </SimpleForm>
    </Create>
);
