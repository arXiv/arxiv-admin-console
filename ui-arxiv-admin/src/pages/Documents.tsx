import {
    List,
    Datagrid,
    TextField,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    Create,
    Filter,
    BooleanInput,
    ReferenceField,
    Show,
    DateInput, useListContext, SelectInput,
    useDataProvider,
    useRefresh, useNotify
} from 'react-admin';

import LinkIcon from '@mui/icons-material/Link';
import MetadataIcon from '@mui/icons-material/Edit';


import {addDays} from 'date-fns';

import React, {useEffect, useState} from "react";
import CircularProgress from "@mui/material/CircularProgress";
import SubmissionCategoriesField from "../bits/SubmissionCategoriesField";
import Box from "@mui/material/Box";
import Table from "@mui/material/Table";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import Switch from "@mui/material/Switch";
import FormControlLabel from "@mui/material/FormControlLabel";
import Link from "@mui/material/Link";
import PaperOwnersList from "../components/PaperOwnersList";
import SubmissionHistoryList from "../bits/SubmissionHistoryList";
import AdminLogList from "../bits/AdminLogList";
import PaperAdminAddOwnerDialog from "../components/PaperAdminAddOwnerDialog";
import {useNavigate} from "react-router-dom";
import {paths as adminApi} from '../types/admin-api';
import FieldNameCell from "../bits/FieldNameCell";
import ShowEmailsRequestsList from "../bits/ShowEmailRequestsList";
import RenewPaperPasswordDialog from "../bits/RenewPaperPasswordDialog";
import ISODateField from '../bits/ISODateFiled';

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
            <TextInput label="Document ID" source="id" alwaysOn/>
            <TextInput label="Paoper ID" source="paper_id" alwaysOn/>
            <TextInput label="Name" source="submitter_name" alwaysOn/>
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
    const record = useRecordContext();

    if (!record)
        return <CircularProgress/>;

    const paper_id = record?.paper_id;
    console.log('ShowArxivPdf:', paper_id);

    return (
        paper_id ? (
                <Box style={{display: 'flex', flexDirection: 'column', height: '100%'}}>
                    <iframe
                        src={`https://mozilla.github.io/pdf.js/web/viewer.html?file=${encodeURIComponent(`https://arxiv.org/pdf/${paper_id}`)}`}
                        style={{
                            width: "100%",
                            height: "1200px",
                            border: "none"
                        }}
                    />
                </Box>
            )
            : null
    );
}


const DocumentContent = () => {
    const record = useRecordContext();
    const [openAddOwnerDialog, setOpenAddOwnerDialog] = React.useState(false);
    const [openRenewPaperPasswordDialog, setOpenRenewPaperPasswordDialog] = React.useState(false);
    const refresh = useRefresh();
    const navigate = useNavigate();
    const [metadata, setMetadata] = useState<MetadataT | null>(null);
    const dataProvider = useDataProvider();
    const notify = useNotify();

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
                    notify('Error fetching document metadata', {type: 'error'});
                } finally {
                }
            }
        }

        getMetadata();
    }, [record?.id]);

    async function renewPaperPassword () {
        console.log('Renewing paper password');
        if (record?.id) {
            try {
                const response = await dataProvider.update('paper_pw', {
                    id: record.id,
                    previousData: {},
                    data: {} /* auto-gen so no need for data*/
                });
                console.log('Renewed paper password:', JSON.stringify(response.data));
                notify('Renewed paper password');
            } catch (error) {
                console.error('Error renewing paper password:', error);
                notify('Error renewing paper password', {type: 'error'});
            } finally {
                refresh();
            }
        }
    }

    return (
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
                            <Box gap={2} flexDirection={'row'} display="flex" alignItems="center">
                                <TextField source={"paper_id"}/>
                                <Link href={`https://arxiv.org/abs/${record?.paper_id}`}
                                      target="_blank">Abstract <LinkIcon/></Link>
                                <Link href={`https://arxiv.org/pdf/${record?.paper_id}`} target="_blank">PDF <LinkIcon/></Link>
                                <Button disabled={!metadata?.id} endIcon={<MetadataIcon/>}
                                        onClick={() => navigate(`/metadata/${metadata?.id}/edit`)}>Edit
                                    Metadata</Button>
                            </Box>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Title</FieldNameCell>
                        <TableCell>
                            <TextField source="title" variant={"body1"} fontSize={"1.25rem"}/>
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <FieldNameCell>Authors</FieldNameCell>
                        <TableCell>
                            <TextField source="authors" variant={"body1"}/>
                        </TableCell>
                    </TableRow>
                    <TableRow>
                        <FieldNameCell>Categories</FieldNameCell>
                        <TableCell>
                            <SubmissionCategoriesField/>
                        </TableCell>
                    </TableRow>


                    <TableRow>
                        <FieldNameCell>Paper PWD</FieldNameCell>
                        <TableCell>
                            <Box display="flex" sx={{m: 0, p: 0}}>
                                <ReferenceField reference={"paper_pw"} source={"id"}>
                                    <TextField source="password_enc" variant="body1"/>
                                </ReferenceField>
                                <Box flex={1}/>
                                <Button onClick={() => setOpenRenewPaperPasswordDialog(true)}>Change Paper Password</Button>
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
                        <FieldNameCell>Version</FieldNameCell>
                        <TableCell>
                            <Typography>{metadata?.version || "No metadata"}</Typography>
                        </TableCell>
                    </TableRow>

                </Table>
            </Paper>

            {/* Paper Information */}
            <Paper elevation={3} style={{padding: '1em'}}>
                <Typography variant="body1" fontWeight={"bold"}>
                    Show e-mail requests:
                </Typography>
                <Box maxWidth={"sm"}>
                    <ShowEmailsRequestsList document_id={record?.id}/>
                </Box>
            </Paper>

            {/* Paper Owners */}
            <Paper elevation={3} style={{padding: '1em'}}>
                <Box display="flex" alignItems="center">
                    <Typography variant="body1" fontWeight={"bold"}>
                        Paper owners:
                    </Typography>
                    <Button variant={"contained"} sx={{ml: 3}}
                            onClick={() => setOpenAddOwnerDialog(true)}
                    >Add Owner</Button>
                </Box>
                <Box maxWidth={"sm"}>
                    <PaperOwnersList document_id={record?.id}/>
                </Box>
            </Paper>

            {/* Submission History */}
            <Paper elevation={3} style={{padding: '1em'}}>
                <Typography variant="body1" fontWeight={"bold"}>
                    Submission history:
                </Typography>
                <Box maxWidth={"sm"}>
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
            <PaperAdminAddOwnerDialog documentId={record?.id} open={openAddOwnerDialog}
                                      setOpen={setOpenAddOwnerDialog}/>
            <RenewPaperPasswordDialog open={openRenewPaperPasswordDialog} setOpen={setOpenRenewPaperPasswordDialog} renew={renewPaperPassword} />
        </Box>
    );
};

export const DocumentShow = () => {
    const [showPdf, setShowPdf] = React.useState(true);

    return (
        <Show title={<DocumentTitle/>} actions={false}>
            <Box>
                <DocumentContent/>

                <FormControlLabel
                    control={
                        <Switch checked={showPdf} onChange={() => setShowPdf(!showPdf)}
                                inputProps={{'aria-label': 'controlled'}}/>
                    }
                    label="PDF"/>
                {
                    showPdf ? <ShowArxivPdf/> : null
                }


            </Box>

        </Show>
    )
};

export const DocumentList = () => {
    // const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<DocumentFilter/>}>
            <Datagrid rowClick="show">
                <TextField source="id" label={"ID"}/>
                <ISODateField source="dated" label={"Date"}/>

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
                <ISODateField source="created" label={"Created"}/>

            </Datagrid>
        </List>
    );
};


const DocumentTitle = () => {
    const record = useRecordContext();
    return <span>Document {record ? `${record.paper_id}: ${record.title} by ${record.authors}` : ''}</span>;
};


export const DocumentEdit = () => (
    <Edit title={<DocumentTitle/>}>
        <SimpleForm>
            <DocumentContent/>
        </SimpleForm>
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