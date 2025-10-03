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
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import EditIcon from '@mui/icons-material/Edit';


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
import ConsoleTitle from "../bits/ConsoleTitle";
import TruncatedTextField from "../bits/TruncatedTextField";
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
import {StandardAccordion} from "../components/StandardAccordion";
import {LazyAccordion} from "../components/LazyAccordion";
import IconButton from '@mui/material/IconButton';
import {TruncatedList} from "../components/TruncatedList";
import {truncateList} from "../utils/truncateList";
import Divider from '@mui/material/Divider';

type MetadataT = adminApi['/v1/metadata/document/{document_id}']['get']['responses']['200']['content']['application/json'];

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
            <TextInput label="Paper ID" source="paper_id" alwaysOn/>
            <TextInput label="Name" source="submitter_name" alwaysOn/>
            <TextInput label="Category" source="category" alwaysOn/>
            <TextInput label="Title" source="title"/>

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
                    const response = await dataProvider.getOne('document-metadata-latest', {
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
        <Box gap={1} display="flex" flexDirection="column">

            <Box gap={2} flexDirection={'row'} display="flex" alignItems="center">
                <Button disabled={!metadata?.id} startIcon={<MetadataIcon/>} variant={"contained"}
                        onClick={() => navigate(`/metadata/${metadata?.id}/edit`)}>
                    Edit Metadata
                </Button>
                <Button variant={"outlined"} endIcon={<OpenInNewIcon/>} onClick={() => window.open(`https://arxiv.org/pdf/${record?.paper_id}`, '_blank')}>PDF</Button>
                <Button variant={"outlined"} endIcon={<OpenInNewIcon/>} onClick={() => window.open(`https://arxiv.org/html/${record?.paper_id}`, '_blank')}>HTML</Button>
                <Button variant={"outlined"} endIcon={<OpenInNewIcon/>} onClick={() => window.open(`https://arxiv.org/abs/${record?.paper_id}`, '_blank')}>Abstract</Button>
            </Box>
            {/* Paper Details */}


                <Table size="small" sx={{
                    '& .MuiTableRow-root': {
                        '& .MuiTableCell-root': {
                            border: 'none',
                        }
                    }
                }}>
                    <TableRow>
                        <FieldNameCell>Announced ID</FieldNameCell>
                        <TableCell>
                            <TextField source="paper_id"/>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Document ID</FieldNameCell>
                        <TableCell>
                            <TextField source="id"/>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Version</FieldNameCell>
                        <TableCell>
                            <Typography>{metadata?.version || "No metadata"}</Typography>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Announced Date</FieldNameCell>
                        <TableCell>
                            <ISODateField source="dated" />
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Title</FieldNameCell>
                        <TableCell>
                            <TextField source="title" />
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Authors</FieldNameCell>
                        <TableCell>
                            <TextField source="authors"/>
                        </TableCell>
                    </TableRow>


                    <TableRow>

                        <FieldNameCell>Categories</FieldNameCell>
                        <TableCell>
                            <SubmissionCategoriesField/>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Source Format</FieldNameCell>
                        <TableCell>
                            <Typography>{metadata?.source_format || "No metadata"}</Typography>
                        </TableCell>
                    </TableRow>

                    <TableRow>
                        <FieldNameCell>Paper Password</FieldNameCell>
                        <TableCell>
                            <ReferenceField reference={"paper_pw"} source={"id"}>
                                <TextField source="password_enc" variant="body1"/>
                            </ReferenceField>
                            <IconButton onClick={() => setOpenRenewPaperPasswordDialog(true)}><EditIcon /></IconButton>
                        </TableCell>

                    </TableRow>
                </Table>

            {/* Paper Owners */}
            <Divider />
            <StandardAccordion title="Paper owners" summary={truncateList(record?.authors, 3)} >
                <Box display="flex" alignItems="center" mb={2}>
                    <Button variant={"contained"}
                            onClick={() => setOpenAddOwnerDialog(true)}
                    >Add Owner</Button>
                </Box>
                <Paper sx={{maxWidth: "md"}}>
                    <PaperOwnersList document_id={record?.id}/>
                </Paper>
            </StandardAccordion>

            {/* Admin Log */}
            <Divider />
            <StandardAccordion title="Admin Log">
                <Paper sx={{mb: 2, maxWidth: "md"}}>
                    <AdminLogList paper_id={record?.paper_id}/>
                </Paper>
            </StandardAccordion>


            {/* Submission History */}
            <Divider />
            <StandardAccordion title="Submission history">
                <Paper sx={{mb: 2, maxWidth: "md"}}>
                    <SubmissionHistoryList document_id={record?.id}/>
                </Paper>
            </StandardAccordion>

            {/* Paper Information */}
            <Divider />
            <StandardAccordion title="Show e-mail requests:">
                <Paper sx={{mb: 2, maxWidth: "md"}}>
                    <ShowEmailsRequestsList document_id={record?.id}/>
                </Paper>
            </StandardAccordion>

            <PaperAdminAddOwnerDialog documentId={record?.id} open={openAddOwnerDialog}
                                      setOpen={setOpenAddOwnerDialog}/>
            <RenewPaperPasswordDialog open={openRenewPaperPasswordDialog} setOpen={setOpenRenewPaperPasswordDialog} renew={renewPaperPassword} />
        </Box>
    );
};

export const DocumentShow = () => {

    return (
        <Box maxWidth={"lg"} ml={"10%"} width={"80%"}>
            <Show title={false} actions={false} component={"div"}>
                <StyledDocumentTitle prefix={""}/>
                <DocumentContent/>
                <Divider />
                <Box my={1}>
                    <LazyAccordion title="PDF">
                        <ShowArxivPdf/>
                    </LazyAccordion>
                </Box>
            </Show>
        </Box>
    )
};

export const DocumentList = () => {
    // const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <Box maxWidth={"xl"} sx={{ mx: 'auto', px: '3rem', backgroundColor: 'background.default' }}>
            <ConsoleTitle>Documents</ConsoleTitle>
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

                <TruncatedTextField source="authors" maxItems={3} />
                <TextField source="abs_categories" label={"Categories"}/>
                <ISODateField source="created" label={"Created"}/>

                <ReferenceField reference={"document-metadata-latest"} source={"id"} label={"Vers"}>
                    <TextField source={"version"}  />
                </ReferenceField>

            </Datagrid>
        </List>
        </Box>
    );
};


const DocumentTitle = () => {
    const record = useRecordContext();
    return <span>{record ? `${record.paper_id}: ${record.title}` : ''}</span>;
};

export const StyledDocumentTitle : React.FC<{prefix: string}> = ({prefix}) => {
    const record = useRecordContext();
    return (
        <Typography variant={"h1"} fontSize={"2rem"} sx={{mt: 3, mb: 2}}>{prefix}{record ? `${record.paper_id}: ` : ''}
            <Typography component="span" fontSize="1.5rem" fontWeight={700}>{record ? record.title : ''}</Typography>
        </Typography>
    );
};


export const DocumentEdit = () => (
    <Edit title={false} component={"div"}>
        <SimpleForm>
            <DocumentContent/>
        </SimpleForm>
    </Edit>
);
/*
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
 */