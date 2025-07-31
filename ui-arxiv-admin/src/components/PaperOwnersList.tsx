/*
  list of owners for a paper

  If you are looking for a list of papers owned by a user, this is not it.
 */

import {
    useListController,
    ListContextProvider,
    Datagrid,
    ReferenceField,
    Pagination,
    BooleanField,
    useListContext, useNotify, Identifier,
    useRefresh, useDataProvider
} from 'react-admin';
import React from 'react';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';

import {paths as adminApi} from "../types/admin-api";
import UserNameField from "../bits/UserNameField";

type UpdatePaperOwnersRequestType = adminApi['/v1/paper_owners/authorship/{action}']['put']['requestBody']['content']['application/json'];

// Create a separate component for bulk actions to properly use hooks
export const PaperOwnerBulkActionButtons: React.FC = () => {
    const listContext = useListContext();
    const notify = useNotify();
    const refresh = useRefresh();
    const dataProvider = useDataProvider();

    async function setPaperOwners(selectedIds: string[], is_owner: boolean, valid: boolean) {
        const body: UpdatePaperOwnersRequestType = {
            authored: is_owner ? selectedIds : [],
            not_authored: !is_owner ? selectedIds : [],
            valid: valid,
        }

        try {
            const response = await dataProvider.update("paper_owners/authorship",
                {
                    id: "update",  // This becomes "paper_owners/authorship/update"
                    data: body,
                    previousData: {}
                });
            console.log(JSON.stringify(response));
            notify("Updated", {type: 'info'});
            refresh();
        } catch (error: any) {
            console.error(JSON.stringify(error));
            notify(error?.detail || JSON.stringify(error), {type: 'warning'});
            refresh();
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
                bulkActionButtons={<PaperOwnerBulkActionButtons />}
                empty={<p><b>No owners for this paper</b></p>}
            >
                <BooleanField source="flag_author" label={"Author"} />
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
