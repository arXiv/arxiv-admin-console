import { useMediaQuery } from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    NumberField,
    BooleanField,
    SortPayload,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    useListContext, SelectInput, EditButton
} from 'react-admin';

// import { addDays } from 'date-fns';

import React from "react";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import PlainTextInput from '../bits/PlainTextInput';

/*
    archive: Mapped[str] = mapped_column(ForeignKey('arXiv_archives.archive_id'), primary_key=True, nullable=False, server_default=FetchedValue())
    subject_class: Mapped[str] = mapped_column(String(16), primary_key=True, nullable=False, server_default=FetchedValue())
    definitive: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    active: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("'0'"))
    category_name: Mapped[Optional[str]]
    endorse_all: Mapped[Literal['y', 'n', 'd']] = mapped_column(Enum('y', 'n', 'd'), nullable=False, server_default=text("'d'"))
    endorse_email: Mapped[Literal['y', 'n', 'd']] = mapped_column(Enum('y', 'n', 'd'), nullable=False, server_default=text("'d'"))
    papers_to_endorse: Mapped[int] = mapped_column(SmallInteger, nullable=False, server_default=text("'0'"))
    endorsement_domain: Mapped[Optional[str]] = mapped_column(ForeignKey('arXiv_endorsement_domains.endorsement_domain'), index=True)
 */


const BibFeedFilter = (props: any) => {

    return (
        <Filter {...props}>
            <TextInput label="Name" source="name" alwaysOn />
            <TextInput label="URI" source="uri" />
            <TextInput label="Identifier" source="identifier" />
            <BooleanInput label="Enabled" source="enabled" />
        </Filter>
    );
};



/*
    {
        "id": 3,
        "name": "ManualOverride",
        "priority": 99,
        "uri": null,
        "identifier": null,
        "version": null,
        "strip_journal_ref": 0,
        "concatenate_dupes": null,
        "max_updates": null,
        "email_errors": null,
        "prune_ids": null,
        "prune_regex": null,
        "enabled": 0
    },
 */

export const BibFeedList = () => {
    const sorter: SortPayload = {field: 'archive', order: 'ASC'};
    return (
        <Box sx={{ margin: '0 auto'}}>
            <ConsoleTitle>Bib Feeds</ConsoleTitle>
            <List filters={<BibFeedFilter />}>
            <Datagrid rowClick={"edit"}  sort={sorter} bulkActionButtons={false}>
                <TextField source="id" />
                <TextField source="name" />
                <NumberField source="priority" />
                <TextField source="uri" label="URI"/>
                <TextField source="identifier" />
                <TextField source="version" />
                <BooleanField source="strip_journal_ref" FalseIcon={null} />
                <NumberField source="concatenate_dupes" />
                <NumberField source="max_updates" />
                <TextField source="email_errors" />
                <TextField source="prune_ids" />
                <TextField source="prune_regex" />
                <BooleanField source="enabled" FalseIcon={null} />
            </Datagrid>
        </List>
        </Box>
    );
};


const BibFeedTitle = () => {
    const record = useRecordContext();
    return <span>Feed {record ? `[${record.id}] "${record.name}" - ${record.identifier}` : ''}</span>;
};

const BibFeedFormInputs = () => (
    <>
        <TextInput source="name" />
        <TextInput source="uri" />
        <TextInput source="identifier" />
        <Box sx={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 1,
            width: '100%'
        }}>
            <TextInput source="version" fullWidth helperText={false}/>
            <NumberInput source="priority" fullWidth helperText={false} />
            <BooleanInput source="strip_journal_ref" fullWidth sx={{ml: 3, mt: 2}} helperText={false} />
            <NumberInput source="concatenate_dupes" fullWidth helperText={false} />
            <BooleanInput source="enabled" fullWidth sx={{ml: 3, mt: 2}} helperText={false} />
            <NumberInput source="max_updates" fullWidth helperText={false} />
        </Box>
        <PlainTextInput source="prune_ids" multiline={true} minRows={1} fullWidth helperText={false} resizable={"vertical"} />
        <PlainTextInput source="prune_regex" multiline={true} minRows={1} fullWidth helperText={false} resizable={"vertical"} />
        <TextInput source="email_errors" />
    </>
);

export const BibFeedEdit = () => (
    <Box maxWidth={"xl"} minWidth={"600px"} sx={{margin: '0 auto'}} >
        <Edit component={"div"}>
            <ConsoleTitle><BibFeedTitle /></ConsoleTitle>
            <Paper>
                <SimpleForm>
                    <BibFeedFormInputs />
                </SimpleForm>
            </Paper>
        </Edit>
    </Box>
);

export const BibFeedCreate = () => (
    <Box maxWidth={"xl"} minWidth={"600px"} sx={{margin: '0 auto'}} >
        <Create component={"div"}>
            <ConsoleTitle>Create New Bib Feed</ConsoleTitle>
            <Paper>
                <SimpleForm>
                    <BibFeedFormInputs />
                </SimpleForm>
            </Paper>
        </Create>
    </Box>
);

