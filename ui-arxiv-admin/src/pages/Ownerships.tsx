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
    DateInput, useListContext, SelectInput
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
import Typography from "@mui/material/Typography";
import ISODateField from "../bits/ISODateFiled";
import CategoryInput from "../bits/CategoryInput";
import UserChooser from "../components/UserChooser";
import SingleUserInputField from "../components/SingleUserInputField";
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


export const OwnershipList = () => {
    return (
        <List filters={<OwnershipFilter />}>
            <Datagrid rowClick="edit">
                <ReferenceField reference={"documents"} source={"document_id"} >
                    <TextField source={"id"} />
                </ReferenceField>

                <ReferenceField reference={"users"} source={"user_id"} >
                    <TextField source={"first_name"} /> {" "}
                    <TextField source={"last_name"} />
                </ReferenceField>

                <ISODateField source={"date"} />

                <ReferenceField reference={"users"} source={"added_by"} >
                    <TextField source={"first_name"} /> {" "}
                    <TextField source={"last_name"} />
                </ReferenceField>

                <TextField source={"remote_addr"} />
                <TextField source={"remote_host"} />

                <BooleanField source={"valid"} />
                <BooleanField source={"flag_author"} label={"Author"}/>
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


