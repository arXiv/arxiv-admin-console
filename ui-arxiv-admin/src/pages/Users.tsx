import {
    useMediaQuery,
} from '@mui/material';

import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Grid from '@mui/material/Grid';
import Link from '@mui/material/Link';
import Table from '@mui/material/Table';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import Box from '@mui/material/Box';
import Divider from '@mui/material/Divider';
import EmailIcon from '@mui/icons-material/Email';


import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
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
    DeleteButton, Toolbar, useNotify, useEditContext, useRefresh,
    Confirm
} from 'react-admin';

import DoDisturbOnIcon from '@mui/icons-material/DoDisturbOn';
import React, {useContext, useEffect, useState} from "react";
import CategoryField from "../bits/CategoryField";
import PersonNameField from "../bits/PersonNameField";
import CareereStatusField from "../bits/CareereStatusField";
import TapirSessionInfo from "../bits/TapirSessionInfo";
import Typography from "@mui/material/Typography";
import OwnedPaperList from "../bits/OwnedPaperList";
import {AdminAuditList} from "../bits/TapirAdminLogs";
import Button from '@mui/material/Button';
import LoginIcon from '@mui/icons-material/Login';
import SuspendIcon from '@mui/icons-material/Pause';
import {RuntimeContext} from "../RuntimeContext"; // for "Become This User"
import { useLocation, useNavigate } from 'react-router-dom';
import EmailLinkField from "../bits/EmailLinkField";
import ModerationCategoryDialog from "../components/ModerationCategoryDialog";
import EndorsementCategoryDialog from "../components/EndorsementCategoryDialog";

import { paths as adminApi } from '../types/admin-api';
import CanSubmitToDialog from "../components/CanSubmitToDialog";
import CanEndorseForDialog from "../components/CanEndorseForDialog";
import PolicClassField from "../bits/PolicClassField";
import EmailHistoryList from "../bits/EmailHistoryList";
import ChangeEmailDialog from "../components/ChangeEmailDialog";
import ISODateField from "../bits/ISODateFiled";

type ModeratorT = adminApi['/v1/moderators/']['get']['responses']['200']['content']['application/json'][0];
type EndorsementT = adminApi['/v1/endorsements/']['get']['responses']['200']['content']['application/json'][0];


const UserFilter = (props: any) => (
    <Filter {...props}>
        <BooleanInput label="Admin" source="flag_edit_users" defaultValue={true} />
        <BooleanInput label="Mod" source="flag_is_mod"  defaultValue={true} />
        <TextInput label="Search by Email" source="email" alwaysOn />
        <TextInput label="Login name" source="username" />
        <TextInput label="Search by First name" source="first_name"/>
        <TextInput label="Search by Last Name" source="last_name"/>
        <BooleanInput label="Email bouncing" source="email_bouncing" defaultValue={true} />
        <BooleanInput label="Suspect" source="suspect" defaultValue={true} />
        <BooleanInput label="Non-academit email" source="is_non_academic" defaultValue={true} />
        <BooleanInput label="Email verified" source="flag_email_verified" defaultValue={true} />
        <DateInput label="Start joined date" source="start_joined_date" />
        <DateInput label="End joined date" source="end_joined_date" />
    </Filter>
);

// export default UserFilter;

interface VisibleColumns {
    email: boolean,
    joinedDate:boolean,
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
                    navigate(newUrl, { replace: true });
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
        <List filters={<UserFilter/>}>
            <Datagrid rowClick="edit" bulkActionButtons={false}>
                <TextField source={"id"} label="ID" />
                <PersonNameField source={"last_name"} label="Name" />
                <TextField source="username" label={"Login name"}/>
                <EmailField source="email"/>
                <ISODateField source="joined_date"/>
                <BooleanField source="flag_edit_users" label={"Admin"} FalseIcon={null}/>
                <BooleanField source="flag_is_mod" label={"Mod"} FalseIcon={null}/>
                <BooleanField source="flag_banned" label={"Suspended"} FalseIcon={null}
                              TrueIcon={DoDisturbOnIcon} />
                <BooleanField source="flag_suspect" label={"Suspect"} FalseIcon={null}
                              TrueIcon={DoDisturbOnIcon}/>
                <ReferenceField source="moderator_id" reference="moderators"
                                link={(record, reference) => `/${reference}/${record.moderator_id}`} >
                    <TextField source={"archive"} />
                    {"/"}
                    <TextField source={"subject_class"} />
                </ReferenceField>
            </Datagrid>
        </List>
    );
};

const UserTitle = () => {
    const record = useRecordContext();
    return <span>User {record ? `"${record.last_name}, ${record.first_name}" - ${record.email}` : ''}</span>;
};

const policyClassChoices = [
    { id: 0, name: 'Owner' },
    { id: 1, name: 'Admin' },
    { id: 2, name: 'Public user' },
    { id: 3, name: 'Legacy user' },
];

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
                        filter: { user_id: record.id },
                        sort: { field: "id", order: "DESC" },
                        pagination: { page: 1, perPage: 2 }, // Only get the latest two
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
    <Table size="small" >
        <TableHead>
            <TableCell width={"25%"} sx={{minWidth: "120px"}}>
                Property
            </TableCell>
            <TableCell>
                Values
            </TableCell>

        </TableHead>
        <TableRow>
            <TableCell>
                User ID
            </TableCell>
            <TableCell>
                <TextField source="id" />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>
                Login name
            </TableCell>
            <TableCell>
                <TextField source="username" />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>
                Policy class
            </TableCell>
            <TableCell>
                <PolicClassField source="policy_class" />
            </TableCell>
        </TableRow>


        <TableRow>
            <TableCell>
                Last login
            </TableCell>
            <TableCell>
                <TapirSessionInfo source={"id"} index={0} isLoading={isLoading} total={totalTapirSessions} tapirSessions={tapirSessions} />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>Penultimate Login</TableCell>
            <TableCell>
                <TapirSessionInfo source={"id"} index={1} isLoading={isLoading} total={totalTapirSessions} tapirSessions={tapirSessions} />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>Total sessions</TableCell>
            <TableCell>
                <TapirSessionInfo source={"id"} index={-1} isLoading={isLoading} total={totalTapirSessions} tapirSessions={tapirSessions} />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>Joined Date</TableCell>
            <TableCell>
                <ISODateField source="joined_date" />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>Joined From</TableCell>
            <TableCell>
                <TextField source="joined_ip_num" />
            </TableCell>
        </TableRow>


        <TableRow>
            <TableCell>Affiliation</TableCell>
            <TableCell>
                <TextField source="affiliation" />
            </TableCell>
        </TableRow>
        <TableRow>
            <TableCell>Country</TableCell>
            <TableCell>
                <TextField source="country" />
            </TableCell>
        </TableRow>
        <TableRow>
            <TableCell>URL</TableCell>
            <TableCell>
                <TextField source="url" />
            </TableCell>
        </TableRow>
        <TableRow>
            <TableCell>Default Category</TableCell>
            <TableCell>
                <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" />
            </TableCell>
        </TableRow>

        <TableRow>
            <TableCell>Career Status</TableCell>
            <TableCell>
                <CareereStatusField source="type" />
            </TableCell>
        </TableRow>
        <TableRow>
            <TableCell>arXiv Author ID</TableCell>
            <TableCell>
                <ReferenceField reference={"author_ids"} source={"id"} >
                    <TextField source="author_id" emptyText={"No author ID"} />
                </ReferenceField>
            </TableCell>
        </TableRow>
        <TableRow>
            <TableCell>ORCID</TableCell>
            <TableCell>
                <ReferenceField reference={"orcid_ids"} source={"id"} >
                    <TextField source="orcid" emptyText={"No ORCID"} />
                </ReferenceField>
            </TableCell>
        </TableRow>

    </Table>);
}


function UserEndorsements({open, setOpen} : {open: boolean, setOpen: (open: boolean) => void}) {
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

    function Endorsement({domain}: {domain: EndorsementT}) {
        return (
                <RecordContextProvider value={domain} >
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
                        <Endorsement key={`${endorsement.id}`} domain={endorsement} />
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


function UserModerationCategories({open, setOpen} : {open: boolean, setOpen: (open: boolean) => void}) {
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

    function ModerationCategory({domain}: {domain: ModeratorT}) {
        return (
            <RecordContextProvider value={domain} >
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
                    <ModerationCategory key={`${domain.id}`} domain={domain} />
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


const UserEditToolbar = () => {
    const notify = useNotify();
    const record = useRecordContext();
    const runtimeProps = useContext(RuntimeContext);

    const handleBan = async () => {
        if (!record?.id) return;

    }

    const handleMasquerade = async () => {
        if (!record?.id) return;

        console.log( "aaa: " + runtimeProps.AAA_URL);

        try {
            const response = await fetch(`${runtimeProps.AAA_URL}/impersonate/${record.id}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include', // send cookies if needed
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

            notify('Switched to user session', { type: 'info' });
            window.location.href = '/'; // Or wherever you want to redirect
        } catch (error: unknown) {
            let message = 'Unknown error';
            if (error instanceof Error) {
                message = error.message;
            }
            notify(`Masquerade failed: ${message}`, { type: 'error' });
        }
    };

    return (
        <Toolbar sx={{gap: 1}}>
            <SaveButton />
            <Button
                variant="contained"
                color="secondary"
                startIcon={<LoginIcon />}
                onClick={handleMasquerade}
                sx={{ ml: 2 }}
            >
                Become This User
            </Button>
            <Box sx={{ flexGrow: 1 }} />
            <Button
                variant="contained"
                color="secondary"
                startIcon={<SuspendIcon />}
                onClick={handleBan}
                sx={{ ml: 2 }}
            >
                Suspend
            </Button>
            <DeleteButton />
        </Toolbar>
    );
};

type statusInputType = {source: string, label: string, disabled?: boolean} | null;

export const UserEdit = () => {
    const [isEndorsementsOpen, setIsEndorsementsOpen] = useState(false);
    const [isModOpen, setIsModOpen] = useState(false);
    const [canEndorseForOpen, setCanEndorseForOpen] = useState(false);
    const [canSubmitToOpen, setCanSubmitToOpen] = useState(false);
    const [changeEmailOpen, setChangeEmailOpen] = useState(false);
    const refresh = useRefresh(); // Import this from react-admin

    const switchProps = {
        '& .MuiSwitch-root': {
            transform: 'scale(0.7)', // smaller than small
        },
        flex: 4,
        size: "small",
    };

    const statusInputs: statusInputType[][] = [
        [
            {source: "flag_banned", label: "Banned", disabled: true},
            {source: "flag_deleted", label: "Deleted", disabled: true},
            {source: "flag_suspect", label: "Suspect"},
        ],
        [
            {source: "flag_approved", label: "Approved"},
            {source: "flag_veto_status", label: "Veto status"},
            {source: "flag_proxy", label: "Proxy"},
            ],
        [
            {source: "flag_xml", label: "XML"},
            {source: "flag_allow_tex_produced", label: "Allow Tex"},
            null,
        ]
    ];

    const adminInputs: statusInputType[][] = [
        [
            {source: "flag_edit_users", label: "Edit Users"},
            {source: "flag_edit_system", label: "Edit System"},
            {source: "flag_group_test", label: "Test"},
        ],
        [
            {source: "flag_internal", label: "Internal"},
            {source: "flag_can_lock", label: "Can Lock"},
            null,
        ],
    ];

    const handleEmailChanged = (newEmail: string) => {
        refresh(); // Refresh the form to show the updated email
    };


    return (
    <Edit title={<UserTitle />} actions={false}>
        <SimpleForm toolbar={<UserEditToolbar />}>
            <Grid container>
                <Grid size={{xs: 6}} >
                    <Box display="flex" flexDirection="row" gap={2} justifyItems={"normal"}>
                        <Button
                            variant="outlined"
                            size="small"
                            startIcon={<EmailIcon />}
                            onClick={() => setChangeEmailOpen(true)}
                        >
                            Change
                        </Button>
                        <EmailField source="email"  fontSize={"large"} />
                            <ChangeEmailDialog
                                open={changeEmailOpen}
                                setOpen={setChangeEmailOpen}
                                onEmailChanged={handleEmailChanged}
                            />

                    </Box>
                    <Box display="flex" flexDirection="row" gap={2} justifyItems={"normal"}>
                        <BooleanInput source="flag_email_verified" label={"Email verified"} helperText={false} options={{size: "small"}} />
                        <BooleanInput source="email_bouncing" label={"Email bouncing"} helperText={false} options={{size: "small"}}  />
                    </Box>
                    <Divider />

                    <Box display="flex" flexDirection="row" gap={1} justifyItems={"baseline"}>
                        <TextInput source="first_name" helperText={false} />
                        <TextInput source="last_name" helperText={false}  />
                        <TextInput source="suffix_name" helperText={false} sx={{maxWidth: "6em"}} />
                    </Box>
                    <Divider />

                    <Table size="small">
                        {
                            statusInputs.map((inputs) => (
                                <TableRow>
                                    {
                                        inputs.map((input) => (
                                            <TableCell>
                                                {
                                                    input === null ? null :
                                                        (<BooleanInput source={input.source} label={input.label}
                                                                       helperText={false} sx={switchProps} size="small"
                                                                       disabled={input?.disabled}
                                                        />)

                                                }
                                            </TableCell>

                                        ))
                                    }
                                </TableRow>
                            ))
                        }

                        {
                            adminInputs.map((inputs) => (
                                <TableRow>
                                    {
                                        inputs.map((input) => (
                                            <TableCell>
                                                {
                                                    input === null ? null :
                                                        (<BooleanInput source={input.source} label={input.label}
                                                                      helperText={false} sx={switchProps} size="small" />)

                                                }
                                            </TableCell>

                                        ))
                                    }
                                </TableRow>
                            ))
                        }
                    </Table>

                    <Box >
                        <Button onClick={() => setIsEndorsementsOpen(true)}> Endorsed for </Button>
                        <UserEndorsements open={isEndorsementsOpen} setOpen={setIsEndorsementsOpen} />
                    </Box>
                    <Divider />
                    <Box >
                        <Button onClick={() => setIsModOpen(true)}>Moderator for</Button>
                        <UserModerationCategories  open={isModOpen} setOpen={setIsModOpen} />
                    </Box>
                    <Divider />
                    <Box>
                        <Button variant={"contained"} onClick={() => setCanSubmitToOpen(true)}>Can Submit to?</Button>
                        <Button variant={"contained"} onClick={() => setCanEndorseForOpen(true)} sx={{ml: 2}}>Can Endorsed for?</Button>
                        <CanSubmitToDialog open={canSubmitToOpen} setOpen={setCanSubmitToOpen} />
                        <CanEndorseForDialog open={canEndorseForOpen} setOpen={setCanEndorseForOpen} />
                    </Box>
                    <Divider />

                    <AdminAuditList />
                </Grid>

                <Grid size={{xs: 6}}>
                    <UserDemographic />
                    <EmailHistoryList />
                    <Grid size={{xs: 12}}>
                        <OwnedPaperList />
                    </Grid>
                </Grid>


            </Grid>
        </SimpleForm>
    </Edit>
)
};

export const UserCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceInput source="username" reference="users" />
            <TextInput source="first_name" />
            <TextInput source="last_name" />
            <TextInput source="email" />
            <BooleanInput source="flag_email_verified" label={"Email verified"} />
            <BooleanInput source="flag_edit_users" label={"Admin"}/>
            <BooleanInput source="email_bouncing" label={"Email bouncing"} />
            <BooleanInput source="flad_banned" label={"Banned"}/>
        </SimpleForm>
    </Create>
);


