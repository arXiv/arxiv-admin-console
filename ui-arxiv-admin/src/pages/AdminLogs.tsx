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

import { addDays } from 'date-fns';

import React from "react";
import ISODateField from "../bits/ISODateFiled";


const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return { startDate: addDays(today, -1), endDate: today };
        case 'last_7_days':
            return { startDate: addDays(today, -7), endDate: today };
        case 'last_28_days':
            return { startDate: addDays(today, -28), endDate: today };
        default:
            return { startDate: null, endDate: null };
    }
};

const AdminLogFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const { startDate, endDate } = calculatePresetDates("");
        setFilters({
            ...filterValues,
            startDate: startDate ? startDate.toISOString().split('T')[0] : '',
            endDate: endDate ? endDate.toISOString().split('T')[0] : '',
        });
    };

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


