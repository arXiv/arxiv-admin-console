/*
  list of admin actions for a paper

 */

import {
    useListController,
    Pagination,
    Datagrid,
    TextField,
    Filter,
    BooleanInput,
    ReferenceField,
    DateInput,
    ListContextProvider, Identifier,
} from 'react-admin';
import React from 'react';
import ISODateField from "./ISODateFiled";
import UserNameField from "./UserNameField";
import Paper from '@mui/material/Paper';


const AdminLogList: React.FC<{paper_id?: string, submission_id?: Identifier}> = ({paper_id, submission_id}) => {
    const controllerProps = useListController({
        resource: 'admin_logs',
        filter: { paper_id: paper_id, submission_id: submission_id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (!paper_id && !submission_id) return null;
    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <Paper >
        <ListContextProvider value={controllerProps}>
            <Datagrid
                bulkActionButtons={false}
                rowClick={false}
                empty={<p><b>No admin logs</b></p>}
            >
                {
                    /*
                            <th>Time</th>
                            <th>Username</th>
                            <th>Program/Command</th>
                            <th>Sub Id</th>
                            <th>Log text</th>

                     */
                }
                <ISODateField source={"created"} label={"Time"} showTime={true} />
                <ReferenceField reference={'users-by-username'} source={'username'} label={'User'} link={(record) => `/users/${record.user_id}/edit`} >
                    <UserNameField withUsername />
                </ReferenceField>
                <TextField source="program" label={"Program"} />
                <TextField source="command" label={"Command"} />
                <ReferenceField reference="submissions" source="submission_id" label="SubID">
                    <TextField source="id" />
                </ReferenceField>
                <TextField source="logtext" label={"Log Text"} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
        </Paper>
    );
};


export const AdminLogFilter = (props: any) => {
    return (
        <Filter {...props}>
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" />
        </Filter>
    );
};

export default AdminLogList;
