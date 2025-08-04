import React, {useState, useEffect} from 'react';

import {Grid, useMediaQuery, Table, TableRow, TableCell} from '@mui/material';
import {
    useDataProvider,
    List,
    SimpleList,
    Datagrid,
    TextField,
    BooleanField,
    NumberField,
    SortPayload,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    DateInput,
    SelectInput,
    useListContext,
    ReferenceField,
    Show,
    SimpleShowLayout, useGetOne, RecordContextProvider, Identifier, FieldProps,
} from 'react-admin';

import CategoryField from "../bits/CategoryField";

import PointValueBooleanField from "../bits/PointValueBooleanField";
import ISODateField from "../bits/ISODateFiled";
import UserNameField from "./UserNameField";

const EndorsementRequestFieldFilter = (props: any) => {
    return (
        <Filter {...props}>
            <TextInput label="First Name" source="endorsee_first_name"  />
            <TextInput label="Last Name" source="endorsee_last_name"  />
            <TextInput label="Email Address" source="endorsee_email" />
            <TextInput label="Username" source="endorsee_username"  />
            <TextInput label="Category" source="category"  />

            <BooleanInput label="Closed" source="positive" />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" defaultValue="true"/>
            <BooleanInput label="Suspect" source="suspected" defaultValue="false"/>

        </Filter>
    );
};


const EndorsementRequestListField: React.FC<FieldProps> = (props) => {
    const record = useRecordContext();
    if (!record) return null;
    const user_id = record[props.source];
    if (!user_id) return null;

    return (
        <List
            actions={false}
            resource="endorsement_requests"
            filter={{endorsee_id: user_id, }}
            empty={<span>No endorsement requests</span>}
        >
            <Datagrid rowClick="edit" bulkActionButtons={false} >
                <NumberField source="id" label={"ID"}/>

                <CategoryField label={"Category"} source="archive" sourceCategory="archive" sourceClass="subject_class" />
                <ISODateField source="issued_when" label={"Issued"}/>

                <BooleanField source="flag_valid" label={"Valid"} FalseIcon={null} />
                <PointValueBooleanField source="point_value" label={"Open"} />
            </Datagrid>
        </List>
    );
};

export default  EndorsementRequestListField;
