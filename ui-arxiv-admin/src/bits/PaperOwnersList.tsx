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
    ReferenceField,
    Pagination,
    BooleanField,
    useListContext, useNotify, Identifier,
    useRefresh, EmailField
} from 'react-admin';
import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import {paths as adminApi} from "../types/admin-api";
import {RuntimeContext} from "../RuntimeContext";
import UserNameField from "./UserNameField";

type UpdatePaperOwnersRequestType = adminApi['/v1/paper_owners/update-paper-owners']['post']['requestBody']['content']['application/json'];

// Create a separate component for bulk actions to properly use hooks
const PaperOwnerBulkActionButtons: React.FC<{documentId: Identifier}> = ({documentId}) => {
    const listContext = useListContext();
    const runtimeProps = React.useContext(RuntimeContext);
    const notify = useNotify();
    const refresh = useRefresh();

    async function setPaperOwners(selectedIds: string[], is_owner: boolean, valid: boolean) {

        const body: UpdatePaperOwnersRequestType = {
            document_id: documentId.toString(),
            owners: is_owner ? selectedIds : [],
            nonowners: !is_owner ? selectedIds : [],
            valid: valid,
        }

        const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + "/paper_owners/update-paper-owners",
            {
                method: "POST", headers: {"Content-Type": "application/json",}, body: JSON.stringify(body),
            });
        if (response.ok) {
            notify("Updated", { type: 'info' });
            refresh();
        } else {
            notify(await response.text(), { type: 'warning' });
        }
    }


    const handleIsOwner = async () => {
        const selectedIds = listContext.selectedIds;
        console.log('Selected IDs:', selectedIds);

        if (selectedIds.length === 0) {
            notify("No document selected", { type: 'warning' });
            return;
        }
        await setPaperOwners(selectedIds, true, true);
    };

    const handleIsNotOwner = async () => {
        const selectedIds = listContext.selectedIds;
        console.log('Selected IDs:', selectedIds);

        if (selectedIds.length === 0) {
            notify("No document selected", { type: 'warning' });
            return;
        }
        await setPaperOwners(selectedIds, false, true);
    };

    const handleRevoked = async () => {
        const selectedIds = listContext.selectedIds;
        console.log('Selected IDs:', selectedIds);

        if (selectedIds.length === 0) {
            notify("No document selected", { type: 'warning' });
            return;
        }
        await setPaperOwners(selectedIds, false, false);
    };

    return (
        <Box display={"flex"} flexDirection={"row"} sx={{gap: 3, m: 1}}>
            <Button
                id="owns_paper"
                name="owns_paper"
                variant="contained"
                onClick={handleIsOwner}
            >
                Author
            </Button>
            <Button
                id="not_owns_paper"
                name="not_owns_paper"
                variant="contained"
                onClick={handleIsNotOwner}
            >
                Not author
            </Button>
            <Button
                id="not_owns_paper"
                name="not_owns_paper"
                variant="contained"
                color="warning"
                onClick={handleRevoked}
            >
                Revoke
            </Button>
        </Box>
    );
};

const PaperOwnersList: React.FC<{document_id?: Identifier}> = ({document_id}) => {
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
                size={"small"}
                rowClick="edit"
                bulkActionButtons={<PaperOwnerBulkActionButtons documentId={document_id} />}
                empty={<p><b>No owners for this paper</b></p>}
            >
                <BooleanField source="flag_author" label={"Owner"} />
                <BooleanField source="valid" label={"Valid"} />
                <ReferenceField reference="users" source="user_id" label="Name">
                    <UserNameField />
                </ReferenceField>
            </Datagrid>
            <Pagination />
        </ListContextProvider>
    );
};

export default PaperOwnersList;
