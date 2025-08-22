import {Box, Table, TableRow, TableCell, Accordion, AccordionSummary, AccordionDetails, Typography} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
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
import CategoryInputField from "../bits/CategoryInputField";
// import SubmissionCategoriesField, {CategoriesField, CategoryList} from "../bits/SubmissionCategoriesField";
import IsOkField from "../bits/IsOkField";
import {RuntimeContext} from "../RuntimeContext";
import ArxivCheckSubmissionLink from "../bits/ArxivCheckSubmissionLink";
import ISODateField from '../bits/ISODateFiled';
import UriTemplate from 'uri-templates';
import Button from '@mui/material/Button';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import LinkIcon from '@mui/icons-material/Link';
import { useNavigate } from 'react-router-dom';

import {paths as adminApi, components as adminComponents} from "../types/admin-api";
import UserNameField from "../bits/UserNameField";
import CategoryField from "../bits/CategoryField";
import PrimaryCategoryField from "../bits/PirmaryCategoryField";
import AdminLogField from "../bits/AdminLogField";


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
            <BooleanInput label="Valid" source="flag_valid"/>

        </Filter>
    );
};


export const SubmissionList = () => {
    const defaultDates = calculatePresetDates('last_28_days');

    return (
        <List filters={<SubmissionFilter/>}
              filterDefaultValues={{
                  submission_status: [],
              }}
              sort={{ field: 'id', order: 'DESC' }}
        >
            <Datagrid rowClick={false} bulkActionButtons={false}>
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
                <AdminLogField source="id" label={"Log"}/>
                <IsOkField source="is_ok" label={"OK?"}/>
            </Datagrid>
        </List>
    );
};


const SubmissionTitle = () => {
    const record = useRecordContext();
    return <span>Submission {record ? `"${record.last_name}, ${record.first_name}" - ${record.email}` : ''}</span>;
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
    <Accordion>
        <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls="admin-logs-content"
            id="admin-logs-header"
        >
            <Typography>Admin Logs</Typography>
        </AccordionSummary>
        <AccordionDetails>
            <SubmissionAdminLogList />
        </AccordionDetails>
    </Accordion>
);

const SubmissionEditToolbar = () => (
    <Toolbar>
        <SaveButton />
    </Toolbar>
);

export const SubmissionEdit = () => {
    return (
        <Box display={"flex"} flexDirection={"column"}>
            <Edit >
                <SubmissionAdminLogAccordion />
                <SimpleForm toolbar={<SubmissionEditToolbar />}>
                    <Table size="small">
                        <TableRow>
                            <TableCell>ID</TableCell>
                            <TableCell>
                                <ArxivCheckSubmissionLink source={"id"} />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Source Format</TableCell>
                            <TableCell>
                                <TextField source="source_format"/>
                                {" - "}
                                <NumberField source="source_size"/>
                                {" bytes"}
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Status</TableCell>
                            <TableCell>
                                <SelectInput source="status" choices={submissionStatusOptions} helperText={false}/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>User Identity</TableCell>
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
                            <TableCell>Email</TableCell>
                            <TableCell>
                                <ReferenceField source="submitter_id" reference="users" label={"Submitter"}>
                                    <EmailField source={"email"}/>
                                </ReferenceField>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>From Name</TableCell>
                            <TableCell>
                                <TextInput source="submitter_name" helperText={false}/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>From Email</TableCell>
                            <TableCell>
                                <TextInput source="submitter_email" helperText={false}/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Date Created</TableCell>
                            <TableCell>
                                <ISODateField source="created" label="Created"/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Date Updated</TableCell>
                            <TableCell>
                                <ISODateField source="updated"/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Categories</TableCell>
                            <TableCell colSpan={3}>
                                <CategoryInputField source="id" sourceCategory="archive"
                                                    sourceClass="subject_class"
                                                    helperText={false}
                                />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Title</TableCell>
                            <TableCell colSpan={3}>
                                <TextInput source="title" helperText={false}/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Authors</TableCell>
                            <TableCell colSpan={3}>
                                <TextInput source="authors" helperText={false}/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Comments</TableCell>
                            <TableCell colSpan={3}>
                                <TextInput source="comments" helperText={false}/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>License</TableCell>
                            <TableCell colSpan={3}>
                                <TextField source="license"/>
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>Abstract</TableCell>
                            <TableCell colSpan={3}>
                                <TextInput source="abstract" multiline rows={20} helperText={false}/>
                            </TableCell>
                        </TableRow>
                    </Table>
                </SimpleForm>
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
        const getNavigation = runtimeProps.adminFetcher.path('/v1/submissions/navigate').method('get').create();
        async function fetchNavigation() {
            if (id) {
                try {
                    const response = await getNavigation({id: Number(id)});
                    if (response.ok) {
                        setNavigation(response.data);
                    }
                }
                catch (error: any) {
                    console.error('Error fetching navigation:', error);
                }
            }
        }

        fetchNavigation();
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

    const handleArxivCheck = () => {
        if (record?.id) {
            const url = UriTemplate(runtimeProps.URLS.CheckSubmissionLink).fill({
                arxivCheck: runtimeProps.ARXIV_CHECK,
                submissionId: record.id,
            });
            window.open(url, '_blank');
        }
    };

    return (
        <TopToolbar sx={{ justifyContent: 'space-between' }}>
            <Button
                variant="outlined"
                startIcon={<LinkIcon />}
                onClick={handleArxivCheck}
                disabled={!record?.id}
            >
                arXiv Check
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
        <Table size="small">
            <TableRow>
                <TableCell>ID</TableCell>
                <TableCell>
                    <ArxivCheckSubmissionLink source={"id"} />
                    {" / "}
                    <TextField source="document_id"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Source Format</TableCell>
                <TableCell>
                    <TextField source="source_format"/>
                    {" - "}
                    <NumberField source="source_size"/>
                    {" bytes"}
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Status</TableCell>
                <TableCell>
                    <SelectField source="status" choices={submissionStatusOptions}/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>User Identity</TableCell>
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
                <TableCell>Email</TableCell>
                <TableCell>
                    <ReferenceField source="submitter_id" reference="users" label={"Submitter"}>
                        <EmailField source={"email"}/>
                    </ReferenceField>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>From Name</TableCell>
                <TableCell>
                    <TextField source="submitter_name"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>From Email</TableCell>
                <TableCell>
                    <TextField source="submitter_email"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Date Created</TableCell>
                <TableCell>
                    <ISODateField source="created" label="Created"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Date Updated</TableCell>
                <TableCell>
                    <ISODateField source="updated"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Submission Date</TableCell>
                <TableCell>
                    <ISODateField source="submit_time"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Release Time</TableCell>
                <TableCell>
                    <ISODateField source="release_time"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Categories</TableCell>
                <TableCell colSpan={3}>
                    <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Title</TableCell>
                <TableCell colSpan={3}>
                    <TextField source="title"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Authors</TableCell>
                <TableCell colSpan={3}>
                    <TextField source="authors"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Comments</TableCell>
                <TableCell colSpan={3}>
                    <TextField source="comments"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>License</TableCell>
                <TableCell colSpan={3}>
                    <TextField source="license"/>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Abstract</TableCell>
                <TableCell colSpan={3}>
                    <TextField source="abstract"/>
                </TableCell>
            </TableRow>
        </Table>

    );
}


export const SubmissionShow = () => {
    return (
        <Box display={"flex"} flexDirection={"column"}>
            <Show actions={<SubmissionShowActions />}>
                <SubmissionAdminLogAccordion />
                <SimpleShowLayout>
                    <SubmissionRecordContent />
                </SimpleShowLayout>
            </Show>
        </Box>
    );
};
