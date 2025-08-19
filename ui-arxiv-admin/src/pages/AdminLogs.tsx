import { useMediaQuery } from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
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
    ReferenceField,
    NumberField,
    DateInput, useListContext, SelectInput, ListContextProvider, useDataProvider, useGetList
} from 'react-admin';

import React from "react";
import ISODateField from "../bits/ISODateFiled";


export const AdminLogFilter = (props: any) => {
    return (
        <Filter {...props}>
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" />
        </Filter>
    );
};

interface AdminLogsProps {
    showLogs: boolean;
}
export const AdminLogs = (props: AdminLogsProps) => {
    const record = useRecordContext();
    if (!record) return null;
    if (!props.showLogs)
        return null;

    // @ts-ignore
    return (
        <List filters={<AdminLogFilter />} resource="admin_logs" filter={{submission_id: record.id}} >
            <Datagrid size="small" bulkActionButtons={false}>
                <ISODateField source="created" />
                <TextField source="username" />
                <TextField source="logtext" />
            </Datagrid>
        </List>
    );
};


