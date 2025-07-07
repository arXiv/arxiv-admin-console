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
    useRefresh
} from 'react-admin';
import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import {paths as aaaApi} from "../types/aaa-api";
import {RuntimeContext} from "../RuntimeContext";

type emailHistoryResponseType = aaaApi['/account/email/history/{user_id}/']['get']['responses']['200']['content']['application/json'];


const EmailHistoryList: React.FC = () => {
    const record = useRecordContext();
    if (!record) return null;

    const controllerProps = useListController({
        resource: 'user_email_history',
        filter: { user_id: record.id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid empty={<p><b>User has no email change history</b></p>} size="small" >
                <TextField source={"email"} />
                <DateField source={"start_date"} />
                <DateField source={"end_date"} />
                <TextField source={"changed_by"} label={"By"}/>
                <BooleanField source={"used"} />
            </Datagrid>
            <Pagination  />
        </ListContextProvider>
    );
};

export default EmailHistoryList;
