import React, {useState, useEffect} from 'react';

import Box from '@mui/material/Box';
import Card from '@mui/material/Card';
import CardContent from '@mui/material/CardContent';
import CardHeader from '@mui/material/CardHeader';
import Stack from '@mui/material/Stack';
import Table from '@mui/material/Table';
import TablePagination from '@mui/material/TablePagination';
import TableCell from '@mui/material/TableCell';
import TableRow from '@mui/material/TableRow';
import TableHead from '@mui/material/TableHead';
import Typography from '@mui/material/Typography';
// import ToggleButton from '@mui/material/ToggleButton';
import Toolbar from '@mui/material/Toolbar';
import Tooltip from '@mui/material/Tooltip';
import Chip from '@mui/material/Chip';
import FormLabel from '@mui/material/FormLabel';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import SaveIcon from '@mui/icons-material/Save';

import YesIcon from '@mui/icons-material/Check';

import {
    useDataProvider,
    List,
    Datagrid,
    TextField,
    EmailField,
    DateField,
    NumberField,
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
    useListContext,
    ReferenceField,
    Show,
    useGetOne, RadioButtonGroupInput,
    RecordContextProvider,
    ReferenceArrayField,
    useGetList,
    UseListOptions,
    SaveButton, useSaveContext,
} from 'react-admin';


import { useParams, useNavigate } from 'react-router-dom';

import { addDays } from 'date-fns';
import CircularProgress from "@mui/material/CircularProgress";
import Button from '@mui/material/Button';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useFormContext } from 'react-hook-form';

import {paths as adminApi} from "../types/admin-api";
import HighlightText from "../bits/HighlightText";
// type ArxivDocument = adminApi['/v1/documents/paper_id/{paper_id}']['get']['responses']['200']['content']['application/json'];
// type OwnershipRequestsRequest = adminApi['/v1/ownership_requests/']['post']['requestBody']['content']['application/json'];
// type OwnershipRequestsList = adminApi['/v1/ownership_requests/']['get']['responses']['200']['content']['application/json'];
type OwnershipRequestType = adminApi['/v1/ownership_requests/{id}']['get']['responses']['200']['content']['application/json'];
type PaperOwnerType = adminApi['/v1/paper_owners/{id}']['get']['responses']['200']['content']['application/json'];
type DocumentType = adminApi['/v1/documents/{id}']['get']['responses']['200']['content']['application/json'];
type DocumentIdType = DocumentType['id'];

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
    return (
        <List filters={<OwnershipRequestFilter />} filterDefaultValues={{workflow_status: "pending"}}>
            <Datagrid sort={{field: 'id', order: 'ASC'}}> rowClick="edit"
                <NumberField source="id" label={"Req ID"}/>
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
                <ReferenceField source="ownershipRequest_id" reference="ownership_requests_audit" label={"Remote host"}>
                    <TextField source={"remote_host"} defaultValue={"Unknown"}/>
                </ReferenceField>
            </Datagrid>
        </List>
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


const PaperOwnerList: React.FC<{
    nameFragments: string[];
}> = ({nameFragments}) => {
    const record = useRecordContext<PaperOwnerType>();
    const dataProvider = useDataProvider();
    const [paperOwners, setPaperOwners] = useState<PaperOwnerType[]>([]);
    const [documents, setDocuments] = useState<DocumentType[] | undefined>(undefined);
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
                    dataProvider.getOne<DocumentType>('documents', {id: ownership.document_id})
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
                    <TableRow key={`doc_${document.id}_row_${index}`}>
                        <TableCell key={`doc_${document.id}_row_${index}_owner`}>
                            {paperOwners[index]?.flag_author ? <YesIcon /> : null}
                        </TableCell>
                        <TableCell  key={`doc_${document.id}_row_${index}_doc`}>
                            <ReferenceField source="id" reference="documents" record={document} link="show">
                                <TextField source="paper_id" />
                            </ReferenceField>
                        </TableCell>
                        <TableCell key={`doc_${document.id}_row_${index}_title`}>
                            {document.title}
                        </TableCell>
                        <TableCell key={`doc_${document.id}_row_${index}_authors`}>
                            <HighlightText text={document.authors || ""} highlighters={nameFragments}/>
                        </TableCell>
                        <TableCell key={`doc_${document.id}_row_${index}_dated`}>
                            {document.dated}
                        </TableCell>
                    </TableRow>
                ))}
            </Table>
        </>
    );
};

interface RequestedPaperListProps {
    userId: number;
    workflowStatus: WorkflowStatusType; // Expecting a string prop for workflowStatus
    nameFragments: string[];
    documents: DocumentType[];
    selectedDocuments: DocumentIdType[];
    setSelectedDocuments: (newSel: DocumentIdType[]) => void;
}


const RequestedPaperList: React.FC<RequestedPaperListProps> = ({userId, workflowStatus, nameFragments, documents, selectedDocuments, setSelectedDocuments}) => {
/*
    const record = useRecordContext<OwnershipRequestType>();
    const dataProvider = useDataProvider();
    const [paperOwners, setPaperOwners] = useState<any[] | undefined>(undefined);

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
                        console.log("paper-owner: " + JSON.stringify(data));
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

*/
    const {register, setValue} = useFormContext();
    register('selected_documents');
    setValue('selected_documents', selectedDocuments);

    const docSelectionChange = (doc: DocumentType) => {
        const newSelection =  selectedDocuments.includes(doc.id) ?
            selectedDocuments.filter( (id) => id !== doc.id)
            :
            selectedDocuments.concat(doc.id);
        setSelectedDocuments(newSelection);
    }

    if (!documents) {
        return (<Typography>
            Requested papers - loading...
        </Typography>)
    }
    console.log("docSelectionChange ", JSON.stringify(selectedDocuments));

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
                            <Chip
                                id={`user_${userId}-doc_${document.id}`}
                                label={document.id}
                                color={selectedDocuments.includes(document.id) ? 'primary' : 'default'}
                                variant={selectedDocuments.includes(document.id) ? 'filled' : 'outlined'}
                                onClick={() => docSelectionChange(document)}
                                clickable
                            />
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
                            <HighlightText text={document.authors || ""} highlighters={nameFragments}/>
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

const OwnershipRequestSaveButton = ({ disabled }: { disabled: boolean }) => {
    const { save, saving } = useSaveContext();
    const { handleSubmit } = useFormContext();

    const onSubmit = handleSubmit((values) => {
        if (save) {
            save(values); // safe and validated
        }
    });

    return (
        <Button
            onClick={onSubmit}
            disabled={disabled || saving}
            startIcon={<SaveIcon />}
            variant="contained"
        >
            Save
        </Button>
    );
};

const OwnershipRequestToolbar = ({ prevId, nextId, ok }: { prevId: number | null; nextId: number | null; ok:boolean }) => {
    const navigate = useNavigate();

    return (
        <Toolbar>
            {/* Default Save button */}
            <OwnershipRequestSaveButton disabled={!ok}  />
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


const WorkflowStatusSelection = (
    {
        workflowStatus,
        resetSelection,
        rejectRequest
    }: {
        workflowStatus: "accepted" | "rejected" | "pending",
        resetSelection: () => void,
        rejectRequest: () => void,
    }
) => {
    const { register, setValue, } = useFormContext();

    // Register and update the field value in the form
    useEffect(() => {
        register('workflow_status');
        setValue('workflow_status', workflowStatus);
    }, [register, setValue, workflowStatus]);

    return (
        <FormControl component="fieldset" sx={{ mt: 2 }}>
            <FormLabel component="legend">Workflow Status</FormLabel>
            <RadioGroup value={workflowStatus} row>
                <FormControlLabel value="accepted" control={<Radio />} label="Accept" disabled />
                <FormControlLabel value="rejected" control={<Radio />} label="Reject" onClick={rejectRequest}  />
                <FormControlLabel value="pending" control={<Radio />} label="Pending" onClick={resetSelection} />
            </RadioGroup>
        </FormControl>
    );
};


const OwnershipRequestEditContent = ({ id, nameFragments, ownershipRequest }: { id: string, nameFragments: string[], ownershipRequest: OwnershipRequestType }) => {
    const dataProvider = useDataProvider();
    const [workflowStatus, setWorkflowStatus] = useState<'pending' | 'accepted' | 'rejected'>('pending'); // State to hold workflow_status
/*
    const handleWorkflowStatusChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
        setWorkflowStatus(event.target.value as any);
    };

 */

    const [listOptions, setListOptions] = useState<UseListOptions>(
        {
            filter: {workflow_status: "pending", current_id: id},
        }
    );

    const [documents, setDocuments] = useState<DocumentType[]>([]);
    const [selectedDocuments, setSelectedDocuments] = useState<DocumentIdType[]>([]);

    const {data, isLoading } = useGetList<OwnershipRequestType>("ownership_requests", listOptions);

    useEffect(() => {
        const fetchDocuments = async () => {
            console.log('Fetching documents ' + JSON.stringify(ownershipRequest));
            if (ownershipRequest?.document_ids) {
                const documentPromises = ownershipRequest.document_ids.map((doc_id) =>
                    dataProvider.getOne<DocumentType>('documents', { id: doc_id })
                );

                const results = await Promise.allSettled(documentPromises);

                const successfulDocuments = results
                    .filter(result => result.status === 'fulfilled')
                    .map((result) => (result as PromiseFulfilledResult<{ data: DocumentType }>).value.data);

                /* setSelectedDocuments([]); */
                setDocuments(successfulDocuments);
            }
        };
        fetchDocuments();
    }, [ownershipRequest, dataProvider]);

    const [paperOwners, setPaperOwners] = useState<PaperOwnerType[]>([]);

    useEffect(() => {
        if (documents) {
            const user_id = ownershipRequest.user_id;
            const fetchOwnership = async () => {
                const ownershipPromises = documents.map(async (doc) => {
                    const fake_id = `user_${user_id}-doc_${doc.id}`;
                    try {
                        const response = await dataProvider.getOne<PaperOwnerType>('paper_owners_user_doc', { id: fake_id });
                        const data = {...response.data,
                            user_id: user_id,
                            document_id: doc.id,
                        };
                        console.log("paper-owner: " + JSON.stringify(data));
                        return data;
                    } catch (error) {
                        return {
                            id: fake_id,
                            document_id: doc.id,
                            user_id: user_id,
                            valid: false,
                            flag_author: false,
                            flag_auto: false,
                        };
                    }
                });

                const results = await Promise.allSettled(ownershipPromises);
                const successfulPaperOwners = results
                    .filter((result): result is PromiseFulfilledResult<PaperOwnerType> => result.status === 'fulfilled')
                    .map((result) => result.value);

                setPaperOwners(successfulPaperOwners);
            };

            fetchOwnership();
        }
    }, [documents, dataProvider]);

    useEffect(() => {
        const validDocs = paperOwners.filter((paperOwner: PaperOwnerType) => paperOwner.valid);
        setSelectedDocuments(validDocs.map((doc) => doc.document_id));
    }, [paperOwners]);

    const selectionChanged = (newSelection: DocumentIdType[]) => {
        if (newSelection && newSelection.length > 0)
            setWorkflowStatus("accepted");
        else
            setWorkflowStatus("rejected");
        setSelectedDocuments(newSelection);
    }

    const resetSelection = () => {
        setSelectedDocuments([]);
        setWorkflowStatus("pending");
    }

    const rejectRequest = () => {
        setSelectedDocuments([]);
        setWorkflowStatus("rejected");
    }

    if (isLoading || !data) return (
        <div>
            <Typography>Getting Ownership Request</Typography>
            <CircularProgress />
        </div>
    );

    const ids = data.map(record => record.id);
    const currentIndex = ids.indexOf(Number(id));
    const prevId = currentIndex > 0 ? ids[currentIndex - 1] : null;
    const nextId = currentIndex < ids.length - 1 ? ids[currentIndex + 1] : null;

    const ok_to_save = workflowStatus === 'rejected' || (workflowStatus === 'accepted' && selectedDocuments.length > 0);

    return (
        <Edit title={<OwnershipRequestTitle />} redirect={false}>
            <SimpleForm toolbar={<OwnershipRequestToolbar prevId={prevId} nextId={nextId} ok={ok_to_save} />}

            >
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
                        <RequestedPaperList
                            userId={ownershipRequest.user_id}
                            workflowStatus={workflowStatus} nameFragments={nameFragments}
                            documents={documents}
                            selectedDocuments={selectedDocuments}
                            setSelectedDocuments={selectionChanged}
                        />
                    </CardContent>
                </Card>
                <WorkflowStatusSelection workflowStatus={workflowStatus} resetSelection={resetSelection} rejectRequest={rejectRequest} />
                <input type="hidden" name="workflow_status" value={workflowStatus} />

            </SimpleForm>
            <PaperOwnerList nameFragments={nameFragments}/>
        </Edit>
    );
}

export const OwnershipRequestEdit = () => {
    const { id } = useParams();

    const { data: this_request, isLoading } = useGetOne<OwnershipRequestType>('ownership_requests', { id: Number(id || "0") }, { enabled: !!id });
    const { data: this_user, isLoading: isUserLoading } = useGetOne('users', {
        id: this_request?.user_id,
    }, { enabled: !!this_request?.user_id });

    const nameFragments = !isUserLoading && this_user
        ? [this_user.first_name, this_user.last_name]
        : [];

    if (!id || !this_request || !this_user) return null;

    return <OwnershipRequestEditContent key={id} id={id} nameFragments={nameFragments} ownershipRequest={this_request} />
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