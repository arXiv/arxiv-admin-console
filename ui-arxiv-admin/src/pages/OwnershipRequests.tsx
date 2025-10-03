import React, {useState, useEffect, useContext} from 'react';

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
import ConsoleTitle from "../bits/ConsoleTitle";
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
// import ToggleButton from '@mui/material/ToggleButton';
import Toolbar from '@mui/material/Toolbar';
import Tooltip from '@mui/material/Tooltip';
import Chip from '@mui/material/Chip';
import FormLabel from '@mui/material/FormLabel';
import FormControl from '@mui/material/FormControl';
import FormControlLabel from '@mui/material/FormControlLabel';
import Radio from '@mui/material/Radio';
import RadioGroup from '@mui/material/RadioGroup';
import SuspectIcon from '@mui/icons-material/Dangerous';

import {
    useDataProvider,
    List,
    Datagrid,
    TextField,
    EmailField,
    NumberField,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    DateInput,
    SelectInput,
    useListContext,
    ReferenceField,
    Show,
    useGetOne,
    ReferenceArrayField,
    useGetList,
    UseListOptions,
    SaveButton, useSaveContext, useEditContext, ButtonProps, BooleanField,
} from 'react-admin';


import { useParams, useNavigate } from 'react-router-dom';

import { addDays } from 'date-fns';
import CircularProgress from "@mui/material/CircularProgress";
import Button from '@mui/material/Button';

import { useFormContext } from 'react-hook-form';

import {paths as adminApi, components as adminComponents} from "../types/admin-api";
import HighlightText from "../bits/HighlightText";
import {RuntimeContext} from "../RuntimeContext";
import ISODateField from '../bits/ISODateFiled';
import ToggleButton from "@mui/material/ToggleButton";

import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import AcceptIcon from '@mui/icons-material/Star';
import YesIcon from '@mui/icons-material/Check';
import RejectIcon from '@mui/icons-material/DoNotDisturb';
import Paper from "@mui/material/Paper";
import OwnershipConclusionButton from '../bits/OwnershipConclusionButton';
import PaperOwnersList from "../components/PaperOwnersList";
import UserNameField from "../bits/UserNameField";
import UserStatusField from '../bits/UserStatusField';
import {StandardAccordion} from "../components/StandardAccordion";


// type ArxivDocument = adminApi['/v1/documents/paper_id/{paper_id}']['get']['responses']['200']['content']['application/json'];
// type OwnershipRequestsRequest = adminApi['/v1/ownership_requests/']['post']['requestBody']['content']['application/json'];
// type OwnershipRequestsList = adminApi['/v1/ownership_requests/']['get']['responses']['200']['content']['application/json'];
type OwnershipRequestType = adminApi['/v1/ownership_requests/{id}']['get']['responses']['200']['content']['application/json'];
type PaperOwnerType = adminApi['/v1/paper_owners/{id}']['get']['responses']['200']['content']['application/json'];
type DocumentType = adminApi['/v1/documents/{id}']['get']['responses']['200']['content']['application/json'];
type DocumentIdType = DocumentType['id'];
type OwnershipRequestNavi = adminApi['/v1/ownership_requests/navigate']['get']['responses']['200']['content']['application/json'];

type WorkflowStatusType = adminComponents['schemas']['WorkflowStatus'];

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
            return { preset: preset };
        case 'last_7_days':
            return { preset: preset };
        case 'last_28_days':
            return { preset: preset };
        default:
            return { startDate: null, endDate: null, preset: null};
    }
};


const OwnershipRequestFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();

    const handleWorkflowStatusChoice = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const value = event.target.value;
        setFilters({
            ...filterValues,
            workflow_status: value,
        });
    };

    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const preset = calculatePresetDates(event.target.value);
        setFilters({
            ...filterValues,
            preset: preset,
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
        <Box maxWidth={"xl"} sx={{ margin: '0 auto'}}>
            <ConsoleTitle>Ownership Requests</ConsoleTitle>

        <List filters={<OwnershipRequestFilter />} filterDefaultValues={{workflow_status: "pending"}}>
            <Datagrid rowClick="edit">
                <NumberField source="id" label={"Req ID"}/>
                <ISODateField source="date" label={"Date"}/>
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
        </Box>

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
            Ownership Request: {ownershipRequestData ? `${userData?.first_name || ''} ${userData?.last_name || ''}` : ''}
        </span>
    );
};


const PaperOwnerListContent: React.FC = () => {
    const { total } = useListContext();

    return (
        <Datagrid bulkActionButtons={false}>
            <ReferenceField source="document_id" reference="documents" link="show" label="arXiv ID">
                <TextField source="paper_id" />
            </ReferenceField>
            <ReferenceField source="document_id" reference="documents" label="Title">
                <TextField source="title" />
            </ReferenceField>
            <ReferenceField source="document_id" reference="documents" label="Date">
                <TextField source="dated" />
            </ReferenceField>
        </Datagrid>
    );
};

const PaperOwnerList: React.FC<{
    nameFragments: string[];
}> = ({nameFragments}) => {
    const record = useRecordContext<PaperOwnerType>();
    const [expanded, setExpanded] = useState<boolean>(false);
    const [documentCount, setDocumentCount] = useState<number>(0);

    const handleAccordionChange = (event: React.SyntheticEvent, isExpanded: boolean) => {
        setExpanded(isExpanded);
    };

    if (!record?.user_id) {
        return null;
    }

    return (
        <StandardAccordion
            title="Other papers owned by the user"
            summary={documentCount > 0 ? `${documentCount} documents` : undefined}
            onChange={handleAccordionChange}
        >
            <Paper>
                <List
                    resource="paper_owners"
                    filter={{ user_id: record.user_id }}
                    actions={false}
                    component="div"
                    perPage={25}
                >
                    <PaperOwnerListContentWrapper setDocumentCount={setDocumentCount} />
                </List>
            </Paper>
        </StandardAccordion>
    );
};

const PaperOwnerListContentWrapper: React.FC<{ setDocumentCount: (count: number) => void }> = ({ setDocumentCount }) => {
    const { total } = useListContext();

    useEffect(() => {
        if (total !== undefined) {
            setDocumentCount(total);
        }
    }, [total, setDocumentCount]);

    return <PaperOwnerListContent />;
};

interface RequestedPaperListProps {
    userId: number;
    workflowStatus: WorkflowStatusType; // Expecting a string prop for workflowStatus
    nameFragments: string[];
    documents: DocumentType[];
    authoredDocuments: DocumentIdType[];
    setSelectedDocuments: (newSel: DocumentIdType[]) => void;
    ownedPapers: number[];
}

const AuthorsField : React.FC<{
    nameFragments: string[];
    document: DocumentType;
}> = ({nameFragments, document}) => {
    const [submitter, setSubmitter] = useState<string[]>([]);
    const dataProvider = useDataProvider();

    useEffect(() => {
        dataProvider.getOne('users', {id: document.submitter_id}).then(
            (response) => {
                setSubmitter([response.data.first_name, response.data.last_name]);
            }
        );
    }, [document.submitter_id]);

    return (
        <span>
            <HighlightText text={document.authors || ""} highlighters={nameFragments} secondary={submitter}/>
        </span>

    );
}


const RequestedPaperList: React.FC<RequestedPaperListProps> = ({userId, workflowStatus, nameFragments, documents, authoredDocuments, setSelectedDocuments, ownedPapers}) => {
    const {register, setValue} = useFormContext();
    register('authored_documents');
    setValue('authored_documents', authoredDocuments);

    const docSelectionChange = (doc: DocumentType) => {
        const newSelection =  authoredDocuments.includes(doc.id) ?
            authoredDocuments.filter( (id) => id !== doc.id)
            :
            authoredDocuments.concat(doc.id);
        setSelectedDocuments(newSelection);
    }

    if (!documents) {
        return (<Typography>
            Requested papers - loading...
        </Typography>)
    }
    console.log("docSelectionChange ", JSON.stringify(authoredDocuments));

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
                    <TableCell>
                        <Tooltip title={"Author/non-Author"}><span>Author</span></Tooltip>
                    </TableCell>
                    <TableCell>Paper</TableCell>
                    <TableCell>Title</TableCell>
                    <TableCell>Submitter</TableCell>
                    <TableCell>Authors</TableCell>
                    <TableCell>Owners</TableCell>
                    <TableCell>Date</TableCell>
                </TableHead>
                {documents.map((document, index) => (
                    <TableRow key={document.id}>
                        <TableCell>
                            <ToggleButton
                                id={`author-user_${userId}-doc_${document.id}`}
                                onClick={() => docSelectionChange(document)}
                                value={`user_${userId}-doc_${document.id}`}
                                selected={authoredDocuments.includes(document.id)}
                                sx={{minWidth: "5em"}}
                            >
                                {authoredDocuments.includes(document.id) ? 'Yes' : 'No'}
                            </ToggleButton>
                        </TableCell>

                        <TableCell>
                            <ReferenceField source="id" reference="documents" record={document} link="show">

                            <Chip
                                id={`owner-user_${userId}-doc_${document.id}`}
                                label={ownedPapers.includes(document.id) ? 'Owns' : document.id}
                                variant={ownedPapers.includes(document.id) ? 'filled' : 'outlined'}
                            />
                            </ReferenceField>
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
                            <ReferenceField source="submitter_id" reference="users" record={document} link="edit">
                                <UserNameField />
                            </ReferenceField>
                        </TableCell>

                        <TableCell>
                            <AuthorsField nameFragments={nameFragments} document={document} />
                        </TableCell>
                        <TableCell>
                            <PaperOwnersList document_id={document.id} />
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


const OwnershipRequestToolbar = ({ prevId, nextId, setWorkflowStatus, ok }: {
    prevId: number | null;
    nextId: number | null;
    setWorkflowStatus: (newStatus: WorkflowStatusType) => void;
    ok: boolean;
}) => {
    const navigate = useNavigate();
    
    useEffect(() => {

        const handleKeyPress = (event: KeyboardEvent) => {
            // Save on Enter
            if (event.key === 'Enter' && !event.ctrlKey && !event.shiftKey) {
                const saveButton = document.querySelector('[data-testid="ownership-request-save-button"]');
                if (saveButton instanceof HTMLElement) {
                    saveButton.click();
                }
            }
            
            // Previous with Ctrl+Left
            if (event.ctrlKey && event.key === 'ArrowLeft') {
                const prevButton = document.querySelector('[data-testid="ownership-request-prev-button"]');
                if (prevButton instanceof HTMLElement) {
                    prevButton.click();
                }
            }
            
            // Next with Ctrl+Right
            if (event.ctrlKey && event.key === 'ArrowRight') {
                const nextButton = document.querySelector('[data-testid="ownership-request-next-button"]');
                if (nextButton instanceof HTMLElement) {
                    nextButton.click();
                }
            }
        };

        // Add event listener
        document.addEventListener('keydown', handleKeyPress);

        // Cleanup
        return () => {
            document.removeEventListener('keydown', handleKeyPress);
        };
    }, []);

    return (
        <Toolbar>
            {/* Default Save button */}
            <OwnershipConclusionButton
                disabled={!ok} nextId={nextId}
                setWorkflowStatus={setWorkflowStatus}
                conclusion={"accepted"}
                buttonLabel={nextId ? `Accept then ${nextId}` : "Accept"}
                startIcon={<AcceptIcon />}
                variant="contained"
            />
            {/* Navigation buttons */}
            <Stack direction="row" spacing={1} sx={{ ml: 2 }}>
                <Button
                    data-testid="ownership-request-prev-button"
                    variant="outlined"
                    startIcon={<ArrowBackIcon />}
                    onClick={() => navigate(`/ownership_requests/${prevId}`)}
                    disabled={!prevId}
                >
                    {prevId ?? ''}
                </Button>
                <Button
                    data-testid="ownership-request-next-button"
                    variant="outlined"
                    endIcon={<ArrowForwardIcon />}
                    onClick={() => navigate(`/ownership_requests/${nextId}`)}
                    disabled={!nextId}
                >
                    {nextId ?? ''}
                </Button>
            </Stack>
            <Box sx={{ flexGrow: 1 }} />

            <OwnershipConclusionButton
                disabled={!ok} nextId={nextId}
                setWorkflowStatus={setWorkflowStatus}
                conclusion={"rejected"}
                buttonLabel={"Reject"}
                startIcon={<RejectIcon />}
                variant="contained"
                color="error"
            />

        </Toolbar>
    );
};


const OwnershipRequestEditContent = ({ id, nameFragments, ownershipRequest }: { id: string, nameFragments: string[], ownershipRequest: OwnershipRequestType }) => {
    const runtimeProps = useContext(RuntimeContext);
    const dataProvider = useDataProvider();
    const [workflowStatus, setWorkflowStatus] = useState<WorkflowStatusType>('pending'); // State to hold workflow_status
/*
    const handleWorkflowStatusChange = (event: React.ChangeEvent<HTMLInputElement>): void => {
        setWorkflowStatus(event.target.value as any);
    };

 */

    const [documents, setDocuments] = useState<DocumentType[]>([]);
    const [authoredDocuments, setSelectedDocuments] = useState<DocumentIdType[]>([]);
    const [isMentioned, setIsMentioned] = useState<boolean>(false);

/*
    const [listOptions, setListOptions] = useState<UseListOptions>(
        {
            filter: {workflow_status: "pending", current_id: id},
        }
    );
    const {data, isLoading } = useGetList<OwnershipRequestType>("ownership_requests", listOptions);

 */
    const [navigation, setNavigation] = useState<OwnershipRequestNavi | null>(null);

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
                if (nameFragments.length > 0) {
                    const mentioned = successfulDocuments.filter(doc =>
                        nameFragments.filter((nf) => doc.authors?.includes(nf)).length > 0
                    );
                    if (mentioned.length > 0) {
                        setSelectedDocuments(mentioned.map(doc => doc.id));
                        setIsMentioned(true);
                    }
                }
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
                        const response = await dataProvider.getOne<PaperOwnerType>('paper_owners', { id: fake_id });
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

                console.log("successfulPaperOwners: " + JSON.stringify(successfulPaperOwners))
                setPaperOwners(successfulPaperOwners);
            };

            fetchOwnership();
        }
    }, [documents, dataProvider]);

    useEffect(() => {
        const validDocs = paperOwners.filter((paperOwner: PaperOwnerType) => paperOwner.valid);
        const mergedSelection = [...new Set([
            ...validDocs.map((doc) => doc.document_id),
            ...authoredDocuments
        ])];

        setSelectedDocuments(mergedSelection);
    }, [paperOwners]);

    const selectionChanged = (newSelection: DocumentIdType[]) => {
        setSelectedDocuments(newSelection);
    }


    useEffect(() => {
        async function fetchNavigation() {
            if (id) {
                try {
                    const response = await fetch(runtimeProps.ADMIN_API_BACKEND_URL + `/v1/ownership_requests/navigate?id=${id}`);
                    if (response.ok) {
                        const navi: OwnershipRequestNavi = await response.json();
                        setNavigation(navi);
                        console.log("navi: " + JSON.stringify(navi))
                    }
                }
                catch (error) {
                    console.log(error);
                }
            }
        }

        fetchNavigation();
    }, [id]);


    // const ids = data.map(record => record.id);

    const prevId = navigation?.prev_request_ids ? navigation?.prev_request_ids[0] : null;
    const nextId = navigation?.next_request_ids ? navigation?.next_request_ids[0] : null;

    const ok_to_save = workflowStatus === 'pending';
    const ownedPapers = paperOwners.filter((paper) => paper.valid).map((paper) => paper.document_id);

    return (
        <Edit title={false} redirect={false} component={"div"}>
            <ConsoleTitle><OwnershipRequestTitle /></ConsoleTitle>

            <Paper >
            <SimpleForm toolbar={<OwnershipRequestToolbar
                prevId={prevId} nextId={nextId} ok={ok_to_save} setWorkflowStatus={setWorkflowStatus} />}>
                    <Table>
                        <TableHead>
                            <TableCell>User</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Email</TableCell>
                            <TableCell>Info</TableCell>
                        </TableHead>
                        <TableRow>
                            <TableCell>
                                <ReferenceField source="user_id" reference="users"
                                                link={(record, reference) => `/${reference}/${record.id}`} >
                                    <UserNameField />
                                    <BooleanField source={"flag_suspect"} FalseIcon={null} TrueIcon={SuspectIcon}/>
                                </ReferenceField>
                            </TableCell>
                            <TableCell>
                                <ReferenceField source="user_id" reference="users"
                                                link={(record, reference) => `/${reference}/${record.id}`} >
                                    <UserStatusField source={"id"} variant={"labeled"}/>
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
                                    <ISODateField source={"date"} />
                                </ReferenceField>

                            </TableCell>
                        </TableRow>
                    </Table>
                    <RequestedPaperList
                        userId={ownershipRequest.user_id}
                        workflowStatus={workflowStatus} nameFragments={nameFragments}
                        documents={documents}
                        authoredDocuments={authoredDocuments}
                        setSelectedDocuments={selectionChanged}
                        ownedPapers={ownedPapers}
                    />
                <input type="hidden" name="workflow_status" value={workflowStatus} />

            </SimpleForm>
            </Paper>

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
        ? this_user.first_name.split(' ').concat(this_user.last_name.split(' '))
        : [];

    if (!id || !this_request || !this_user) return null;

    return (
        <Box ml={"10%"} width={"80%"} maxWidth={"xl"}>
            <OwnershipRequestEditContent key={id} id={id} nameFragments={nameFragments} ownershipRequest={this_request} />
        </Box>
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
    // const record = useRecordContext();
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
                    <ISODateField source="date"/>
                </Box>
                <ReferenceArrayField source="document_ids" reference="documents">
                    <TextField source="id"/>
                </ReferenceArrayField>
            </CardContent>
        </Card>
    </Show>)
}