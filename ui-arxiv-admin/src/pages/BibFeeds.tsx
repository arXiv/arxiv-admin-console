import { useMediaQuery, FormControlLabel, Checkbox } from '@mui/material';
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
    useListContext, SelectInput, EditButton,
    Toolbar,
    SaveButton
} from 'react-admin';
import { useWatch } from 'react-hook-form';

// import { addDays } from 'date-fns';

import React from "react";
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

interface ColumnToggleProps {
    columnName: string;
    label: string;
    checked: boolean;
    onToggle: (columnName: string) => void;
}

const ColumnToggle = ({ columnName, label, checked, onToggle }: ColumnToggleProps) => (
    <FormControlLabel
        control={
            <Checkbox
                checked={checked}
                onChange={() => onToggle(columnName)}
            />
        }
        label={label}
    />
);

export const BibFeedList = () => {
    const sorter: SortPayload = {field: 'archive', order: 'ASC'};
    const [columnVisibility, setColumnVisibility] = React.useState({
        id: false,
        email_errors: true,
        strip_journal_ref: true,
        prune_ids: true,
        prune_regex: true,
        concatenate_dupes: true,
        max_updates: true,
    });

    const toggleColumn = (columnName: string) => {
        setColumnVisibility(prev => ({
            ...prev,
            [columnName]: !prev[columnName as keyof typeof prev]
        }));
    };

    return (
        <Box sx={{ margin: '0 auto'}}>
            <ConsoleTitle>Bib Feeds</ConsoleTitle>
            <List filters={<BibFeedFilter />}>
                <Box sx={{ display: 'flex', gap: 1, mb: 1, ml: 2, alignItems: 'center' }}>
                    <ColumnToggle
                        columnName="id"
                        label="ID"
                        checked={columnVisibility.id}
                        onToggle={toggleColumn}
                    />
                    <ColumnToggle
                        columnName="strip_journal_ref"
                        label="Strip JRef"
                        checked={columnVisibility.strip_journal_ref}
                        onToggle={toggleColumn}
                    />
                    <ColumnToggle
                        columnName="prune_ids"
                        label="Prune IDs"
                        checked={columnVisibility.prune_ids}
                        onToggle={toggleColumn}
                    />
                    <ColumnToggle
                        columnName="prune_regex"
                        label="Prune Regex"
                        checked={columnVisibility.prune_regex}
                        onToggle={toggleColumn}
                    />
                    <ColumnToggle
                        columnName="concatenate_dupes"
                        label="Concatenate Dupes"
                        checked={columnVisibility.concatenate_dupes}
                        onToggle={toggleColumn}
                    />
                    <ColumnToggle
                        columnName="max_updates"
                        label="Max Updates"
                        checked={columnVisibility.max_updates}
                        onToggle={toggleColumn}
                    />
                    <ColumnToggle
                        columnName="email_errors"
                        label="Email Errors"
                        checked={columnVisibility.email_errors}
                        onToggle={toggleColumn}
                    />
                </Box>
                <Datagrid rowClick={"edit"}  sort={sorter} bulkActionButtons={false}>
                    <BooleanField source="enabled" FalseIcon={null} />
                    {columnVisibility.id &&<TextField source="id" />}

                    <TextField source="name" />
                    <NumberField source="priority" />
                    <TextField source="uri" label="URI"/>
                    <TextField source="identifier" />
                    <TextField source="version" />
                    {columnVisibility.strip_journal_ref && <BooleanField source="strip_journal_ref" FalseIcon={null} label={"Strip JREF"}/>}
                    {columnVisibility.concatenate_dupes && <NumberField source="concatenate_dupes" />}
                    {columnVisibility.max_updates && <NumberField source="max_updates" />}
                    {columnVisibility.email_errors && <TextField source="email_errors" />}
                    {columnVisibility.prune_ids && <TextField source="prune_ids" />}
                    {columnVisibility.prune_regex && <TextField source="prune_regex" />}
                </Datagrid>
            </List>
        </Box>
    );
};


const BibFeedTitle = () => {
    const record = useRecordContext();
    return <span>Feed {record ? `[${record.id}] "${record.name}" - ${record.identifier}` : ''}</span>;
};

const BibFeedToolbar = (props: any) => {
    const enabled = useWatch({ name: 'enabled' });
    const name = useWatch({ name: 'name' });
    const uri = useWatch({ name: 'uri' });

    const hasNameError = !name || name.trim() === '';

    let hasUriError = false;
    if (enabled && (!uri || uri.trim() === '')) {
        hasUriError = true;
    } else if (uri && uri.trim() !== '') {
        const validSchemas = ['http://', 'https://', 'ftp://', 'sftp://'];
        const hasValidSchema = validSchemas.some(schema => uri.toLowerCase().startsWith(schema));
        if (!hasValidSchema) {
            hasUriError = true;
        }
    }

    const hasErrors = hasNameError || hasUriError;

    return (
        <Toolbar {...props}>
            <SaveButton disabled={hasErrors} />
        </Toolbar>
    );
};

const BibFeedFormInputs = () => {
    const record = useRecordContext();
    const enabled = useWatch({ name: 'enabled' });
    const name = useWatch({ name: 'name' });
    const uri = useWatch({ name: 'uri' });

    const [errors, setErrors] = React.useState<Record<string, string>>({
        name: '',
        uri: ''
    });

    React.useEffect(() => {
        const newErrors: Record<string, string> = {};

        // Validate name
        if (!name || name.trim() === '') {
            newErrors.name = 'Name is required and cannot be empty';
        }

        // Validate URI
        if (enabled && (!uri || uri.trim() === '')) {
            newErrors.uri = 'URI is required when feed is enabled';
        } else if (uri && uri.trim() !== '') {
            const validSchemas = ['http://', 'https://', 'ftp://', 'sftp://'];
            const hasValidSchema = validSchemas.some(schema => uri.toLowerCase().startsWith(schema));
            if (!hasValidSchema) {
                newErrors.uri = 'URI must start with http://, https://, ftp://, or sftp://';
            }
        }

        setErrors(newErrors);
    }, [name, uri, enabled]);

    return (<>
        <BooleanInput source="enabled" fullWidth sx={{ml: 3, my: 1}} helperText={false} label={`Feed Enabled for ${record?.id ? '[' + record.id + '] - ' : ''}${record?.name || 'New Feed'}`}/>
        <TextInput source="name" helperText={errors.name || false} error={!!errors.name} />
        <TextInput source="uri" helperText={errors.uri || false} error={!!errors.uri} />
        <TextInput source="identifier"/>
        <Box sx={{
            display: 'grid',
            gridTemplateColumns: '1fr 1fr',
            gap: 1,
            width: '100%'
        }}>
            <TextInput source="version" fullWidth helperText={false}/>
            <NumberInput source="priority" fullWidth helperText={false}/>
            <NumberInput source="concatenate_dupes" fullWidth helperText={false}/>
            <NumberInput source="max_updates" fullWidth helperText={false}/>
            <BooleanInput source="strip_journal_ref" fullWidth sx={{ml: 3, my: 1}} helperText={false}/>
        </Box>
        <PlainTextInput label="Prune IDs" source="prune_ids" multiline={true} minRows={1} fullWidth helperText={false}
                        resizable={"vertical"}/>
        <PlainTextInput label="Prune REGEX" source="prune_regex" multiline={true} minRows={1} fullWidth
                        helperText={false} resizable={"vertical"}/>
        <TextInput source="email_errors" label={"Email for error reports"}/>
    </>)
};

export const BibFeedEdit = () => (
    <Box maxWidth={"xl"} minWidth={"600px"} sx={{margin: '0 auto'}} >
        <Edit component={"div"}>
            <ConsoleTitle><BibFeedTitle /></ConsoleTitle>
            <Paper>
                <SimpleForm toolbar={<BibFeedToolbar />}>
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
                <SimpleForm toolbar={<BibFeedToolbar />}>
                    <BibFeedFormInputs />
                </SimpleForm>
            </Paper>
        </Create>
    </Box>
);

