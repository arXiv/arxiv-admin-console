/*
  Compact, read-only list of owners for a paper
 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    ReferenceField,
    Pagination,
} from 'react-admin';
import BooleanField from "../bits/BooleanNumberField";

import React from 'react';

import UserNameField from "../bits/UserNameField";

const PaperOwnersReadOnlyList: React.FC<{document_id?: string | number}> = ({document_id}) => {
    if (!document_id) return null;

    const controllerProps = useListController({
        resource: 'paper_owners',
        filter: { document_id: document_id },
        sort: { field: 'id', order: 'ASC' },
        perPage: 10,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid
                size={"small"}
                rowClick={false}
                bulkActionButtons={false}
                empty={<p><b>No owners for this paper</b></p>}
                sx={{
                    '& .RaDatagrid-tableWrapper': {
                        minWidth: 'auto'
                    }
                }}
            >
                <ReferenceField reference="users" source="user_id" label="Name">
                    <UserNameField />
                </ReferenceField>
                <BooleanField source="flag_author" label={"Author"} />
                <BooleanField source="valid" label={"Valid"} />
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default PaperOwnersReadOnlyList;
