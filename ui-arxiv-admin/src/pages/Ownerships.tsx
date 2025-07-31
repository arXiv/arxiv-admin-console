import { useMediaQuery } from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    BooleanField,
    SortPayload,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    Create,
    Filter,
    BooleanInput,
    ReferenceField,
    DateInput, useListContext, SelectInput,
    useDataProvider,
    useNotify,
    useRefresh,
    useListContext as useListContextForActions,
    TopToolbar, EmailField
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import ButtonGroup from "@mui/material/ButtonGroup";
import ISODateField from "../bits/ISODateFiled";
import CategoryInput from "../bits/CategoryInput";
import UserChooser from "../components/UserChooser";
import SingleUserInputField from "../components/SingleUserInputField";
import UserNameField from "../bits/UserNameField";
/*
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_ownership_requests.request_id'), index=True)
 */

import {paths as adminApi, components as adminComponents} from "../types/admin-api";
import {PaperOwnerBulkActionButtons} from "../components/PaperOwnersList";

type OwnershipsUpdateT = adminComponents['schemas']['PaperOwnershipUpdateRequest'];
type UpdatePaperOwnersRequestType = adminApi['/v1/paper_owners/authorship/{action}']['put']['requestBody']['content']['application/json'];

const OwnershipFilter = (props: any) => {

    return (
        <Filter {...props}>
            <SingleUserInputField source={"user_id"} label={"Owner"} alwaysOn variant={"dialog"}/>
            <TextInput label="Doc" source="document_id"  />
            <TextInput label="Paper" source="paper_id"   />
            <TextInput source={"first_name"}  />
            <TextInput source={"last_name"}  />
            <TextInput source={"email"}  />
            <BooleanInput label="Valid" source="flag_valid" />
            <BooleanInput label="Auto" source="flag_auto" />
        </Filter>
    );
};

/*
const OwnershipBulkActions = () => {
    const { selectedIds } = useListContextForActions();
    const dataProvider = useDataProvider();
    const notify = useNotify();
    const refresh = useRefresh();

    const handleBulkAuthorshipUpdate = async (action: 'author' | 'not_author' | 'invalidate') => {
        if (selectedIds.length === 0) {
            notify('Please select at least one ownership record', { type: 'warning' });
            return;
        }

        try {
            const requestBody: UpdatePaperOwnersRequestType = {
                authored: action === 'author' ? selectedIds.map(id => id.toString()) : [],
                not_authored: action === 'author' ? [] : selectedIds.map(id => id.toString()),
                valid: action === 'invalidate' ? false : undefined,
            };

            await dataProvider.update("paper_owners/authorship/", {
                id: "update",
                data: requestBody,
                previousData: {}
            });

            let message = '';
            switch (action) {
                case 'author':
                    message = `${selectedIds.length} record(s) marked as author`;
                    break;
                case 'not_author':
                    message = `${selectedIds.length} record(s) marked as not author`;
                    break;
                case 'invalidate':
                    message = `${selectedIds.length} record(s) invalidated`;
                    break;
            }

            notify(message, { type: 'success' });
            refresh();
        } catch (error: any) {
            console.error('Error updating authorship:', error);
            notify(error?.detail || 'Failed to update authorship', { type: 'error' });
        }
    };

    return (
        <>
            <Button
                onClick={() => handleBulkAuthorshipUpdate('author')}
                color="primary"
                variant="contained"
                disabled={selectedIds.length === 0}
            >
                Author
            </Button>
            <Button
                onClick={() => handleBulkAuthorshipUpdate('not_author')}
                color="secondary"
                variant="contained"
                disabled={selectedIds.length === 0}
            >
                Not Author
            </Button>
            <Button
                onClick={() => handleBulkAuthorshipUpdate('invalidate')}
                color="error"
                variant="contained"
                disabled={selectedIds.length === 0}
            >
                Invalidate
            </Button>
        </>
    );
};
*/


export const OwnershipList = () => {
    return (
        <List filters={<OwnershipFilter />}>
            <Datagrid rowClick="edit" bulkActionButtons={<PaperOwnerBulkActionButtons />}>
                <ReferenceField reference={"documents"} source={"document_id"} >
                    <TextField source={"id"} />
                </ReferenceField>

                <ReferenceField reference={"users"} source={"user_id"} label={"Owner"} link={"edit"}>
                    <UserNameField withEmail withUsername/>
                </ReferenceField>

                <ISODateField source={"date"} />

                <BooleanField source={"flag_author"} label={"Author"}/>
                <BooleanField source={"valid"} />
                <BooleanField source={"flag_auto"} label={"Auto"}/>
            </Datagrid>
        </List>
    );
};


const OwnershipTitle = () => {
    const record = useRecordContext();
    return <span>Ownership {record ? `"${record.document_id}` : ''}</span>;
};

export const OwnershipEdit = () => (
    <Edit title={<OwnershipTitle />}>
        <SimpleForm>
            <ReferenceField source="user_id" reference="users" label={"Owner"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ReferenceField source="added_by" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ISODateField source="date" />
            <ReferenceField source="document_id" reference="documents" label={"Paper"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"paper_id"} /> {" Title: "}
                <TextField source={"title"} />{" Authors: "}
                <TextField source={"authors"} />{"  "}

            </ReferenceField>

            <BooleanInput source="valid" label={"Valid"} />

            <Typography>Author: </Typography>
            <BooleanField source="flag_author" label={"Author"} />
            <Typography>Auto: </Typography>
            <BooleanField source="flag_auto" label={"Auto"} />

        </SimpleForm>
    </Edit>
);

export const OwnershipCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>

            <TextInput source="archive" />

            <TextInput source="subject_class" />
            <BooleanInput source="flag_valid" label={"Valid"}/>

            <TextInput source="type" />
            <NumberInput source="point_value" label={"Point"} />
            <DateInput source="issued_when" label={"Issued"} />

        </SimpleForm>
    </Create>
);


