/*
  list of admin actions for a paper

 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    TextField,
    ReferenceField,
    Pagination,
} from 'react-admin';
import React from 'react';
import ISODateField from "./ISODateFiled";


const AdminLogList: React.FC<{paper_id?: string}> = ({paper_id}) => {
    if (!paper_id) return null;

    const controllerProps = useListController({
        resource: 'admin_logs',
        filter: { paper_id: paper_id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid
                bulkActionButtons={false}
                rowClick="edit"
                empty={<p><b>No admin logs???</b></p>}
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
                <TextField source="username" label={"Username"} />
                <TextField source="program" label={"Program"} />
                <TextField source="command" label={"Command"} />
                <ReferenceField reference="submissions" source="submission_id" label="SubID">
                    <TextField source="id" />
                </ReferenceField>
                <TextField source="logtext" label={"Log Text"} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default AdminLogList;
