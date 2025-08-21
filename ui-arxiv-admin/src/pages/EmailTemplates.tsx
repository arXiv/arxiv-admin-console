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
    useRecordContext, ReferenceField,
} from 'react-admin';
import ISODateField from "../bits/ISODateFiled";
import Typography from "@mui/material/Typography";
import UserNameField from "../bits/UserNameField";

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
            <ReferenceField reference={"users"} source={"updated_by"} >
                <UserNameField />
            </ReferenceField>
            <EditButton />
        </Datagrid>
    </List>
);

const TemplateTitle = () => {
    const record = useRecordContext();
    return <span>Template {record ? `"${record.short_name}"` : ''}</span>;
};

export const EmailTemplateEdit = () => (
    <Edit title={<TemplateTitle />} actions={false}>
        <SimpleForm>
            <Typography component={"span"} >
                {"ID: "}
                <TextField source="id" />
            </Typography>
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
