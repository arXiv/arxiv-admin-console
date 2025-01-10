import { useMediaQuery } from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    SortPayload,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    DateField,
    ReferenceField,
    NumberField,
    DateInput, useListContext, SelectInput
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
import CategoryField from "./bits/CategoryField";
/*
    id: str
    user_id: int
    archive: str
    subject_class: Optional[str]
    is_public: bool
    no_email: bool
    no_web_email: bool
    no_reply_to: bool
    daily_update: bool
 */


const ModeratorFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="Subject" source="archive" alwaysOn  />
            <TextInput label="Class" source="subject_class" alwaysOn />
            <TextInput label="Last name" source="last_name" />
            <TextInput label="First name" source="first_name" />
        </Filter>
    );
};


export const ModeratorList = () => {
    const sorter: SortPayload = {field: 'id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<ModeratorFilter />}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.moderatorname}
                    tertiaryText={record => record.email}
                />
            ) : (

                <Datagrid rowClick="show" sort={sorter}>
                    <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category" />

                    <ReferenceField source="user_id" reference="users" label={"Moderator"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                        {" ("}
                        <TextField source={"id"} />
                        {")"}
                    </ReferenceField>

                    <ReferenceField source="user_id" reference="users" label={"Email"}
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <EmailField source={"email"} />
                    </ReferenceField>

                </Datagrid>
            )}
        </List>
    );
};


const ModeratorTitle = () => {
    const record = useRecordContext();
    return <span>Moderator {record ? `${record.paper_id}: ${record.title} by ${record.authors}` : ''}</span>;
};

export const ModeratorEdit = () => (
    <Edit title={<ModeratorTitle />}>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <TextInput source="archive" />

            <TextInput source="subject_class" />
            <BooleanInput source="flag_valid" label={"Valid"} />

            <TextInput source="type" />
            <NumberInput source="point_value" label={"Point"} />
            <DateInput source="issued_when" label={"Issued"} />

            <ReferenceField source="request_id" reference="moderator_request" label={"Request"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
            </ReferenceField>
        </SimpleForm>
    </Edit>
);

export const ModeratorCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <TextInput source="archive" />

            <TextInput source="subject_class" />
            <BooleanInput source="flag_valid" label={"Valid"}/>

            <TextInput source="type" />
            <NumberInput source="point_value" label={"Point"} />
            <DateInput source="issued_when" label={"Issued"} />

        </SimpleForm>
    </Create>
);


