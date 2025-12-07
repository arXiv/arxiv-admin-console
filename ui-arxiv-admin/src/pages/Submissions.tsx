import {Box, Table, TableRow, TableCell, Typography, Link} from '@mui/material';
import ConsoleTitle from "../bits/ConsoleTitle";
import {
    BooleanInput,
    Create,
    Datagrid,
    DateInput,
    Edit,
    EmailField,
    Filter,
    List,
    NumberField,
    NumberInput,
    ReferenceField,
    SelectInput,
    SelectArrayInput,
    SelectField,
    Show,
    SimpleForm,
    SimpleShowLayout,
    TextField,
    TextInput,
    useListContext,
    useRecordContext,
    Toolbar,
    SaveButton,
    EditButton,
    TopToolbar,
} from 'react-admin';


import {addDays} from 'date-fns';

import React, {useState, useContext, useEffect} from "react";
import {submissionStatusOptions} from "../bits/SubmissionStateField";
import AdminLogList, {AdminLogFilter} from "../bits/AdminLogList";
import ArchiveSubjectClassInput from "../bits/ArchiveSubjectClassInput";
// import SubmissionCategoriesField, {CategoriesField, CategoryList} from "../bits/SubmissionCategoriesField";
import IsOkField from "../bits/IsOkField";
import {RuntimeContext} from "../RuntimeContext";
import ArxivCheckSubmissionLink from "../bits/ArxivCheckSubmissionLink";
import ISODateField from '../bits/ISODateFiled';
import UriTemplate from 'uri-templates';
import Button from '@mui/material/Button';
import Paper from '@mui/material/Paper';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import LinkIcon from '@mui/icons-material/Link';
import LaunchIcon from '@mui/icons-material/Launch';
import { useNavigate } from 'react-router-dom';
import { StandardAccordion } from '../components/StandardAccordion';

import {paths as adminApi, components as adminComponents} from "../types/admin-api";
import UserNameField from "../bits/UserNameField";
import CategoryField from "../bits/CategoryField";
import PrimaryCategoryField from "../bits/PirmaryCategoryField";
import AdminLogField from "../bits/AdminLogField";
import SingleUserInputField from "../components/SingleUserInputField";
import Divider from "@mui/material/Divider";


type SubmissionModel = adminComponents['schemas']['SubmissionModel'];
type SubmissionType = adminComponents['schemas']['SubmissionType'];

type SubmissionNavi = adminApi['/v1/submissions/navigate']['get']['responses']['200']['content']['application/json'];


const presetOptions = [
    {id: 'last_1_day', name: 'Last 1 Day'},
    {id: 'last_7_days', name: 'Last 7 Days'},
    {id: 'last_28_days', name: 'Last 28 Days'},
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
        default:
            return {startDate: null, endDate: null};
    }
};

export const submissionTypeOptions = [
    {"id": "new", "name": "New"},
    {"id": "cross", "name": "Cross"},
    {"id": "jref", "name": "JRef"},
    {"id": "rep", "name": "Rep"},
    {"id": "wdr", "name": "Withdrawal"}
];


const SubmissionFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        setFilters({
            ...filterValues,
        });
    };

    return (
        <Filter {...props}>
            <NumberInput label="Submission ID" source="id" alwaysOn sx={{width: '8rem'}}/>
            <SelectInput
                label="Status"
                source="submission_status"
                choices={submissionStatusOptions}
                alwaysOn
            />
            <SelectArrayInput
                label="S-Type"
                source="type"
                choices={submissionTypeOptions}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date"/>
            <DateInput label="End Date" source="end_date"/>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <SingleUserInputField source={"submitter_id"} label={"Submitter"} alwaysOn variant={"dialog"}/>
            <TextInput label="Title" source="title" />
        </Filter>
    );
};


export const SubmissionList = () => {
    const defaultDates = calculatePresetDates('last_28_days');

    return (
        <Box maxWidth={"xl"} sx={{ margin: '0 auto'}}>
            <ConsoleTitle>Submissions</ConsoleTitle>
        <List filters={<SubmissionFilter/>}
              filterDefaultValues={{
                  submission_status: [],
              }}
              sort={{ field: 'id', order: 'DESC' }}

        >
            <Datagrid rowClick={false} bulkActionButtons={false}
                      expand={<AdminLogField source="id" label={"Log"} variant={'list'}/>}
            >
                <ReferenceField reference={"submissions"} source={"id"} link={"show"}>
                    <TextField source="id" label="ID" textAlign="right"/>
                </ReferenceField>
                <ArxivCheckSubmissionLink source="type" label="Type"/>
                <PrimaryCategoryField source="submission_categories" label="Cat"/>
                <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                link={(record, reference) => `/${reference}/${record.id}/show`}>
                    <UserNameField withUsername/>
                </ReferenceField>
                <ArxivCheckSubmissionLink source="title"/>
                <ReferenceField source="document_id" reference="documents" label={"Doc"}
                                link={(record, reference) => `/${reference}/${record.id}/show`}>
                    <TextField source={"paper_id"}/>
                </ReferenceField>
                <IsOkField source="is_ok" label={"OK?"}/>
            </Datagrid>
        </List>
        </Box>
    );
};


const SubmissionTitle = () => {
    const record = useRecordContext();
    return <span>Submission {record ? `${record.id}` : ''}</span>;
};

const SubmissionAdminLogList = () => {
    const record = useRecordContext();
    if (!record?.id)
        return null;
    return (
        <AdminLogList submission_id={record.id}/>
    )
}

const SubmissionAdminLogAccordion = () => (
    <StandardAccordion title="Admin Logs">
        <Paper>
            <SubmissionAdminLogList />
        </Paper>
    </StandardAccordion>
);

const SubmissionEditToolbar = () => (
    <Toolbar>
        <SaveButton />
    </Toolbar>
);

const SubmissionTable = ({ mode }: { mode: 'edit' | 'show' }) => {
    return (
        <Table size="small" sx={{
            '& .MuiTableCell-head': {
                width: '10rem',
                textAlign: 'right',
            }
        }}>
            <TableRow>
                <TableCell variant="head">ID</TableCell>
                <TableCell>
                    <ArxivCheckSubmissionLink source={"id"} />
                    {mode === 'show' && (
                        <>
                            {" / "}
                            <TextField source="document_id"/>
                        </>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Source Format</TableCell>
                <TableCell>
                    <TextField source="source_format"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Source Size</TableCell>
                <TableCell>
                    <NumberField source="source_size"/>
                    {" bytes"}
                </TableCell>
            </TableRow>

            <TableRow>
                <TableCell variant="head">Status</TableCell>
                <TableCell>
                    <SelectField source="status" choices={submissionStatusOptions} />
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">User Identity</TableCell>
                <TableCell>
                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}
                                    link={(record, reference) => `/${reference}/${record.id}`}>
                        <TextField source={"last_name"}/>
                        {", "}
                        <TextField source={"first_name"}/>
                    </ReferenceField>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Email</TableCell>
                <TableCell>
                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}>
                        <EmailField source={"email"}/>
                    </ReferenceField>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">From Name</TableCell>
                <TableCell>
                    {mode === 'edit' ? (
                        <TextInput source="submitter_name" helperText={false}/>
                    ) : (
                        <TextField source="submitter_name"/>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">From Email</TableCell>
                <TableCell>
                    {mode === 'edit' ? (
                        <TextInput source="submitter_email" helperText={false}/>
                    ) : (
                        <TextField source="submitter_email"/>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Date Created</TableCell>
                <TableCell>
                    <ISODateField source="created" label="Created"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Date Updated</TableCell>
                <TableCell>
                    <ISODateField source="updated"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Submission Date</TableCell>
                <TableCell>
                    <ISODateField source="submit_time"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Release Time</TableCell>
                <TableCell>
                    <ISODateField source="release_time"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Categories</TableCell>
                <TableCell >
                    {mode === 'edit' ? (
                        <ArchiveSubjectClassInput source="id" sourceCategory="archive"
                                                  sourceClass="subject_class"
                                                  helperText={false}
                        />
                    ) : (
                        <CategoryField sourceCategory="archive" sourceClass="subject_class" source="archive" label="Category"/>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Title</TableCell>
                <TableCell >
                    {mode === 'edit' ? (
                        <TextInput source="title" helperText={false}/>
                    ) : (
                        <TextField source="title"/>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Authors</TableCell>
                <TableCell>
                    {mode === 'edit' ? (
                        <TextInput source="authors" helperText={false}/>
                    ) : (
                        <TextField source="authors"/>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Comments</TableCell>
                <TableCell>
                    {mode === 'edit' ? (
                        <TextInput source="comments" helperText={false}/>
                    ) : (
                        <TextField source="comments"/>
                    )}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">License</TableCell>
                <TableCell>
                    <TextField source="license"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell variant="head">Abstract</TableCell>
                <TableCell>
                    {mode === 'edit' ? (
                        <TextInput source="abstract" multiline rows={20} helperText={false}/>
                    ) : (
                        <TextField source="abstract"/>
                    )}
                </TableCell>
            </TableRow>
        </Table>
    );
};

const SubmissionEditContent = () => {
    const record = useRecordContext();
    const runtimeProps = useContext(RuntimeContext);

    const arxivCheckUrl = record?.id ? UriTemplate(runtimeProps.URLS.CheckSubmissionLink).fill({
        arxivCheck: runtimeProps.ARXIV_CHECK,
        submissionId: record.id,
    }) : '';

    return (
        <Box my={1} >
            <ConsoleTitle>Edit: <SubmissionTitle /></ConsoleTitle>

            <Box sx={{ mb: 2 }}>
                <Button
                    component="a"
                    href={arxivCheckUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="outlined"
                    disabled={!record?.id}
                    endIcon={<LaunchIcon />}
                >
                    Jump to arXiv Check
                </Button>
            </Box>

            <Paper elevation={2} sx={{width: "100%", maxWidth: "lg", margin: "0 auto"}}>
                <SimpleForm toolbar={<SubmissionEditToolbar />}>
                    <SubmissionTable mode="edit" />
                </SimpleForm>
            </Paper>
            <Divider />
            <SubmissionAdminLogAccordion />
        </Box>
    );
};

export const SubmissionEdit = () => {
    return (
        <Box display={"flex"} flexDirection={"column"} width={"80%"} ml={"10%"} maxWidth={"lg"}>
            <Edit component={"div"}>
                <SubmissionEditContent />
            </Edit>
        </Box>
    );
}


/*
 */
const SubmissionShowActions = () => {
    const record = useRecordContext();
    const navigate = useNavigate();
    const runtimeProps = useContext(RuntimeContext);
    const [navigation, setNavigation] = useState<SubmissionNavi | null>(null);
    const id = record?.id;

    useEffect(() => {
        if (runtimeProps.adminFetcher) {
            const getNavigation = runtimeProps.adminFetcher.path('/v1/submissions/navigate').method('get').create();

            async function fetchNavigation() {
                if (id) {
                    try {
                        const response = await getNavigation({id: Number(id)});
                        if (response.ok) {
                            setNavigation(response.data);
                        }
                    } catch (error: any) {
                        console.error('Error fetching navigation:', error);
                    }
                }
            }

            fetchNavigation();
        }
    }, [id, runtimeProps.adminFetcher]);

    const handlePrevious = () => {
        if (navigation?.prev_id) {
            const prevId = navigation.prev_id;
            navigate(`/submissions/${prevId}/show`);
        }
    };

    const handleNext = () => {
        if (navigation?.next_id && navigation.next_id) {
            const nextId = navigation.next_id;
            navigate(`/submissions/${nextId}/show`);
        }
    };

    const arxivCheckUrl = record?.id ? UriTemplate(runtimeProps.URLS.CheckSubmissionLink).fill({
        arxivCheck: runtimeProps.ARXIV_CHECK,
        submissionId: record.id,
    }) : '';

    return (
        <TopToolbar sx={{ justifyContent: 'space-between' }}>
            <Button
                component="a"
                href={arxivCheckUrl}
                target="_blank"
                rel="noopener noreferrer"
                variant="outlined"
                disabled={!record?.id}
                endIcon={<LaunchIcon />}
            >
                Jump to arXiv Check
            </Button>
            <Box display="flex" gap={1}>
                <EditButton />
                <Button
                    variant="outlined"
                    startIcon={<ArrowBackIcon />}
                    onClick={handlePrevious}
                    disabled={!navigation?.prev_id}
                >
                    Previous
                </Button>
                <Button
                    variant="outlined"
                    endIcon={<ArrowForwardIcon />}
                    onClick={handleNext}
                    disabled={!navigation?.next_id}
                >
                    Next
                </Button>
            </Box>
        </TopToolbar>
    );
};

const SubmissionRecordContent = () => {
    return (
        <Paper elevation={2}>
            <SubmissionTable mode="show" />
        </Paper>
    );
}


export const SubmissionShow = () => {
    return (
        <Box display={"flex"} flexDirection={"column"} width={"80%"} ml={"10%"} maxWidth={"lg"} >
            <Show actions={false} component={"div"}>
                <ConsoleTitle><SubmissionTitle /></ConsoleTitle>
                <SubmissionShowActions />
                <SimpleShowLayout>
                    <SubmissionRecordContent />
                </SimpleShowLayout>
                <Divider sx={{ my: 3 }} />
                <SubmissionAdminLogAccordion />

            </Show>
        </Box>
    );
};
