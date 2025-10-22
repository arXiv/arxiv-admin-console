import {Grid, Table, TableCell, TableRow, useMediaQuery, Box, Button, LinearProgress, Typography} from '@mui/material';
import ConsoleTitle from "../bits/ConsoleTitle";
import {
    BooleanInput,
    Create,
    Datagrid,
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
    useDataProvider,
    useNotify,
    useRefresh,
    useUnselectAll,
} from 'react-admin';


import LinkIcon from '@mui/icons-material/Link';


import {addDays} from 'date-fns';

import React, {useContext, useEffect, useState} from "react";
import {useFormContext} from 'react-hook-form';
// import SaveOnlyActions from "../bits/SaveOnlyActions";
import SaveOnlyToolbar from "../bits/SaveOnlyToolbar";
import ISODateField from "../bits/ISODateFiled";
import UserNameField from "../bits/UserNameField";
import Paper from "@mui/material/Paper";
import IPv4AddressInput from "../components/IPv4AddressInput";

const presetOptions = [
    {id: 'last_1_day', name: 'Last 1 Day'},
    {id: 'last_7_days', name: 'Last 7 Days'},
    {id: 'last_28_days', name: 'Last 28 Days'},
];

const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return {preset: preset, startDate: addDays(today, -1), endDate: today};
        case 'last_7_days':
            return {preset: preset, startDate: addDays(today, -7), endDate: today};
        case 'last_28_days':
            return {preset: preset, startDate: addDays(today, -28), endDate: today};
        default:
            return {preset: preset, startDate: null, endDate: null};
    }
};

const TapirSessionBulkActionButtons = () => {
    const listContext = useListContext();
    const notify = useNotify();
    const refresh = useRefresh();
    const unselectAll = useUnselectAll('tapir_sessions');
    const dataProvider = useDataProvider();
    const [isUpdating, setIsUpdating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentAction, setCurrentAction] = useState('');

    const handleBulkClose = async () => {
        const selectedIds = listContext.selectedIds;
        console.log('Close Sessions - Selected IDs:', selectedIds);

        if (selectedIds.length === 0) {
            notify("No Tapir sessions selected", {type: 'warning'});
            return;
        }

        setIsUpdating(true);
        setCurrentAction('Closing sessions');
        setProgress(0);

        const successes: string[] = [];
        const errors: string[] = [];
        const total = selectedIds.length;

        for (let i = 0; i < selectedIds.length; i++) {
            const id = selectedIds[i];
            try {
                await dataProvider.update('tapir_sessions', {
                    id: id,
                    data: {close_session: true},
                    previousData: {close_session: false},
                });
                successes.push(id);
            } catch (error) {
                errors.push(id);
            }

            // Update progress
            const completed = i + 1;
            const progressPercent = Math.round((completed / total) * 100);
            setProgress(progressPercent);
        }

        // Show final results
        if (successes.length > 0) {
            notify(`Closed ${successes.length} Tapir sessions`, {type: 'info'});
        }
        if (errors.length > 0) {
            notify(`Failed to close ${errors.length} Tapir sessions`, {type: 'warning'});
        }

        // Clean up
        setIsUpdating(false);
        setProgress(0);
        setCurrentAction('');
        unselectAll();
        refresh();
    };

    return (
        <Box display="flex" flexDirection="column" sx={{gap: 1, m: 1}}>
            {/* Progress Indicator */}
            {isUpdating && (
                <Box sx={{width: '100%', mb: 2}}>
                    <Box display="flex" alignItems="center" sx={{mb: 1}}>
                        <Typography variant="body2" sx={{mr: 1}}>
                            {currentAction}... ({progress}%)
                        </Typography>
                    </Box>
                    <LinearProgress
                        variant="determinate"
                        value={progress}
                        sx={{height: 6, borderRadius: 3}}
                    />
                </Box>
            )}

            {/* Action Buttons */}
            <Box display="flex" flexDirection="row" sx={{gap: 1}}>
                <Button
                    variant="contained"
                    color="secondary"
                    onClick={handleBulkClose}
                    disabled={isUpdating}
                >
                    Close
                </Button>
            </Box>
        </Box>
    );
};

const TapirSessionFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
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
            />
            <DateInput label="Start Date" source="start_date"/>
            <DateInput label="End Date" source="end_date"/>
            <TextInput label="ID" source="id" alwaysOn/>
            <ReferenceInput label="User" source="user_id" reference="users" alwaysOn>
                <AutocompleteInput
                    optionText={(choice) => `${choice.first_name} ${choice.last_name} (${choice.email})`}
                    filterToQuery={(searchText: string) => ({clue: searchText})} // Filter dynamically
                />
            </ReferenceInput>
            <BooleanInput label="Open session" source="is_open"/>
            <IPv4AddressInput label="Remote IP Address" source="remote_ip"/>
        </Filter>
    );
};


export const TapirSessionList = () => {
    return (
        <Box maxWidth={"lg"} sx={{ margin: '0 auto'}}>
            <ConsoleTitle>Tapir Sessions</ConsoleTitle>
        <List filters={<TapirSessionFilter/>}>
            <Datagrid rowClick="edit" bulkActionButtons={<TapirSessionBulkActionButtons/>}>
                <NumberField source="id" label="TapirSession ID"/>
                <ReferenceField source="user_id" reference="users"
                                link={(record, reference) => `/${reference}/${record.id}`}>
                    <TextField source={"last_name"}/>
                    {", "}
                    <TextField source={"first_name"}/>
                    {"  ("}
                    <TextField source={"username"}/>
                    {")"}
                </ReferenceField>
                <ISODateField source="last_reissue" showTime/>
                <ISODateField source="start_time" showTime/>
                <ISODateField source="end_time" showTime/>
                <TextField source="remote_ip" />
            </Datagrid>
        </List>
        </Box>
    );
};


const TapirSessionTitle = () => {
    const record = useRecordContext();
    return <span>Tapir Session {record ? `${record.id}` : ''}</span>;
};

const CloseSessionToggle: React.FC = () => {
    const {watch} = useFormContext();
    const formValues = watch();
    const isSessionClosed = formValues?.end_time !== null && formValues?.end_time !== undefined;

    console.log("formValues: " + JSON.stringify(formValues));
    console.log("isSessionClosed: " + isSessionClosed);

    return <BooleanInput source="close_session" label="Close session" disabled={isSessionClosed}/>;
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
        <Box display="flex" flexDirection="column" sx={{gap: 1, m: 1}} maxWidth="sm" alignItems={"center"}>
            <Edit {...props} component={"div"}>
                <ConsoleTitle><TapirSessionTitle /></ConsoleTitle>
                <Paper sx={{mt: "3em"}}>
                <SimpleForm toolbar={<SaveOnlyToolbar/>}>
                        <Table size={"small"}>
                            <TableRow>
                                <TableCell>Session ID</TableCell>
                                <TableCell><NumberField source="id" label="TapirSession ID"/></TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>User</TableCell>
                                <TableCell>
                                    <ReferenceField source="user_id" reference="users"
                                                    link={(record, reference) => `/${reference}/${record.id}`}>
                                        <UserNameField withEmail withUsername/>
                                    </ReferenceField>
                                </TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Start time</TableCell>
                                <TableCell>
                                    <ISODateField source="start_time" showTime/>
                                </TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>End time</TableCell>
                                <TableCell>
                                    <ISODateField source="end_time" showTime/>
                                </TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Remote IP Address</TableCell>
                                <TableCell>
                                    <TextField source="remote_ip" />
                                </TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>Remote Host</TableCell>
                                <TableCell>
                                    <TextField source="remote_host" />
                                </TableCell>
                            </TableRow>
                            <TableRow>
                                <TableCell>
                                    <CloseSessionToggle/>
                                </TableCell>
                                <TableCell></TableCell>
                            </TableRow>
                        </Table>
                </SimpleForm>
                </Paper>
            </Edit>
        </Box>
    );
}
