import {
    SxProps,
    useMediaQuery,
    Switch,
    FormControlLabel,
    Card,
    CardContent,
    CardHeader,
} from '@mui/material';

// import ToggleButton from '@mui/material/ToggleButton';
// import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
// import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import Box from '@mui/material/Box';
import IconButton from '@mui/material/IconButton';
import Divider from '@mui/material/Divider';
import Paper from '@mui/material/Paper';
import EmailIcon from '@mui/icons-material/Email';
import EditIcon from '@mui/icons-material/Edit';


import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    SortPayload,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    ReferenceField,
    SelectInput,
    DateInput,
    RecordContextProvider,
    useDataProvider,
    SaveButton,
    DeleteButton, useNotify, useEditContext, useRefresh,
    Confirm,
    useGetRecordId, ArrayField
} from 'react-admin';

import DoDisturbOnIcon from '@mui/icons-material/DoDisturbOn';
import ArrowRightIcon from '@mui/icons-material/ArrowRight';
import React, {useContext, useEffect, useState} from "react";
import CategoryField from "../bits/CategoryField";
import PersonNameField from "../bits/PersonNameField";
import CareereStatusField from "../bits/CareereStatusField";
import TapirSessionInfo from "../bits/TapirSessionInfo";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";
import OwnedPaperList from "../bits/OwnedPaperList";
import {AdminAuditList} from "../bits/TapirAdminLogs";
import Button from '@mui/material/Button';
import LoginIcon from '@mui/icons-material/Login';
import SuspendIcon from '@mui/icons-material/Pause';
import CommentIcon from '@mui/icons-material/Comment';
import UploadIcon from '@mui/icons-material/Upload';
import PasswordIcon from '@mui/icons-material/Password';

import {RuntimeContext} from "../RuntimeContext"; // for "Become This User"
import {useLocation, useNavigate} from 'react-router-dom';
import EmailLinkField from "../bits/EmailLinkField";
import ModerationCategoryDialog from "../components/ModerationCategoryDialog";
import EndorsementCategoryDialog from "../components/EndorsementCategoryDialog";

import {paths as adminApi} from '../types/admin-api';
import CanSubmitToDialog from "../components/CanSubmitToDialog";
import CanEndorseForDialog from "../components/CanEndorseForDialog";
import PolicyClassField from "../bits/PolicyClassField";
import EmailHistoryList from "../bits/EmailHistoryList";
import ChangeEmailDialog from "../components/ChangeEmailDialog";
import ISODateField from "../bits/ISODateFiled";
import FlaggedToggle from "../components/FlaggedToggle";
import EndorsementRequestListField from '../bits/EndorsementRequestListField';
import UserFlagDialog from '../components/UserFlagDialog';
import BooleanField from '../bits/BooleanNumberField';
import UserNameField from "../bits/UserNameField";
import EndorsementCategoriesField from "../bits/EndorsementCategoriesField";
import UserNameDialog from "../components/UserNameDialog";
import {UserSubmissionList} from "../components/UserSumissionList";
import BulkPaperOwnerDialog from "../components/BulkPaperOwnerDialog";
import {StandardAccordion} from "../components/StandardAccordion";
import {LazyAccordion} from "../components/LazyAccordion";
import {DottedLineRow} from "../components/DottedLineRow";
import ChangePasswordDialog from "../components/ChangePasswordDialog";

type ModeratorT = adminApi['/v1/moderators/']['get']['responses']['200']['content']['application/json'][0];
type EndorsementT = adminApi['/v1/endorsements/']['get']['responses']['200']['content']['application/json'][0];
type SubmissionSummaryT = adminApi['/v1/submissions/user/{user_id}/summary']['get']['responses']['200']['content']['application/json'];
type PaperOwnershipSummaryT = adminApi['/v1/paper_owners/user/{user_id}/summary']['get']['responses']['200']['content']['application/json'];

const UserFilter = (props: any) => (
    <Filter {...props}>
        <BooleanInput label="Admin" source="flag_edit_users" defaultValue={true}/>
        <BooleanInput label="Mod" source="flag_is_mod" defaultValue={true}/>
        <TextInput label="Search by Email" source="email" alwaysOn/>
        <TextInput label="Login name" source="username"/>
        <TextInput label="Search by First name" source="first_name"/>
        <TextInput label="Search by Last Name" source="last_name"/>
        <BooleanInput label="Email bouncing" source="email_bouncing" defaultValue={true}/>
        <BooleanInput label="Flagged" source="suspect" defaultValue={true}/>
        <BooleanInput label="Non-academit email" source="is_non_academic" defaultValue={true}/>
        <BooleanInput label="Email verified" source="flag_email_verified" defaultValue={true}/>
        <DateInput label="Start joined date" source="start_joined_date"/>
        <DateInput label="End joined date" source="end_joined_date"/>
    </Filter>
);

// export default UserFilter;

interface VisibleColumns {
    email: boolean,
    joinedDate: boolean,
    mod: boolean,
}

export const UserList = () => {
    const _isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    const location = useLocation();
    const navigate = useNavigate();

    // Track if this is the initial load to prevent interference with user interactions
    const isInitialLoad = React.useRef(true);
    const lastProcessedSearch = React.useRef<string>('');

    useEffect(() => {
        // Skip processing if this is a user interaction (not initial load)
        if (!isInitialLoad.current) {
            return;
        }

        // Skip if we've already processed this exact search string
        if (lastProcessedSearch.current === location.search) {
            return;
        }

        const searchParams = new URLSearchParams(location.search);
        const filterParam = searchParams.get('filter');

        // Only process if there are filters and they might need cleanup
        if (filterParam) {
            try {
                const parsedFilters = JSON.parse(decodeURIComponent(filterParam));

                // Check if this looks like a URL that needs cleanup (has problematic filters)
                const hasProblematicFilters = Object.keys(parsedFilters).some(key =>
                    !['email', 'first_name', 'last_name', 'username', 'flag_edit_users', 'flag_is_mod',
                        'email_bouncing', 'suspect', 'is_non_academic', 'flag_email_verified',
                        'start_joined_date', 'end_joined_date'].includes(key)
                );

                if (hasProblematicFilters) {
                    // Create new filter object with only allowed filters
                    const allowedFilters: any = {};
                    const allowedKeys = ['email', 'first_name', 'last_name', 'username', 'flag_edit_users',
                        'flag_is_mod', 'email_bouncing', 'suspect', 'is_non_academic',
                        'flag_email_verified', 'start_joined_date', 'end_joined_date'];

                    allowedKeys.forEach(key => {
                        if (parsedFilters[key] !== undefined) {
                            allowedFilters[key] = parsedFilters[key];
                        }
                    });

                    // Preserve all other React Admin URL parameters (pagination, sorting, etc.)
                    const newSearchParams = new URLSearchParams(location.search);

                    if (Object.keys(allowedFilters).length > 0) {
                        newSearchParams.set('filter', encodeURIComponent(JSON.stringify(allowedFilters)));
                    } else {
                        newSearchParams.delete('filter');
                    }

                    const newUrl = `${location.pathname}?${newSearchParams.toString()}`;
                    lastProcessedSearch.current = newSearchParams.toString();

                    // Replace current URL without triggering a page reload
                    navigate(newUrl, {replace: true});
                }
            } catch (error) {
                console.error('Error parsing URL filters:', error);
            }
        }

        // Mark that initial load processing is complete
        isInitialLoad.current = false;
        lastProcessedSearch.current = location.search;
    }, [location.search, navigate, location.pathname]);

    return (
        <Box maxWidth={"lg"} sx={{backgroundColor: 'background.default' }} ml={"10%"} width={"80%"}>
            <ConsoleTitle>Users</ConsoleTitle>
            <List filters={<UserFilter/>}>
                <Datagrid rowClick="edit" bulkActionButtons={false}>
                    <TextField source={"id"} label="ID"/>
                    <UserNameField/>
                    <BooleanField source="flag_suspect" label={"Flagged"} FalseIcon={null} TrueIcon={DoDisturbOnIcon}/>
                    <EmailField source="email"/>
                    <ISODateField source="joined_date"/>
                    <BooleanField source="flag_edit_users" label={"Admin"} FalseIcon={null}/>
                    <BooleanField source="flag_is_mod" label={"Mod"} FalseIcon={null}/>
                    <BooleanField source="flag_banned" label={"Suspended"} FalseIcon={null}
                                  TrueIcon={DoDisturbOnIcon}/>
                    <ReferenceField source="moderator_id" reference="moderators"
                                    link={(record, reference) => `/${reference}/${record.moderator_id}`}>
                        <TextField source={"archive"}/>
                        {"/"}
                        <TextField source={"subject_class"}/>
                    </ReferenceField>
                </Datagrid>
            </List>
        </Box>
    );
};

const UserTitle = () => {
    const record = useRecordContext();
    return <span>{record ? `${record.first_name} ${record.last_name}` : ''}</span>;
};

const policyClassChoices = [
    {id: 0, name: 'Owner'},
    {id: 1, name: 'Admin'},
    {id: 2, name: 'Public user'},
    {id: 3, name: 'Legacy user'},
];

const vetoStatusChoices = [
    {id: 'ok', name: 'OK'},
    {id: 'no-endorse', name: 'No Endorse'},
    {id: 'no-upload', name: 'No Upload'},
    {id: 'no-replace', name: 'No Replace'},
];

const getVetoStatusName = (vetoStatus: string) => {
    const choice = vetoStatusChoices.find(c => c.id === vetoStatus);
    return choice ? choice.name : vetoStatus;
};

const VetoStatusField = ({source}: { source: string }) => {
    const record = useRecordContext();
    if (!record) return null;
    const vetoStatus = record[source] || 'ok';
    return <Typography variant="body2">{getVetoStatusName(vetoStatus)}</Typography>;
};

function UserDemographic() {
    /*
    const record = useRecordContext<any>();
    const [demographic, setDemographic] = useState<any>({country: "No data", affiliation: "No data", url: ""});
    const dataProvider = useDataProvider();

    useEffect(() => {
        const fetchDemographic = async (userId: number) => {
            try {
                const response = await dataProvider.getOne('demographics', {id: userId});
                setDemographic(response.data);
            } catch (error) {
                console.error("Error fetching demographic data:", error);
            }
        };

        if (record)
            fetchDemographic(record.id);
    }, [dataProvider, record]);
*/
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [tapirSessions, setTapirSessions] = useState<any[]>([]);
    const [totalTapirSessions, setTotalTapirSessions] = useState<number>(0);
    const [isLoading, setIsLoading] = useState<boolean>(false);


    useEffect(() => {
        const fetchTapirSessions = async () => {
            console.log("tapir session record: " + JSON.stringify(record?.id));
            if (record?.id) {
                setIsLoading(true);
                try {
                    const response = await dataProvider.getList('tapir_sessions', {
                        filter: {user_id: record.id},
                        sort: {field: "id", order: "DESC"},
                        pagination: {page: 1, perPage: 2}, // Only get the latest two
                    });
                    setTapirSessions(response.data);
                    setTotalTapirSessions(Number(response.total));
                } catch (error) {
                    console.error("Error fetching tapir sessions:", error);
                    setTapirSessions([]);
                    setTotalTapirSessions(0);
                } finally {
                    setIsLoading(false);
                }
            }
        };

        fetchTapirSessions();
    }, [dataProvider, record?.id]);


    /*
                        <Box display="flex" flexDirection="row" gap={1} justifyItems={"baseline"}>
                        <SelectInput source="policy_class" choices={policyClassChoices} helperText={false} />
                        <Box >
                            <Typography component={"span"} >Moderator
                                <BooleanField source="flag_is_mod" label={"Moderator"} />
                            </Typography>
                        </Box>
                    </Box>

                    <Divider />

     */
    return (
        <Card sx={{backgroundColor: '#1c1a17', borderRadius: '16px', mb: 2}}>
            <CardHeader
                title="System Data"
                sx={{
                    '& .MuiCardHeader-title': {
                        color: '#c4d82e',
                        fontSize: '1em',
                        fontWeight: 'bold'
                    }
                }}
            />
            <CardContent>
                <Box display="flex" flexDirection="column" gap={1}>
                    <DottedLineRow label="User ID">
                        <TextField source="id" component={"span"}/>
                    </DottedLineRow>

                    <DottedLineRow label="Login name">
                        <TextField source="username"/>
                    </DottedLineRow>

                    <DottedLineRow label="Policy class">
                        <PolicyClassField source="policy_class"/>
                    </DottedLineRow>

                    <DottedLineRow label="Last login">
                        <TapirSessionInfo source={"id"} index={0} isLoading={isLoading} total={totalTapirSessions}
                                          tapirSessions={tapirSessions}/>
                    </DottedLineRow>

                    <DottedLineRow label="Penultimate Login">
                        <TapirSessionInfo source={"id"} index={1} isLoading={isLoading} total={totalTapirSessions}
                                          tapirSessions={tapirSessions}/>
                    </DottedLineRow>

                    <DottedLineRow label="Total sessions">
                        <TapirSessionInfo source={"id"} index={-1} isLoading={isLoading} total={totalTapirSessions}
                                          tapirSessions={tapirSessions}/>
                    </DottedLineRow>

                    <DottedLineRow label="Joined Date">
                        <ISODateField source="joined_date"/>
                    </DottedLineRow>

                    <DottedLineRow label="Joined From">
                        <TextField source="joined_ip_num"/>
                    </DottedLineRow>

                    <DottedLineRow label="Affiliation">
                        <TextField source="affiliation"/>
                    </DottedLineRow>

                    <DottedLineRow label="Country">
                        <TextField source="country"/>
                    </DottedLineRow>

                    <DottedLineRow label="URL">
                        <TextField source="url"/>
                    </DottedLineRow>

                    <DottedLineRow label="Default Category">
                        <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id"/>
                    </DottedLineRow>

                    <DottedLineRow label="Career Status">
                        <CareereStatusField source="type"/>
                    </DottedLineRow>

                    <DottedLineRow label="arXiv Author ID">
                        <ReferenceField reference={"author_ids"} source={"id"}>
                            <TextField source="author_id" emptyText={"No author ID"}/>
                        </ReferenceField>
                    </DottedLineRow>

                    <DottedLineRow label="ORCID">
                        <ReferenceField reference={"orcid_ids"} source={"id"}>
                            <TextField source="orcid" />
                        </ReferenceField>
                    </DottedLineRow>
                </Box>
            </CardContent>
        </Card>);
}


function UserEndorsements({open, setOpen}: { open: boolean, setOpen: (open: boolean) => void }) {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [endorsements, setEndorsements] = useState<EndorsementT[]>([]);

    useEffect(() => {
        const fetchEndorsements = async () => {
            if (record?.id) {
                try {
                    const response = await dataProvider.getList('endorsements', {
                        filter: {endorsee_id: record.id}, sort: {field: 'archive,subject_class', order: 'ASC'},
                    });
                    setEndorsements(response.data);
                } catch (error) {
                    console.error("Error fetching endorsements data:", error);
                }
            }
        };

        fetchEndorsements();
    }, [dataProvider, record, open]);

    function Endorsement({domain}: { domain: EndorsementT }) {
        return (
            <RecordContextProvider value={domain}>
                <ReferenceField source="id" reference="endorsements" label={""}
                                link={(record, reference) => `/${reference}/${record.id}`}>
                    <CategoryField source="id" sourceCategory="archive" sourceClass="subject_class" renderAs={"chip"}/>
                </ReferenceField>
            </RecordContextProvider>
        );
    }

    return (
        <>
            {
                endorsements.map((endorsement, _index) => (
                    <Endorsement key={`${endorsement.id}`} domain={endorsement}/>
                ))
            }
            <EndorsementCategoryDialog
                open={open}
                setOpen={setOpen}
                userId={Number(record?.id) || 0}
            />
        </>
    );
}


function UserModerationCategories({open, setOpen}: { open: boolean, setOpen: (open: boolean) => void }) {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [moderationCategories, setModerationCategories] = useState<ModeratorT[]>([]);

    useEffect(() => {
        const fetchModerationCategories = async () => {
            if (record?.id) {

                try {
                    const response = await dataProvider.getList('moderators', {
                        filter: {user_id: record.id}, sort: {field: 'archive,subject_class', order: 'ASC'},
                    });
                    setModerationCategories(response.data);
                } catch (error) {
                    console.error("Error fetching moderators data:", error);
                }
            }
        };

        fetchModerationCategories();
    }, [dataProvider, record]);

    function ModerationCategory({domain}: { domain: ModeratorT }) {
        return (
            <RecordContextProvider value={domain}>
                <ReferenceField source="id" reference="moderators" label={""}
                                link={(record, reference) => `/${reference}/${record.id}`}>
                    <CategoryField source="id" sourceCategory="archive" sourceClass="subject_class" renderAs={"chip"}/>
                </ReferenceField>
            </RecordContextProvider>
        );
    }

    return (
        <>
            {
                moderationCategories.map((domain, _index) => (
                    <ModerationCategory key={`${domain.id}`} domain={domain}/>
                ))
            }

            <ModerationCategoryDialog
                open={open}
                setOpen={setOpen}
                userId={Number(record?.id) || 0}
            />
        </>
    );
}


type statusInputType = { source: string, label: string, disabled?: boolean, component?: string } | null;

interface EmailVerificationSwitchProps {
    onUpdateEmailVerified: (verified: boolean, userId: string) => void;
}

const EmailVerificationSwitch: React.FC<EmailVerificationSwitchProps> = ({onUpdateEmailVerified}) => {
    const [confirmOpen, setConfirmOpen] = useState(false);
    const [pendingVerified, setPendingVerified] = useState<boolean | null>(null);
    const record = useRecordContext();

    const handleChange = (event: React.ChangeEvent<HTMLInputElement>) => {
        const newValue = event.target.checked;
        setPendingVerified(newValue);
        setConfirmOpen(true);
    };

    const handleConfirm = () => {
        if (pendingVerified !== null && record?.id) {
            onUpdateEmailVerified(pendingVerified, record.id as string);
        }
        setConfirmOpen(false);
        setPendingVerified(null);
    };

    const handleCancel = () => {
        setConfirmOpen(false);
        setPendingVerified(null);
    };

    return (
        <>
            <FormControlLabel
                control={
                    <Switch
                        checked={Boolean(record?.flag_email_verified)}
                        onChange={handleChange}
                        size="small"
                    />
                }
                label="Email verified"
            />
            <Confirm
                isOpen={confirmOpen}
                title="Confirm Email Verification Change"
                content={`Are you sure you want to ${pendingVerified ? 'verify' : 'unverify'} this user's email address? This will clear off the existing log-in session if the user is being logged in.`}
                onConfirm={handleConfirm}
                onClose={handleCancel}
            />
        </>
    );
};

const UserEditContent = () => {
    const [isEndorsementsOpen, setIsEndorsementsOpen] = useState(false);
    const [isModOpen, setIsModOpen] = useState(false);
    const [canEndorseForOpen, setCanEndorseForOpen] = useState(false);
    const [canSubmitToOpen, setCanSubmitToOpen] = useState(false);
    const [changeEmailOpen, setChangeEmailOpen] = useState(false);
    const [changeUserNameOpen, setChangeUserNameOpen] = useState(false);
    const [addCommentOpen, setAddCommentOpen] = useState(false);
    const [vetoStatusOpen, setVetoStatusOpen] = useState(false);
    const [bulkPaperOwnerOpen, setBulkPaperOwnerOpen] = useState(false);
    const [changePasswordOpen, setChangePasswordOpen] = useState(false);
    const refresh = useRefresh(); // Import this from react-admin
    const notify = useNotify();
    const runtimeProps = useContext(RuntimeContext);
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [submissionSummary, setSubmissionSummary] = useState<SubmissionSummaryT | null>(null);
    const [paperOwnershipSummary, setPaperOwnershipSummary] = useState<PaperOwnershipSummaryT | null>(null);


    useEffect(() => {
        async function getUserSubmissionSummary() {
            if (record?.id) {
                try {
                    const response = await dataProvider.getOne("user-submission-summary", {id: record.id})
                    console.log("user submission summary: " + JSON.stringify(response));
                    if (response) {
                        setSubmissionSummary(response.data);
                    }
                }
                catch (error) {
                    console.error("Error fetching user submission summary:", error);
                }
            }
        }

        async function getPaperOwnershipSummary() {
            if (record?.id) {
                try {
                    const response = await dataProvider.getOne("user-paper-ownership-summary", {id: record.id})
                    if (response) {
                        setPaperOwnershipSummary(response.data);
                    }
                }
                catch (error) {
                    console.error("Error fetching user submission summary:", error);
                }
            }
        }

        getUserSubmissionSummary();
        getPaperOwnershipSummary();
    }, [dataProvider, record?.id]);

    const switchProps: SxProps = {
        flex: 4,
        size: "small",
        my: 0
    };

    const statusInputs: statusInputType[][] = [
        [
            {source: "flag_approved", label: "Approved"},
            {source: "flag_suspect", label: "Flagged", disabled: false, component: "FlaggedToggle"},
            {source: "flag_proxy", label: "Proxy"},
        ],
        [
            {source: "flag_banned", label: "Banned", disabled: false, component: "FlaggedToggle"},
            {source: "flag_deleted", label: "Deleted", disabled: false, component: "FlaggedToggle"},
            null,
        ],
        [
            {source: "flag_xml", label: "API Submitter"},
            {source: "flag_allow_tex_produced", label: "Allow PDF from TeX"},
            null,
        ]
    ];

    const adminInputs: statusInputType[][] = [
        [
            {source: "flag_edit_users", label: "Admin", component: "FlaggedToggle"},
            {source: "flag_edit_system", label: "Owner", component: "FlaggedToggle"},
            {source: "flag_can_lock", label: "Can Lock", component: "FlaggedToggle"},
        ],
        [
            {source: "flag_group_test", label: "Test"},
            {source: "flag_internal", label: "Internal", component: "FlaggedToggle"},
            null,
        ],
    ];

    const handleEmailChanged = (newEmail: string) => {
        refresh(); // Refresh the form to show the updated email
    };

    const handlePasswordChanged = () => {
        refresh();
    };

    const handleUserNameChanged = () => {

        refresh(); // Refresh the form to show the updated email
    };

    const handleFCommentAdded = () => {
        refresh();
    };

    const handleVetoStatusChanged = () => {
        refresh();
    };

    const updateEmailVerified = async (verified: boolean, userId: string) => {
        console.info(' updating email verification:', verified);

        if (!userId) {
            console.info(' no userId provided');
            return;
        }

        try {
            const putEmailVerified = runtimeProps.aaaFetcher.path('/account/{user_id}/email/verified').method('put').create();
            await putEmailVerified({
                user_id: userId,
                email_verified: verified
            });

            notify(`Email verification ${verified ? 'enabled' : 'disabled'}`, {type: 'success'});
            refresh();
        } catch (error) {
            notify('Failed to update email verification status', {type: 'error'});
            console.error('Error updating email verification:', error);
        }
    };

    const handleMasquerade = async () => {
        if (!record?.id) return;

        try {
            const response = await fetch(`${runtimeProps.AAA_URL}/impersonate/${record.id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
            });

            if ([301, 302, 303, 307, 308].includes(response.status)) {
                const location = response.headers.get('Location');
                if (location) {
                    window.location.href = location;
                    return;
                }
            }

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(errorText || 'Request failed');
            }

            notify('Switched to user session', {type: 'info'});
            window.location.href = '/';
        } catch (error: unknown) {
            let message = 'Unknown error';
            if (error instanceof Error) {
                message = error.message;
            }
            notify(`Masquerade failed: ${message}`, {type: 'error'});
        }
    };


    const buhchOfInputs = [...statusInputs, ...adminInputs];

    /*
          mutationOptions={{onSuccess: () => {refresh();}}}
     */
    const onSuccess = () => {
        notify(`WOOHOO! Changes saved`);
        refresh();
    };

    const labelWidth = '6rem';

    const usersSubSummary = submissionSummary ? `${submissionSummary.active.toLocaleString()} active, ${submissionSummary.submitted.toLocaleString()} submitted, ${submissionSummary.total.toLocaleString()} owned, ${submissionSummary.rejected.toLocaleString()} rejected` : "";
    const usersOwnershipSummary = paperOwnershipSummary ? `${paperOwnershipSummary.total.toLocaleString()} total, ${paperOwnershipSummary.author.toLocaleString()} authored` : "";

    return (
        <>
            <SimpleForm toolbar={false}>
                <Box sx={{display: 'flex', flexDirection: 'column', gap: 1}}>
                    <Typography variant="h1" gutterBottom>
                        <UserTitle/>
                    </Typography>

                    {/* Action buttons moved under user name */}
                    <Box sx={{display: 'flex', flexDirection: 'row', gap: 1, mb: 2}}>
                        <SaveButton/>
                        <Button
                            variant="contained"
                            color="secondary"
                            startIcon={<LoginIcon/>}
                            onClick={handleMasquerade}
                        >
                            Become This User
                        </Button>
                        <Button
                            variant="contained"
                            color="secondary"
                            startIcon={<CommentIcon/>}
                            onClick={() => setAddCommentOpen(true)}
                        >
                            Add comment
                        </Button>
                        <Button
                            variant="contained"
                            color="primary"
                            startIcon={<UploadIcon/>}
                            onClick={() => setBulkPaperOwnerOpen(true)}
                        >
                            Bulk Paper Owner
                        </Button>

                        <Button
                            variant="contained"
                            color="primary"
                            startIcon={<PasswordIcon/>}
                            onClick={() => setChangePasswordOpen(true)}
                        >
                            Change Password
                        </Button>
                    </Box>

                    <Divider />

                    <StandardAccordion title="User Metadata and Status" defaultExpanded={true}>
                        <Box sx={{
                            display: 'flex',
                            flexDirection: {xs: 'column', lg: 'row'},
                            gap: 2
                        }}>
                            <Box sx={{flex: 1}}>
                                <Box display="flex" flexDirection="row" gap={1} justifyItems={"baseline"}>
                                    <Typography width={labelWidth} variant={"h6"}>Name</Typography>

                                    <Typography component={"span"} variant={"body1"} alignContent={"center"}>
                                        <UserNameField/>
                                        <IconButton onClick={() => setChangeUserNameOpen(true)}>
                                            <EditIcon/>
                                        </IconButton>
                                    </Typography>
                                    <UserNameDialog
                                        open={changeUserNameOpen}
                                        setOpen={setChangeUserNameOpen}
                                        onUpdated={handleUserNameChanged}
                                    />
                                </Box>

                                <Box display="flex" flexDirection="column" mt={"2rem"}>
                                    <Box display="flex" flexDirection="row" gap={1} alignItems="center">
                                        <Typography width={labelWidth} variant={"h6"}>Email</Typography>
                                        <EmailField source="email" fontSize={"large"}/>
                                        <IconButton onClick={() => setChangeEmailOpen(true)} size="small">
                                            <EditIcon/>
                                        </IconButton>
                                        <ChangeEmailDialog
                                            open={changeEmailOpen}
                                            setOpen={setChangeEmailOpen}
                                            onEmailChanged={handleEmailChanged}
                                        />
                                    </Box>

                                    <Box display="flex" flexDirection="row" ml={2} gap={2}>
                                        <EmailVerificationSwitch onUpdateEmailVerified={updateEmailVerified}/>
                                        <BooleanInput source="email_bouncing" label={"Email bouncing"}
                                                      helperText={false}
                                                      options={{size: "small"}}/>
                                    </Box>
                                </Box>

                                <Box display="flex" flexDirection="column" mt={"2rem"}>
                                    <Typography variant={"h6"}>Roles and Status</Typography>

                                    <Box display="flex" flexDirection="row" gap={2} alignItems="center">
                                        <Typography variant="body2" sx={{minWidth: '100px'}}>Veto Status:</Typography>
                                        <VetoStatusField source="veto_status"/>
                                        <IconButton
                                            onClick={() => setVetoStatusOpen(true)}
                                        >
                                            <EditIcon/>
                                        </IconButton>
                                    </Box>


                                    <Table size="small" padding={"normal"} >
                                        {
                                            buhchOfInputs.map((inputs) => (
                                                <TableRow key={inputs[0]?.source} sx={{border: 'none'}}>
                                                    {
                                                        inputs.map((input) => (
                                                            <TableCell sx={{border: 'none'}}>
                                                                {
                                                                    input === null ? null :
                                                                        input.component === "FlaggedToggle" ? (
                                                                            <FlaggedToggle
                                                                                source={input.source}
                                                                                label={input.label}
                                                                                helperText={false}
                                                                                sx={switchProps}
                                                                                size="small"
                                                                                disabled={input?.disabled}
                                                                            />
                                                                        ) : (
                                                                            <BooleanInput source={input.source}
                                                                                          label={input.label}
                                                                                          helperText={false}
                                                                                          sx={switchProps}
                                                                                          size="small"
                                                                                          disabled={input?.disabled}
                                                                            />
                                                                        )
                                                                }
                                                            </TableCell>

                                                        ))
                                                    }
                                                </TableRow>
                                            ))
                                        }
                                    </Table>
                                </Box>

                            </Box>

                            <Box sx={{
                                width: {xs: '100%', lg: '400px'},
                                flexShrink: 0
                            }}>
                                <UserDemographic/>
                            </Box>
                        </Box>

                    </StandardAccordion>

                    <Divider />

                    <StandardAccordion title="Moderation, Submission and Endorsement Categories">

                        <Box>
                            <Typography variant={"h6"}>Moderates: </Typography>
                            <IconButton onClick={() => setIsModOpen(true)}>
                                <EditIcon />
                            </IconButton>

                            <UserModerationCategories open={isModOpen} setOpen={setIsModOpen}/>
                        </Box>

                        <Box mt={2}>
                            <Typography variant={"h6"}>Can Submit to: </Typography>
                            <Button size={"small"} variant={"contained"} onClick={() => setCanSubmitToOpen(true)}>
                                Can Submit to?
                            </Button>
                            <CanSubmitToDialog open={canSubmitToOpen} setOpen={setCanSubmitToOpen}/>
                        </Box>

                        <Box mt={2}>
                            <Typography variant={"h6"}>Is endorsed for: </Typography>
                            <IconButton
                                onClick={() => setIsEndorsementsOpen(true)}><EditIcon /></IconButton>
                            <UserEndorsements open={isEndorsementsOpen} setOpen={setIsEndorsementsOpen}/>
                        </Box>

                        <Box mt={2}>
                            <Typography variant={"h6"}>Endorses: </Typography>
                            {
                                /*
                            <Button size={"small"} variant={"contained"} onClick={() => setCanEndorseForOpen(true)} >
                                Can Endorsed for?</Button>
                            <CanEndorseForDialog open={canEndorseForOpen} setOpen={setCanEndorseForOpen}/>

                                 */
                            }
                            <ReferenceField reference={"can-endorse-for"} source={"id"} >
                                <EndorsementCategoriesField source="data" emptyText={"None"}/>
                            </ReferenceField>

                        </Box>

                        <Box mt={2}>
                            <Typography variant={"h6"}>Endorsement Requests</Typography>
                            <EndorsementRequestListField source={"id"}/>
                        </Box>

                    </StandardAccordion>

                    <Divider />

                    <LazyAccordion title="Submissions" summary={usersSubSummary}>
                        <Paper>
                            <UserSubmissionList/>
                        </Paper>
                    </LazyAccordion>

                    <Divider />

                    <LazyAccordion title="Owned Papers" summary={usersOwnershipSummary}>
                        <Paper>
                            <OwnedPaperList/>
                        </Paper>
                    </LazyAccordion>

                    <Divider />

                    <StandardAccordion title="User Activity">
                        <Typography variant={"h6"}>Audit Logs</Typography>
                        <Paper>
                            <AdminAuditList/>
                        </Paper>
                        <Typography variant={"h6"}>Email History</Typography>
                        <Paper>
                            <EmailHistoryList/>
                        </Paper>
                    </StandardAccordion>

                </Box>

            </SimpleForm>
            <UserFlagDialog
                open={addCommentOpen} setOpen={setAddCommentOpen} flagOptions={[]}
                title={"Add comment"} initialFlag={undefined} onUpdated={handleFCommentAdded}
            />
            <UserFlagDialog
                open={vetoStatusOpen} setOpen={setVetoStatusOpen}
                title={"Change Veto Status"} onUpdated={handleVetoStatusChanged}
                vetoStatusMode={true} vetoStatusChoices={vetoStatusChoices}
            />
            <BulkPaperOwnerDialog
                open={bulkPaperOwnerOpen}
                setOpen={setBulkPaperOwnerOpen}
                userId={Number(record?.id) || 0}
                userRecord={record}
            />
            <ChangePasswordDialog
                open={changePasswordOpen}
                setOpen={setChangePasswordOpen}
                onPasswordChanged={handlePasswordChanged}
            />
        </>
    )
};

export const UserEdit = () => {
    return (
        <Box maxWidth={"lg"} ml={"10%"} width={"80%"}>
            <Edit actions={false} redirect={false} component={"div"}>
                <UserEditContent/>
            </Edit>
        </Box>
    )
};

/*
export const UserCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceInput source="username" reference="users"/>
            <TextInput source="first_name"/>
            <TextInput source="last_name"/>
            <TextInput source="email"/>
            <BooleanInput source="flag_email_verified" label={"Email verified"}/>
            <BooleanInput source="flag_edit_users" label={"Admin"}/>
            <BooleanInput source="email_bouncing" label={"Email bouncing"}/>
            <BooleanInput source="flad_banned" label={"Banned"}/>
        </SimpleForm>
    </Create>
);
*/
