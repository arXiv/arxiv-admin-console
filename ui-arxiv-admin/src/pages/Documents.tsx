import {Card, CardContent, Grid, ToggleButton, Typography, useMediaQuery, Switch, FormControlLabel} from '@mui/material';
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
    DateInput, useListContext, SelectInput, useShowContext
} from 'react-admin';

import { addDays } from 'date-fns';

import React from "react";
import CircularProgress from "@mui/material/CircularProgress";
import CategoryField from "../bits/CategoryField";
import SubmissionCategoriesField from "../bits/SubmissionCategoriesField";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
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
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
    { id: 'last_366_days', name: 'Last 366 Days' },
];

const calculatePresetDates = (preset: string) => {
    const today = new Date();
    switch (preset) {
        case 'last_1_day':
            return { startDate: addDays(today, -1), endDate: today };
        case 'last_7_days':
            return { startDate: addDays(today, -7), endDate: today };
        case 'last_28_days':
            return { startDate: addDays(today, -28), endDate: today };
        case 'last_366_days':
            return { startDate: addDays(today, -366), endDate: today };
        default:
            return { startDate: null, endDate: null };
    }
};

const DocumentFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const { startDate, endDate } = calculatePresetDates(event.target.value);
        setFilters({
            ...filterValues,
            startDate: startDate ? startDate.toISOString().split('T')[0] : '',
            endDate: endDate ? endDate.toISOString().split('T')[0] : '',
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="Paoper ID" source="paper_id" alwaysOn />
            <TextInput label="Name" source="submitter_name" alwaysOn />
            <TextInput label="Category" source="category" alwaysOn />
            <TextInput label="Category" source="category" alwaysOn />

            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" />
        </Filter>
    );
};


const ShowArxivPdf = () => {
    const record = useShowContext();

    if (record.isFetching)
        return <CircularProgress />;

    const paper_id = record?.record?.paper_id;

    return (
        paper_id ? (
            <Grid item xs={12}  style={{ display: 'flex', flexDirection: 'column', height: '75vh' }}>
                <iframe
                    src={`https://arxiv.org/pdf/${paper_id}`}
                    title="PDF Document"
                    style={{ border: 'none',
                        width:"100%",
                        flex: 1,}}
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
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                        {" <"}
                        <EmailField source={"email"} />
                        {">"}
                    </ReferenceField>
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Submitter Email:
                </Grid>
                <Grid item xs={10}>
                    <EmailField source="submitter_email" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Submission date:
                </Grid>
                <Grid item xs={3}>
                    <DateField source="dated" />
                </Grid>
                <Grid item xs={2}>
                    Created:
                </Grid>
                <Grid item xs={3}>
                    <DateField source="created" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Title:
                </Grid>
                <Grid item xs={10}>
                    <TextField source="title" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Authors:
                </Grid>
                <Grid item xs={10}>
                    <TextField source="authors" />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Categories:
                </Grid>
                <Grid item xs={10}>
                    <SubmissionCategoriesField />
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    License:
                </Grid>
                <Grid item xs={10}>
                    <ReferenceField source="last_submission_id" reference="submissions" label={"Licence"} link={false}>
                        <TextField source="license" />
                    </ReferenceField>
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <Grid item xs={2}>
                    Abstract:
                </Grid>
                <Grid item xs={10}>
                    <ReferenceField source="last_submission_id" reference="submissions" label={"Abstract"} link={false}>
                        <TextField source="abstract" />
                    </ReferenceField>
                </Grid>
            </Grid>

            <Grid container item xs={12}>
                <FormControlLabel
                    control={
                        <Switch checked={showPdf} onChange={() => setShowPdf(!showPdf)} inputProps={{ 'aria-label': 'controlled'}} />
                    }
                    label="PDF"/>
            </Grid>
            <Grid container item xs={12}>
                {
                    showPdf ? <ShowArxivPdf /> : null
                }
            </Grid>
        </Grid>
    </Show>
)};

export const DocumentList = () => {
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<DocumentFilter />}>
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
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>

                    <TextField source="authors" />
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
    
    return (
        <Box gap={2} display="flex" flexDirection="column">
            {/* Paper Header */}
            <Box flex={12}>
            </Box>

            {/* Paper Details */}
            <Box flex={12}>
                <Table >
                    <TableRow>
                        <TableCell>Paper</TableCell>
                        <TableCell>
                            <TextField source={"paper_id"} />
                            <a href={`/abs/${record?.paper_id}`}>abs</a> |
                            <a href={`/pdf/${record?.paper_id}`}>PDF</a> |
                            <a href={`/admin/meta/edit/${record?.paper_id}`}>edit</a>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <TableCell>Title</TableCell>
                        <TableCell>
                            <TextField source="title" variant="body1"  />
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell>Authors</TableCell>
                        <TableCell>
                            <TextField source="authors" variant="body1"  />
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <TableCell>Categories</TableCell>
                        <TableCell>
                            <SubmissionCategoriesField />
                        </TableCell>
                    </TableRow>
                </Table>
            </Box>

            {/* Paper Information */}
            <Box item xs={12}>
                <Card>
                    <CardContent>
                        <Typography variant="body1" gutterBottom>
                            <span style={{ fontWeight: 'bold' }}>Paper password:</span> <TextField source="paper_password" variant="body1" />
                            <span style={{ fontWeight: 'bold' }}> [<a href={`/admin/change-paper-pw.php?document_id=${record?.id}`}>change</a>]</span>
                        </Typography>
                        <Typography variant="body1" gutterBottom>
                            <span style={{ fontWeight: 'bold' }}>Document id:</span> <TextField source="id" variant="body1" />,
                            latest is v<TextField source="version" variant="body1" /> (shown)
                        </Typography>
                        <Typography variant="body1" gutterBottom>
                            <span style={{ fontWeight: 'bold' }}>Show e-mail requests:</span> 
                            <a href={`/admin/generic-list.php?document_id=${record?.id}`}>
                                <NumberField source="email_request_count" />
                            </a>
                        </Typography>
                    </CardContent>
                </Card>
            </Box>

            {/* Paper Owners */}
            <Box item xs={12}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <span style={{ fontWeight: 'bold' }}>Paper owners:</span>
                        </Typography>
                        <table style={{ marginLeft: '2em', width: '100%' }}>
                            <thead>
                                <tr>
                                    <th>User</th>
                                    <th>Email</th>
                                    <th>Name</th>
                                    <th>Role</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {/* This would be populated with paper owners data */}
                                <tr>
                                    <td>
                                        <ReferenceField source="submitter_id" reference="users" label="Submitter">
                                            <TextField source="username" />
                                        </ReferenceField>
                                    </td>
                                    <td>
                                        <EmailField source="submitter_email" />
                                    </td>
                                    <td>
                                        <ReferenceField source="submitter_id" reference="users">
                                            <TextField source="first_name" />
                                            {" "}
                                            <TextField source="last_name" />
                                        </ReferenceField>
                                    </td>
                                    <td><strong>Author</strong></td>
                                    <td><strong>[<a href="#">revoke</a>]</strong></td>
                                </tr>
                            </tbody>
                        </table>
                        
                        {/* Add Owner Form */}
                        <SimpleForm style={{ marginLeft: '2em', marginTop: '1em' }}>
                            <TextInput source="new_owner_search" label="Search User" />
                            <SelectInput
                                source="author_type"
                                choices={[
                                    { id: '1', name: 'as Author' },
                                    { id: '0', name: 'as Non-Author' }
                                ]}
                                defaultValue="1"
                            />
                            <button type="submit">Add Owner &gt;&gt;</button>
                        </SimpleForm>
                    </CardContent>
                </Card>
            </Box>

            {/* Submission History */}
            <Box item xs={12}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <span style={{ fontWeight: 'bold' }}>Submission history:</span>
                        </Typography>
                        <table style={{ marginLeft: '2em', width: '100%', border: '1px solid #ddd' }}>
                            <thead>
                                <tr style={{ backgroundColor: '#f5f5f5' }}>
                                    <th>Version</th>
                                    <th>Date</th>
                                    <th>Submitter</th>
                                    <th>Email/Name on Submission</th>
                                </tr>
                            </thead>
                            <tbody>
                                {/* This would be populated with submission history data */}
                                <tr>
                                    <td>
                                        <strong>
                                            <a href={`/abs/${record?.paper_id}`}>
                                                v<TextField source="version" variant="body1"  />
                                            </a>
                                        </strong>
                                    </td>
                                    <td><DateField source="created" /></td>
                                    <td>
                                        <ReferenceField source="submitter_id" reference="users">
                                            <TextField source="username" />
                                        </ReferenceField>
                                        : <EmailField source="submitter_email" />
                                        (<TextField source="submitter_name" />)
                                    </td>
                                    <td>
                                        <small>
                                            [email/name on submission: <EmailField source="submitter_old_email" />
                                            (<TextField source="submitter_old_name" />)]
                                        </small>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </CardContent>
                </Card>
            </Box>

            {/* Admin Log */}
            <Box item xs={12}>
                <Card>
                    <CardContent>
                        <Typography variant="h6" gutterBottom>
                            <span style={{ fontWeight: 'bold' }}>Admin Log:</span>
                        </Typography>
                        <table style={{ border: '1px solid #ddd', width: '100%' }}>
                            <thead>
                                <tr style={{ backgroundColor: '#FAA' }}>
                                    <th>Time</th>
                                    <th>Username</th>
                                    <th>Program/Command</th>
                                    <th>Sub Id</th>
                                    <th>Log text</th>
                                </tr>
                            </thead>
                            <tbody>
                                {/* This would be populated with log entries */}
                                <tr>
                                    <td><DateField source="log_created" /></td>
                                    <td><TextField source="log_username" /></td>
                                    <td><TextField source="log_program" /> / <TextField source="log_command" /></td>
                                    <td>
                                        <ReferenceField source="log_submission_id" reference="submissions">
                                            <TextField source="id" />
                                        </ReferenceField>
                                    </td>
                                    <td><TextField source="log_text" /></td>
                                </tr>
                            </tbody>
                        </table>
                    </CardContent>
                </Card>
            </Box>
        </Box>
    );
};

export const DocumentEdit = () => (
    <Edit title={<DocumentTitle />}>
        <DocumentEditContent />
    </Edit>
);

export const DocumentCreate = () => (
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


