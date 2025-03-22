import React, {useState, useEffect} from 'react';

import {
    Card,
    CardContent,
    CardHeader,
    Grid,
    Table,
    TableCell,
    TableRow,
    TableHead,
    useMediaQuery,
    Box,
    Typography,
    TablePagination,
    Tooltip,
    Toolbar,
    Stack
} from '@mui/material';

import YesIcon from '@mui/icons-material/Check';

import {
    useDataProvider,
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    DateField,
    NumberField,
    SortPayload,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    DateInput,
    SelectInput,
    ToggleThemeButton,
    useListContext,
    ReferenceField,
    NumberInput,
    Show,
    SimpleShowLayout,
    useGetOne, RadioButtonGroupInput,
    RecordContextProvider,
    ListContextProvider,
    SourceContextProvider,
    ReferenceArrayField,
    useList,
    useGetList,
    UseListOptions,
    SaveButton
} from 'react-admin';

import { useParams, useNavigate } from 'react-router-dom';

import { addDays } from 'date-fns';
import {json} from "node:stream/consumers";
import CircularProgress from "@mui/material/CircularProgress";
import Button from '@mui/material/Button';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';


import {paths as adminApi} from "./types/admin-api";
// type ArxivDocument = adminApi['/v1/documents/paper_id/{paper_id}']['get']['responses']['200']['content']['application/json'];
type OwnershipRequestsRequest = adminApi['/v1/ownership_requests/']['post']['requestBody']['content']['application/json'];
type OwnershipRequestsList = adminApi['/v1/ownership_requests/']['get']['responses']['200']['content']['application/json'];
type OwnershipRequestType = adminApi['/v1/ownership_requests/{id}']['get']['responses']['200']['content']['application/json'];
type OwnershipModel = adminApi['/v1/paper_owners/{id}']['get']['responses']['200']['content']['application/json'];

type WorkflowStatusType = 'pending' | 'accepted' | 'rejected';

const workflowStatus : {id: WorkflowStatusType, name: string}[]  = [
    { id: 'pending', name: 'Pending' },
    { id: 'accepted', name: 'Accepted' },
    { id: 'rejected', name: 'Rejected' },
];

const presetOptions = [
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
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
        default:
            return { startDate: null, endDate: null };
    }
};


const OwnershipRequestFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();

    const handleWorkflowStatusChoice = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const { startDate, endDate } = calculatePresetDates(event.target.value);
        setFilters({
            ...filterValues,
            startDate: startDate ? startDate.toISOString().split('T')[0] : '',
            endDate: endDate ? endDate.toISOString().split('T')[0] : '',
        });
    };

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
            <SelectInput
                label="Workflow Status"
                source="workflow_status"
                choices={workflowStatus}
                onChange={(event) => handleWorkflowStatusChoice(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
        </Filter>
    );
};


export const OwnershipRequestList = () => {
    const sorter: SortPayload = {field: 'ownershipRequest_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));

    return (
        <>
        <List filters={<OwnershipRequestFilter />} filterDefaultValues={{workflow_status: "pending"}}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.ownershipRequestname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid sort={sorter}> rowClick="edit" isRowExpandable={true}
                    <NumberField source="id" label={"Request ID"}/>
                    <DateField source="date" label={"Date"}/>
                    <ReferenceField source="user_id" reference="users"
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                    </ReferenceField>
                    <ReferenceField source="endorsement_request_id" reference="endorsement_requests" label={"Endorsement Request"}>

                    </ReferenceField>
                    <TextField source="workflow_status" label={"Status"}/>
                    <ReferenceField source="id" reference="ownership_requests_audit" label={"Remote host"}>
                        <TextField source={"remote_host"} defaultValue={"Unknown"}/>
                    </ReferenceField>

                </Datagrid>
            )}
        </List>
        </>
    );
};


const OwnershipRequestTitle = () => {
    const record = useRecordContext();

    // Fetch the ownership request data
    const { data: ownershipRequestData, isLoading: isLoadingOwnershipRequest } = useGetOne('ownership_requests', { id: record?.id });

    // Fetch the user data based on user_id from the ownership request
    const { data: userData, isLoading: isLoadingUser } = useGetOne('users', { id: ownershipRequestData?.user_id }, { enabled: !!ownershipRequestData?.user_id });

    if (!record) {
        return <span>Ownership Request - no record</span>;
    }

    if (isLoadingOwnershipRequest || isLoadingUser) {
        return <span>Ownership Request - Loading...</span>;
    }

    return (
        <span>
            Ownership Request {ownershipRequestData ? `"${ownershipRequestData.id}, ${userData?.first_name || ''}" - ${userData?.email}` : ''}
        </span>
    );
};


const PaperOwnerList: React.FC = () => {
    const record = useRecordContext<{
        id: number,
        document_ids: number[],
        user_id: number,
        endorsement_request_id: number | undefined,
        workflow_status: string,
    }>();
    const dataProvider = useDataProvider();
    const [paperOwners, setPaperOwners] = useState<OwnershipModel[]>([]);
    const [documents, setDocuments] = useState<any[] | undefined>(undefined);
    const [page, setPage] = useState(0);
    const [rowsPerPage, setRowsPerPage] = useState(25);

    useEffect(() => {
        if (record?.user_id) {
            const fetchPaperOwners = async () => {
                const paperOwners = await dataProvider.getList('paper_owners', {
                    filter: {user_id: record.user_id}});
                setPaperOwners(paperOwners.data);
            };
            fetchPaperOwners();
        }
    }, [record, dataProvider]);

    useEffect(() => {
        if (paperOwners) {
            const fetchDocuments = async () => {
                const documentPromises = paperOwners.map((ownership) =>
                    dataProvider.getOne('documents', {id: ownership.document_id})
                );

                const documentResponses = await Promise.all(documentPromises);
                setDocuments(documentResponses.map(response => response.data));
            };

            fetchDocuments();
        }
    }, [paperOwners, dataProvider]);


    const handleChangePage = (event: unknown, newPage: number) => {
        setPage(newPage);
    };

    const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
        setRowsPerPage(parseInt(event.target.value, 10));
        setPage(0);
    };

    if (documents === undefined) {
        return (<Typography>
            Other papers owned by the user - loading...
            </Typography>)
    }

    return (
        <>
            <Typography>
                Other papers owned by the user -{` ${documents.length} documents`}
            </Typography>
            <TablePagination
                rowsPerPageOptions={[10, 25, 100]}
                component="div"
                count={documents.length}
                rowsPerPage={rowsPerPage}
                page={page}
                onPageChange={handleChangePage}
                onRowsPerPageChange={handleChangeRowsPerPage}
            />
            <Table>
                <TableHead>
                    <TableCell>
                        Owner
                    </TableCell>
                    <TableCell>Paper</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Authors</TableCell>
                    <TableCell>Date</TableCell>
                </TableHead>
                {documents.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage).map((document, index) => (
                    <TableRow>
                        <TableCell>
                            {paperOwners[index]?.flag_author ? <YesIcon /> : null}
                        </TableCell>
                        <TableCell>
                            <ReferenceField source="id" reference="documents" record={document} link="show">
                                <TextField source="paper_id" />
                            </ReferenceField>
                        </TableCell>
                        <TableCell>
                            {document.title}
                        </TableCell>
                        <TableCell>
                            {document.authors}
                        </TableCell>
                        <TableCell>
                            {document.dated}
                        </TableCell>
                    </TableRow>
                ))}
            </Table>
        </>
    );
};

interface RequestedPaperListProps {
    workflowStatus: WorkflowStatusType; // Expecting a string prop for workflowStatus
}

const RequestedPaperList: React.FC<RequestedPaperListProps> = ({workflowStatus}) => {
    const record = useRecordContext<{
        id: number,
        document_ids: number[],
        user_id: number,
        endorsement_request_id: number | undefined,
        workflow_status: string,
    }>();
    const dataProvider = useDataProvider();
    const [documents, setDocuments] = useState<any[] | undefined>(undefined);
    const [paperOwners, setPaperOwners] = useState<any[] | undefined>(undefined);

    useEffect(() => {
        if (record?.document_ids) {
            const fetchDocuments = async () => {
                const documentPromises = record?.document_ids.map((doc_id) =>
                    dataProvider.getOne('documents', {id: doc_id})
                );

                const documentResponses = await Promise.all(documentPromises);
                setDocuments(documentResponses.map(response => response.data));
            };

            fetchDocuments();
        }
    }, [record, dataProvider]);

    useEffect(() => {
        if (documents && record) {
            const fetchOwnership = async () => {
                const ownershipPromises = documents.map(async (doc) => {
                    const fake_id = `user_${record.user_id}-doc_${doc.id}`;
                    try {
                        const response = await dataProvider.getOne('paper_owners', { id: fake_id });
                        const data = {...response.data,
                            user_id: record.user_id,
                            document_id: doc.id,
                        };
                        console.log("paper-owner: " + data);
                        return data;
                    } catch (error) {
                        return {
                            id: fake_id,
                            document_id: doc.id,
                            user_id: record.user_id,
                            valid: false,
                            flag_author: false,
                            flag_auto: false,
                        };
                    }
                });

                const ownershipResponses = await Promise.all(ownershipPromises);
                setPaperOwners(ownershipResponses);
            };

            fetchOwnership();
        }
    }, [record, documents, dataProvider]);

    useEffect(() => {
        if (paperOwners) {
            if (workflowStatus === "accepted") {
                const accepted = paperOwners.map( (paperOwner) => ({...paperOwner, flag_author: true}));
                console.log(accepted);
                setPaperOwners(accepted);
            }
        }
    }, [workflowStatus]);

    if (paperOwners === undefined || documents === undefined) {
        return (<Typography>
            Requested papers - loading...
        </Typography>)
    }

    return (
        <>
            <Typography>
                Requested papers
            </Typography>
            <Table>
                <TableHead>
                    <TableCell>
                    <Tooltip title={"If this is on, the user is already a owner"}><span>Owner</span></Tooltip>
                    </TableCell>
                    <TableCell>Paper</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Authors</TableCell>
                    <TableCell>Date</TableCell>
                </TableHead>
                {documents.map((document, index) => (
                    <TableRow key={document.id}>
                        <TableCell>
                            <RecordContextProvider key={document.id} value={paperOwners[index]} >
                                <BooleanInput name={`flag_author_doc_${document.id}`} source="flag_author" label=""/>
                            </RecordContextProvider>
                        </TableCell>
                        <TableCell>
                            <ReferenceField source="id" reference="documents" record={document} link="show">
                                <TextField source="paper_id" />
                            </ReferenceField>
                        </TableCell>
                        <TableCell>
                            {document.title}
                        </TableCell>
                        <TableCell>
                            {document.authors}
                        </TableCell>
                        <TableCell>
                            {document.dated}
                        </TableCell>
                    </TableRow>
                ))}
            </Table>
        </>
    );
};

const OwnershipRequestToolbar = ({ prevId, nextId }: { prevId: number | null; nextId: number | null }) => {
    const navigate = useNavigate();

    return (
        <Toolbar>
            {/* Default Save button */}
            <SaveButton />
            {/* Navigation buttons */}
            <Stack direction="row" spacing={1} sx={{ ml: 2 }}>
                <Button
                    variant="outlined"
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate(`/ownership_requests/${prevId}`)}
                    disabled={!prevId}
                >
                    {prevId ?? ''}
                </Button>
                <Button
                    variant="outlined"
                    endIcon={<ArrowForwardIcon />}
                    onClick={() => navigate(`/ownership_requests/${nextId}`)}
                    disabled={!nextId}
                >
                    {nextId ?? ''}
                </Button>
            </Stack>
        </Toolbar>
    );
};

export const OwnershipRequestEdit = () => {
    // const dataProvider = useDataProvider();
    const [workflowStatus, setWorkflowStatus] = useState<'pending' | 'accepted' | 'rejected'>('pending'); // State to hold workflow_status

    const handleWorkflowStatusChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
        setWorkflowStatus(event.target.value as any);
    };

    const { id } = useParams();

    const [listOptions, setListOptions] = useState<UseListOptions>(
        {
            filter: {"workflow_status": "pending"},
            sort: { field: 'id', order: 'ASC' }
        }
    );

    const {data, isLoading, total, error,  } = useGetList<OwnershipRequestType>("ownership_requests", listOptions);

    if (isLoading || !data) return (
        <div>
            <Typography>Getting Ownership Request</Typography>
            <CircularProgress />
        </div>
    );

    console.log(JSON.stringify(data));

    const ids = data.map(record => record.id);
    const currentIndex = ids.indexOf(Number(id));
    const prevId = currentIndex > 0 ? ids[currentIndex - 1] : null;
    const nextId = currentIndex < ids.length - 1 ? ids[currentIndex + 1] : null;

    return (
        <Edit title={<OwnershipRequestTitle />}>
            <SimpleForm toolbar={<OwnershipRequestToolbar prevId={prevId} nextId={nextId} />}>
                <Card >
                    <CardContent>
                        <Table>
                            <TableHead>
                                <TableCell>User</TableCell>
                                <TableCell>Email</TableCell>
                                <TableCell>Info</TableCell>
                            </TableHead>
                            <TableRow>
                                <TableCell>
                                    <ReferenceField source="user_id" reference="users"
                                                    link={(record, reference) => `/${reference}/${record.id}`} >
                                        <TextField source={"last_name"} />
                                        {", "}
                                        <TextField source={"first_name"} />
                                    </ReferenceField>
                                </TableCell>
                                <TableCell>
                                    <ReferenceField source="user_id" reference="users">
                                        <EmailField source={"email"} />
                                    </ReferenceField>
                                </TableCell>
                                <TableCell>
                                    <ReferenceField source="id" reference="ownership_requests_audit" label={"Audit"}>
                                        {"Remote host: "}
                                        <TextField source={"remote_host"} defaultValue={"Unknown"}/>
                                        {"Date: "}
                                        <DateField source={"date"} />
                                    </ReferenceField>

                                </TableCell>
                            </TableRow>
                        </Table>
                        <RequestedPaperList workflowStatus={workflowStatus} />
                    </CardContent>
                </Card>
                <RadioButtonGroupInput
                    source="workflow_status"
                    choices={[
                        { id: 'accepted', name: 'Accept' },
                        { id: 'rejected', name: 'Reject' },
                        { id: 'pending', name: 'Pending' },
                    ]}
                    label="Workflow Status"
                    onChange={handleWorkflowStatusChange}
                />
            </SimpleForm>
            <PaperOwnerList />
        </Edit>
    );
}

export const OwnershipRequestCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceInput source="ownershipRequestname" reference="ownershipRequests" />
            <TextInput source="first_name" />
            <TextInput source="last_name" />
            <TextInput source="email" />
        </SimpleForm>
    </Create>
);


export const OwnershipRequestShow = () => {
    const record = useRecordContext();
    return (
        <Show>
        <Card>
            <CardHeader title={<>
            {"Ownership Request: "}
                <TextField source="id"/>
            </>}
            />
            <CardContent>
                <ReferenceField source="endorsement_request_id" reference="endorsement_requests"/>
                <TextField source="workflow_status"/>
                <Box>
                    <TextField source="id"/>
                    <ReferenceField source="user_id" reference="users"
                                    link={(record, reference) => `/${reference}/${record.id}`}>
                        <TextField source={"last_name"}/>
                        {", "}
                        <TextField source={"first_name"}/>
                    </ReferenceField>
                    <DateField source="date"/>
                </Box>
                <ReferenceArrayField source="document_ids" reference="documents">
                    <TextField source="id"/>
                </ReferenceArrayField>
            </CardContent>
        </Card>
    </Show>)
}