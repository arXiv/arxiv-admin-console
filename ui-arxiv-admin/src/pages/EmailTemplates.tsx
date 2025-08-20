import {
    List,
    Datagrid,
    TextField,
    EditButton,
    Edit,
    Create,
    SimpleForm,
    ReferenceInput,
    TextInput,
    useRecordContext,
} from 'react-admin';
import ISODateField from "../bits/ISODateFiled";

const templateFilters = [
    <TextInput source="id" label="Search" alwaysOn />,
];

export const EmailTemplateList = () => (
    <List filters={templateFilters}>
        <Datagrid rowClick={false}>
            <TextField source="id" />
            <TextField source="short_name" />
            <TextField source="long_name" />
            <TextField source="data" />
            <ISODateField source="update_date" />
            <TextField source="updater_last_name"  />
            <EditButton />
        </Datagrid>
    </List>
);

const TemplateTitle = () => {
    const record = useRecordContext();
    return <span>Template {record ? `"${record.short_name}"` : ''}</span>;
};

export const EmailTemplateEdit = () => (
    <Edit title={<TemplateTitle />}>
        <SimpleForm>
            <TextInput source="id" disabled />
            <TextInput source="short_name" />
            <TextInput source="long_name" />
            <TextInput source="data" multiline rows={20} />
        </SimpleForm>
    </Edit>
);

export const EmailTemplateCreate = () => (
    <Create>
        <SimpleForm>
            <TextInput source="short_name" />
            <TextInput source="long_name" />
            <TextInput source="data" multiline rows={20} />
        </SimpleForm>
    </Create>
);
