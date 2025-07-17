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
    useRefresh
} from 'react-admin';
import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import {paths as adminApi} from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext";


const PaperOwnersList: React.FC<{document_id: Identifier}> = ({document_id}) => {
    if (!document_id) return null;

    const controllerProps = useListController({
        resource: 'paper_owners',
        filter: { document_id: document_id },
        sort: { field: 'id', order: 'ASC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid
                rowClick="edit"
                bulkActionButtons={false}
                empty={<p><b>No owners for this paper</b></p>}
            >
                <BooleanField source="flag_author" label={"Author"} />
                <ReferenceField reference="documents" source="document_id" label="arXiv ID">
                    <TextField source="paper_id" />
                </ReferenceField>
                <ReferenceField
                    reference="documents"
                    source="document_id"
                    label="Title"
                    link={(record, _reference) => `https://arxiv.org/pdf/${record.paper_id}`}
                >
                    <TextField source="title" />
                </ReferenceField>
                <ReferenceField reference="documents" source="document_id" label="Dated" link={false}>
                    <DateField source="dated" />
                </ReferenceField>
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default PaperOwnersList;
