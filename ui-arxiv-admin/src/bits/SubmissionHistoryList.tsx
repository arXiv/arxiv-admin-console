/*
  list of owners for a paper

  If you are looking for a list of papers owned by a user, this is not it.
 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    TextField,
    DateField,
    useRecordContext,

    ReferenceField,
    Pagination,
    BooleanField,
    useListContext, useNotify, Identifier,
    useRefresh, DateTimeInput, EmailField
} from 'react-admin';
import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import {paths as adminApi} from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext";
import UserNameField from "./UserNameField";


const SubmissionHistoryList: React.FC<{document_id?: Identifier}> = ({document_id}) => {
    if (!document_id) return null;

    const controllerProps = useListController({
        resource: 'submissions',
        filter: { document_id: document_id },
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
                empty={<p><b>No submissions this paper???</b></p>}
            >
                {
                    /*
                            <th>Version</th>
                            <th>Date</th>
                            <th>Submitter</th>
                            <th>Email/Name on Submission</th>

                     */
                }
                <TextField source="version" label={"Version"} />
                <DateField source={"submit_time"} label={"Submit Time"} showTime={true}  />
                <ReferenceField reference="users" source="submitter_id" label="Submitter">
                    <UserNameField />
                </ReferenceField>
                <EmailField source="submitter_email" label={"Submitter Email"} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default SubmissionHistoryList;
