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
    DateInput, useListContext, SelectInput, AutocompleteInput
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
            <ReferenceField source="user_id" reference="users" label={"User"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <TextInput source="archive" />
            <TextInput source="subject_class" />

            <BooleanInput source="is_public" label={"Public"}/>
            <BooleanInput source="no_email" label={"No Email"}/>
            <BooleanInput source="no_web_email" label={"No Web Email"}/>
            <BooleanInput source="no_reply_to" label={"No Reply-To"}/>
            <BooleanInput source="daily_update" label={"Daily Update"}/>
        </SimpleForm>
    </Edit>
);

export const ModeratorCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceInput source="user_id" reference="users">
                <AutocompleteInput
                    optionText={(record) => `${record.last_name}, ${record.first_name} (${record.email}) ${record.id}`}
                />
            </ReferenceInput>

            <TextInput source="archive" />
            <TextInput source="subject_class" />

            <BooleanInput source="is_public" label={"Public"}/>
            <BooleanInput source="no_email" label={"No Email"}/>
            <BooleanInput source="no_web_email" label={"No Web Mail"}/>
            <BooleanInput source="no_reply_to" label={"No Reply-To"}/>
            <BooleanInput source="daily_update" label={"Daily Update"}/>

        </SimpleForm>
    </Create>
);


