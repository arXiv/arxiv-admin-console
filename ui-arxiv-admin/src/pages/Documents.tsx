import {
    Card,
    CardContent,
    Paper,
    Grid,
    ToggleButton,
    Typography,
    useMediaQuery,
    Switch,
    FormControlLabel, IconButton
} from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
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
    DateField,
    ReferenceField,
    NumberField,
    SimpleShowLayout,
    Show,
    DateInput, useListContext, SelectInput, useShowContext, Identifier, useDataProvider
} from 'react-admin';

import LinkIcon from '@mui/icons-material/Link';
import MetadataIcon from '@mui/icons-material/Edit';


import {addDays} from 'date-fns';

import React, {ReactNode, useEffect, useState} from "react";
import CircularProgress from "@mui/material/CircularProgress";
import CategoryField from "../bits/CategoryField";
import SubmissionCategoriesField from "../bits/SubmissionCategoriesField";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableRow from "@mui/material/TableRow";
import TableCell, {TableCellProps} from "@mui/material/TableCell";
import Button from "@mui/material/Button";
import Link from "@mui/material/Link";
import PaperOwnersList from "../components/PaperOwnersList";
import SubmissionHistoryList from "../bits/SubmissionHistoryList";
import AdminLogList from "../bits/AdminLogList";
import PaperAdminAddOwnerDialog from "../components/PaperAdminAddOwnerDialog";
import {useNavigate} from "react-router-dom";
import {paths as adminApi} from '../types/admin-api';
import FieldNameCell from "../bits/FieldNameCell";
import ShowEmailsRequestsList from "../bits/ShowEmailRequestsList";

type MetadataT = adminApi['/v1/metadata/document_id/{document_id}']['get']['responses']['200']['content']['application/json'];

/*
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_document_requests.request_id'), index=True)

 */

const presetOptions = [
    {id: 'last_1_day', name: 'Last 1 Day'},
    {id: 'last_7_days', name: 'Last 7 Days'},
    {id: 'last_28_days', name: 'Last 28 Days'},
    {id: 'last_366_days', name: 'Last 366 Days'},
];

const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return {startDate: addDays(today, -1), endDate: today};
        case 'last_7_days':
            return {startDate: addDays(today, -7), endDate: today};
        case 'last_28_days':
            return {startDate: addDays(today, -28), endDate: today};
        case 'last_366_days':
            return {startDate: addDays(today, -366), endDate: today};
        default:
            return {startDate: null, endDate: null};
    }
};

const DocumentFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const {startDate, endDate} = calculatePresetDates(event.target.value);
        setFilters({
            ...filterValues,
            startDate: startDate ? startDate.toISOString().split('T')[0] : '',
            endDate: endDate ? endDate.toISOString().split('T')[0] : '',
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="Paoper ID" source="paper_id" alwaysOn/>
            <TextInput label="Name" source="submitter_name" alwaysOn/>
            <TextInput label="Category" source="category" alwaysOn/>
            <TextInput label="Category" source="category" alwaysOn/>

            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <DateInput label="Start Date" source="start_date"/>
            <DateInput label="End Date" source="end_date"/>
            <BooleanInput label="Valid" source="flag_valid"/>
        </Filter>
    );
};


const ShowArxivPdf = () => {
    const record = useShowContext();

    if (record.isFetching)
        return <CircularProgress/>;

    const paper_id = record?.record?.paper_id;

    return (
        paper_id ? (
                <Grid item xs={12} style={{display: 'flex', flexDirection: 'column', height: '75vh'}}>
                    <iframe
                        src={`https://arxiv.org/pdf/${paper_id}`}
                        title="PDF Document"
                        style={{
                            border: 'none',
                            width: "100%",
                            flex: 1,
                        }}
                    />
                </Grid>
            )
            : null
    );
}

export const DocumentShow = () => {
    const [showPdf, setShowPdf] = React.useState(true);

    return (
        <Show>
            <Grid container>
                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        {" "}
                    </Grid>
                    <Grid item xs={10}>
                        <TextField source="paper_id"/>
                        {" / "}
                        <TextField source="id"/>
                        {" ("}
                        <ReferenceField source="last_submission_id" reference="submissions" label={"Submission"}>
                            <TextField source="id"/>
                        </ReferenceField>
                        {")"}
                    </Grid>
                </Grid>
                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        From:
                    </Grid>
                    <Grid item xs={10}>
                        <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                        link={(record, reference) => `/${reference}/${record.id}`}>
                            <TextField source={"last_name"}/>
                            {", "}
                            <TextField source={"first_name"}/>
                            {" <"}
                            <EmailField source={"email"}/>
                            {">"}
                        </ReferenceField>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Submitter Email:
                    </Grid>
                    <Grid item xs={10}>
                        <EmailField source="submitter_email"/>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Submission date:
                    </Grid>
                    <Grid item xs={3}>
                        <DateField source="dated"/>
                    </Grid>
                    <Grid item xs={2}>
                        Created:
                    </Grid>
                    <Grid item xs={3}>
                        <DateField source="created"/>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Title:
                    </Grid>
                    <Grid item xs={10}>
                        <TextField source="title"/>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Authors:
                    </Grid>
                    <Grid item xs={10}>
                        <TextField source="authors"/>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Categories:
                    </Grid>
                    <Grid item xs={10}>
                        <SubmissionCategoriesField/>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        License:
                    </Grid>
                    <Grid item xs={10}>
                        <ReferenceField source="last_submission_id" reference="submissions" label={"Licence"}
                                        link={false}>
                            <TextField source="license"/>
                        </ReferenceField>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <Grid item xs={2}>
                        Abstract:
                    </Grid>
                    <Grid item xs={10}>
                        <ReferenceField source="last_submission_id" reference="submissions" label={"Abstract"}
                                        link={false}>
                            <TextField source="abstract"/>
                        </ReferenceField>
                    </Grid>
                </Grid>

                <Grid container item xs={12}>
                    <FormControlLabel
                        control={
                            <Switch checked={showPdf} onChange={() => setShowPdf(!showPdf)}
                                    inputProps={{'aria-label': 'controlled'}}/>
                        }
                        label="PDF"/>
                </Grid>
                <Grid container item xs={12}>
                    {
                        showPdf ? <ShowArxivPdf/> : null
                    }
                </Grid>
            </Grid>
        </Show>
    )
};

export const DocumentList = () => {
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<DocumentFilter/>}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.documentname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="edit">
                    <TextField source="id" label={"ID"}/>
                    <DateField source="dated" label={"Date"}/>

                    <TextField source="paper_id" label={"Paper ID"}/>

                    <TextField source="title" label={"Title"}/>

                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                    link={(record, reference) => `/${reference}/${record.id}`}>
                        <TextField source={"last_name"}/>
                        {", "}
                        <TextField source={"first_name"}/>
                    </ReferenceField>

                    <TextField source="authors"/>
                    <TextField source="abs_categories" label={"Categories"}/>
                    <DateField source="created" label={"Created"}/>

                </Datagrid>
            )}
        </List>
    );
};


const DocumentTitle = () => {
    const record = useRecordContext();
    return <span>Document {record ? `${record.paper_id}: ${record.title} by ${record.authors}` : ''}</span>;
};



const DocumentEditContent = () => {
    const record = useRecordContext();
    const [openAddOwnerDialog, setOpenAddOwnerDialog] = React.useState(false);
    const navigate = useNavigate();
    const [metadata, setMetadata] = useState<MetadataT | null>(null);
    const dataProvider =  useDataProvider();

    useEffect(() => {
        async function getMetadata() {
            if (record?.id) {
                try {
                    const response = await dataProvider.getOne('document-metadata', {
                        id: record.id,
                    });
                    setMetadata(response.data);
                    console.log('Metadata:', JSON.stringify(response.data));
                } catch (error) {
                    console.error('Error fetching submission categories:', error);
                } finally {
                }
            }
        }
        getMetadata();
    }, [record?.id]);

    return (
        <SimpleForm>
            <Box gap={1} display="flex" flexDirection="column"
                 sx={{
                     width: '100%',
                     '& .MuiBox-root': {  // Targets all Box components inside
                         width: '100%'
                     },
                     '& .MuiTable-root': {  // Targets all Table components inside
                         width: '100%'
                     }
                 }}
            >

                {/* Paper Details */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Table size="small">
                        <TableRow>
                            <FieldNameCell>Paper</FieldNameCell>
                            <TableCell>
                                <Box gap={2} flexDirection={'row'} display="flex"  alignItems="center">
                                    <TextField source={"paper_id"}/>
                                    <Link href={`https://arxiv.org/abs/${record?.paper_id}`} target="_blank">Abstruct <LinkIcon /></Link>
                                    <Link href={`https://arxiv.org/pdf/${record?.paper_id}`} target="_blank">PDF <LinkIcon /></Link>
                                    <Button disabled={!metadata?.id} endIcon={<MetadataIcon />} onClick={() => navigate(`/metadata/${metadata?.id}/edit`)}>Edit Metadata</Button>
                                </Box>
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Title</FieldNameCell>
                            <TableCell>
                                <TextField source="title" variant={"body1"} fontSize={"1.25rem"} />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <FieldNameCell>Authors</FieldNameCell>
                            <TableCell>
                                <TextField source="authors" variant={"body1"} />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <FieldNameCell>Categories</FieldNameCell>
                            <TableCell>
                                <SubmissionCategoriesField/>
                            </TableCell>
                        </TableRow>


                        <TableRow>
                            <FieldNameCell>Paper Password</FieldNameCell>
                            <TableCell>
                                <Box display="flex" sx={{m: 0, p: 0}}>
                                    <ReferenceField reference={"paper_pw"} source={"id"}>
                                        <TextField source="password_enc" variant="body1"/>
                                    </ReferenceField>
                                    <Box flex={1}/>
                                    <Button>Change Paper Password</Button>
                                </Box>
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Document ID</FieldNameCell>
                            <TableCell>
                                <Box gap={1}>
                                    <TextField source="id" variant="body1"/>
                                </Box>
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <FieldNameCell>Latest version</FieldNameCell>
                            <TableCell>
                                <ReferenceField reference={"submissions"} source={"last_submission_id"}>
                                    <Typography>
                                        {"version "}
                                        <TextField source="version" variant="body1"/>
                                    </Typography>
                                </ReferenceField>
                            </TableCell>
                        </TableRow>

                    </Table>
                </Paper>

                {/* Paper Information */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Typography variant="body1" fontWeight={"bold"}>
                        Show e-mail requests:
                    </Typography>
                    <Box maxWidth={"sm"} >
                        <ShowEmailsRequestsList document_id={record?.id}/>
                    </Box>
                </Paper>

                {/* Paper Owners */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Box display="flex"  alignItems="center">
                        <Typography variant="body1" fontWeight={"bold"}>
                            Paper owners:
                        </Typography>
                        <Button variant={"contained"} sx={{ml: 3}}
                                onClick={() => setOpenAddOwnerDialog(true)}
                        >Add Owners</Button>
                    </Box>
                    <Box maxWidth={"sm"} >
                        <PaperOwnersList document_id={record?.id}/>
                    </Box>
                </Paper>

                {/* Submission History */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Typography variant="body1" fontWeight={"bold"}>
                        Submission history:
                    </Typography>
                    <Box maxWidth={"sm"} >
                        <SubmissionHistoryList document_id={record?.id}/>
                    </Box>
                </Paper>

                {/* Admin Log */}
                <Paper elevation={3} style={{padding: '1em'}}>
                    <Typography variant="body1" fontWeight={"bold"}>
                        Admin Log:
                    </Typography>
                    <AdminLogList paper_id={record?.paper_id}/>
                </Paper>
            </Box>
            <PaperAdminAddOwnerDialog documentId={record?.id} open={openAddOwnerDialog} setOpen={setOpenAddOwnerDialog} />
        </SimpleForm>
    );
};

export const DocumentEdit = () => (
    <Edit title={<DocumentTitle/>}>
        <DocumentEditContent/>
    </Edit>
);

export const DocumentCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <TextInput source="archive"/>

            <TextInput source="subject_class"/>
            <BooleanInput source="flag_valid" label={"Valid"}/>

            <TextInput source="type"/>
            <NumberInput source="point_value" label={"Point"}/>
            <DateInput source="issued_when" label={"Issued"}/>

        </SimpleForm>
    </Create>
);