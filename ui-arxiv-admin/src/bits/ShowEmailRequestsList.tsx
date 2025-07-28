/*

 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    TextField,
    ReferenceField,
    Pagination,
    Identifier,
} from 'react-admin';
import React from 'react';
import UserNameField from "./UserNameField";
import ISODateField from "./ISODateFiled";


const ShowEmailsRequestsList: React.FC<{document_id?: Identifier}> = ({document_id}) => {
    if (!document_id) return null;

    const controllerProps = useListController({
        resource: 'show_email_requests',
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
                rowClick={false}
                empty={<p><b>No show emails requests</b></p>}
            >
                <TextField source={"id"} />
                <ReferenceField reference={"users"} source={"user_id"} label={"User"}>
                    <UserNameField />
                </ReferenceField>
                <ISODateField source={"dated"} showTime={true} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default ShowEmailsRequestsList;
