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
    useRecordContext, DateField, EmailField,
} from 'react-admin';

const membershipInstitutionFilters = [
    <TextInput source="name" label="Search" alwaysOn />,
];

export const MembershipInstitutionList = () => (
    <List filters={membershipInstitutionFilters}>
        <Datagrid rowClick={"show"}>
            <TextField source="name" />
            <TextField source="note" />
            <EmailField source="email" />
            <TextField source="contact_name" />
        </Datagrid>
    </List>
);

const MembershipInstitutionTitle = () => {
    const record = useRecordContext();
    return <span>membershipInstitution {record ? `"${record.name}"` : ''}</span>;
};

