/*
  Paper list by a single user.

  If you are looking for a list of owners who own a paper, this is not it.
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
type PaperAuthoredRequestType = adminApi['/v1/paper_owners/update-authorship']['post']['requestBody']['content']['application/json'];

// Create a separate component for bulk actions to properly use hooks
const BulkActionButtons: React.FC<{userId: Identifier}> = ({userId}) => {
    const listContext = useListContext();
    const runtimeProps = React.useContext(RuntimeContext);
    const nofify = useNotify();
    const refresh = useRefresh();

    async function setAuthored(selectedIds: string[], authored: boolean) {

        const body: PaperAuthoredRequestType = {
            user_id: userId.toString(),
            authored: authored ? selectedIds : [],
            not_authored: !authored ? selectedIds : [],
        }

        const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/paper_owners/update-authorship",
            {
                method: "POST", headers: {"Content-Type": "application/json",}, body: JSON.stringify(body),
            });
        if (response.ok) {
            nofify("Updated", { type: 'info' });
            refresh();
        } else {
            nofify(await response.text(), { type: 'warning' });
        }
    }


    const handleAuthoredAll = async () => {
        const selectedIds = listContext.selectedIds;
        console.log('Selected IDs:', selectedIds);

        if (selectedIds.length === 0) {
            nofify("No document selected", { type: 'warning' });
            return;
        }
        await setAuthored(selectedIds, true);
    };

    const handleAuthoredNone = async () => {
        const selectedIds = listContext.selectedIds;
        console.log('Selected IDs:', selectedIds);

        if (selectedIds.length === 0) {
            nofify("No document selected", { type: 'warning' });
            return;
        }
        await setAuthored(selectedIds, false);
    };

    return (
        <Box display={"flex"} flexDirection={"row"} sx={{gap: 1, m: 1}}>
            <Button
                id="authored_all"
                name="authored_all"
                variant="outlined"
                onClick={handleAuthoredAll}
            >
                I'm an author.
            </Button>
            <Button
                id="authored_none"
                name="authored_none"
                variant="outlined"
                onClick={handleAuthoredNone}
            >
                I am not an author.
            </Button>
        </Box>
    );
};

const OwnedPaperList: React.FC = () => {
    const record = useRecordContext();
    if (!record) return null;

    const controllerProps = useListController({
        resource: 'paper_owners',
        filter: { user_id: record.id },
        sort: { field: 'id', order: 'DESC' },
        perPage: 5,
        disableSyncWithLocation: true,
    });

    if (controllerProps.isLoading) return null;
    if (controllerProps.error) return <p>Error loading paper ownership data.</p>;

    return (
        <ListContextProvider value={controllerProps}>
            <Datagrid
                rowClick="edit"
                empty={<p><b>User owns none of papers</b></p>}
                bulkActionButtons={<BulkActionButtons userId={record.id} />}
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

export default OwnedPaperList;
