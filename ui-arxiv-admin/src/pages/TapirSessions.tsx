import {Grid, Table, TableCell, TableRow, useMediaQuery} from '@mui/material';
import {
    BooleanField,
    BooleanInput,
    Create,
    Datagrid,
    DateField,
    DateFieldProps,
    DateInput,
    Edit,
    EmailField,
    Filter,
    List,
    NumberField,
    NumberInput,
    ReferenceField,
    ReferenceInput,
    SelectInput,
    SimpleForm,
    SimpleList,
    SortPayload,
    TextField,
    TextInput,
    useListContext,
    useRecordContext,
    AutocompleteInput,
    useFormGroupContext,
    FormGroupContextProvider,
    useEditContext, useFormGroup, EditProps,
} from 'react-admin';


import LinkIcon from '@mui/icons-material/Link';


import { addDays } from 'date-fns';

import React, {useContext, useEffect} from "react";
import { useFormContext } from 'react-hook-form';
// import SaveOnlyActions from "../bits/SaveOnlyActions";
import SaveOnlyToolbar from "../bits/SaveOnlyToolbar";

const presetOptions = [
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
];

const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return { preset: preset, startDate: addDays(today, -1), endDate: today };
        case 'last_7_days':
            return { preset: preset, startDate: addDays(today, -7), endDate: today };
        case 'last_28_days':
            return { preset: preset, startDate: addDays(today, -28), endDate: today };
        default:
            return { preset: preset, startDate: null, endDate: null };
    }
};

const TapirSessionFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const preset = event.target.value;
        setFilters({
            ...filterValues,
            preset: preset,
        });
    };

    return (
        <Filter {...props}>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <ReferenceInput label="User" source="user_id" reference="users" alwaysOn>
                <AutocompleteInput
                    optionText={(choice) => `${choice.first_name} ${choice.last_name} (${choice.email})`}
                    filterToQuery={(searchText: string) => ({ clue: searchText })} // Filter dynamically
                />
            </ReferenceInput>

        </Filter>
    );
};


export const TapirSessionList = () => {
    const sorter: SortPayload = {field: 'tapirSession_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    const defaultDates = calculatePresetDates('last_28_days');
    return (
        <List filters={<TapirSessionFilter />}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.tapirSessionname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="edit" sort={sorter}>
                    <NumberField source="id" label="TapirSession ID" />
                    <ReferenceField source="user_id" reference="users"
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                        {"  ("}
                        <TextField source={"username"} />
                        {")"}
                    </ReferenceField>
                    <DateField source="last_reissue" showTime />
                    <DateField source="start_time" showTime />
                    <DateField source="end_time" showTime />
                </Datagrid>
            )}
        </List>
    );
};


const TapirSessionTitle = () => {
    const record = useRecordContext();
    return <span>TapirSession {record ? `"${record.last_name}, ${record.first_name}" - ${record.email}` : ''}</span>;
};

const CloseSessionToggle: React.FC = () => {
    const formGroupState = useFormGroup("tapirSessions");
    const { watch } = useFormContext();
    const formValues = watch();

    console.log("formGroupState record: " + JSON.stringify(formValues));
    console.log("formGroupState: " + JSON.stringify(formGroupState));

    return <BooleanInput source="close_session" label="Close session" disabled={formValues?.close_session} />;
};


export const TapirSessionEdit: React.FC<EditProps> = (props) => {
/*
    useEffect(() => {
        const endTime = getValues(getSource('end_time'));
        const isCloseSession = endTime !== null && endTime !== undefined;
        setValue(getSource('close_session'), isCloseSession); // Set close_session based on end_time
    }, [getSource, getValues, setValue]);
    xrr
 */

    return (
        <Edit {...props} >
            <SimpleForm toolbar={<SaveOnlyToolbar />}>
                <FormGroupContextProvider name="tapirSession">
                    <Table>
                        <TableRow>
                            <TableCell>Session ID</TableCell>
                            <TableCell><NumberField source="id" label="TapirSession ID" /></TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>User</TableCell>
                            <TableCell>
                                <ReferenceField source="user_id" reference="users"
                                                link={(record, reference) => `/${reference}/${record.id}`} >
                                    <TextField source={"last_name"} />
                                    {", "}
                                    <TextField source={"first_name"} />
                                </ReferenceField>
                            </TableCell>
                            <TableCell>
                                <ReferenceField source="user_id" reference="users"
                                                link={(record, reference) => `/${reference}/${record.id}`} >
                                    <TextField source={"username"} />
                                </ReferenceField>
                            </TableCell>
                            <TableCell>
                                <ReferenceField source="user_id" reference="users">
                                    <EmailField source={"email"} />
                                </ReferenceField>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Start time</TableCell>
                            <TableCell>
                                <DateField source="start_time" showTime />
                            </TableCell>
                            <TableCell>End time</TableCell>
                            <TableCell>
                                <DateField source="end_time" showTime />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                <CloseSessionToggle />
                            </TableCell>
                            <TableCell></TableCell>
                        </TableRow>
                    </Table>
                </FormGroupContextProvider>
            </SimpleForm>
        </Edit>
    );
}
