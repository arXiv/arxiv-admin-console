import {
    Divider, IconButton,
    useMediaQuery,
} from '@mui/material';

import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Grid from '@mui/material/Grid2';
import Table from '@mui/material/Table';
import TableRow from '@mui/material/TableRow';
import TableCell from '@mui/material/TableCell';
import TableHead from '@mui/material/TableHead';
import Box from '@mui/material/Box';
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
    DateField,
    ReferenceField,
    SelectInput,
    DateInput,
    RecordContextProvider,
    useDataProvider,
    SaveButton,
    DeleteButton, Toolbar, useNotify,
} from 'react-admin';

import DoDisturbOnIcon from '@mui/icons-material/DoDisturbOn';
import React, {useContext, useEffect, useState} from "react";
import CategoryField from "../bits/CategoryField";
import PersonNameField from "../bits/PersonNameField";
import CareereStatusField from "../bits/CareereStatusField";
import LastLoginField from "../bits/LastLoginField";
import Typography from "@mui/material/Typography";
import PaperOwnersList from "../bits/PaperOwnersList";
import {AdminAuditList} from "../bits/TapirAdminLogs";
import Button from '@mui/material/Button';
import LoginIcon from '@mui/icons-material/Login';
import {RuntimeContext} from "../RuntimeContext"; // for "Become This User"
import { useLocation, useNavigate } from 'react-router-dom';


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
    const sorter: SortPayload = {field: 'user_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    const [visibleColumns, setVisibleColumns] = useState<VisibleColumns>(
        {
            email: true,
            joinedDate: false,
            mod: false,
        }
    );

    const handleToggle = (event: React.MouseEvent<HTMLElement>) => {
        const column = event.currentTarget.getAttribute('value');
        if (column) {
            const isSelected = event.currentTarget.getAttribute('aria-pressed') === 'true';
            setVisibleColumns((prevState) => ({
                ...prevState,
                [column]: !isSelected,
            }));
        }
    };

    const location = useLocation();
    const navigate = useNavigate();

    useEffect(() => {
        const searchParams = new URLSearchParams(location.search);
        const filterParam = searchParams.get('filter');

        if (filterParam) {
            try {
                const parsedFilters = JSON.parse(decodeURIComponent(filterParam));

                // Create new filter object with only email, first_name, and last_name
                const newFilters: any = {};

                if (parsedFilters.email) {
                    newFilters.email = parsedFilters.email;
                }
                if (parsedFilters.first_name) {
                    newFilters.first_name = parsedFilters.first_name;
                }
                if (parsedFilters.last_name) {
                    newFilters.last_name = parsedFilters.last_name;
                }

                // Only update if we have relevant filters
                if (Object.keys(newFilters).length > 0) {
                    // Create new URL with only the relevant filters
                    const newFilterParam = encodeURIComponent(JSON.stringify(newFilters));
                    const newUrl = `${location.pathname}?filter=${newFilterParam}`;

                    // Replace current URL without triggering a page reload
                    navigate(newUrl, { replace: true });
                }
            } catch (error) {
                console.error('Error parsing URL filters:', error);
            }
        }
    }, [location.search, navigate, location.pathname]);


    return (
        <div>
            <ToggleButtonGroup
                aria-label="Column visibility"
                sx={{ marginBottom: '1em' }}
            >
                <ToggleButton
                    value={"email"}
                    selected={visibleColumns.email}
                    onClick={handleToggle}
                    aria-label="Show Email"
                >
                    Email
                </ToggleButton>
                <ToggleButton
                    value={"joinedDate"}
                    onClick={handleToggle}
                    selected={visibleColumns.joinedDate}
                    aria-label="Show Joined Date"
                >
                    Joined Date
                </ToggleButton>
            </ToggleButtonGroup>

                <List filters={<UserFilter/>}>
                {isSmall ? (
                    <SimpleList
                        primaryText={record => record.name}
                        secondaryText={record => record.username}
                        tertiaryText={record => record.email}
                    />
                ) : (

                    <Datagrid rowClick="edit" sort={sorter}>
                        <PersonNameField source={"id"} label="Name" />
                        <TextField source="username" label={"Login name"}/>

                        {
                            visibleColumns.email ? <EmailField source="email"/> : null
                        }
                        {
                            visibleColumns.joinedDate ? <DateField source="joined_date"/> : null
                        }
                        <BooleanField source="flag_edit_users" label={"Admin"} FalseIcon={null}/>
                        <BooleanField source="flag_is_mod" label={"Mod"} FalseIcon={null}/>
                        <BooleanField source="flag_banned" label={"Suspended"} FalseIcon={null}
                                      TrueIcon={DoDisturbOnIcon}/>
                        <BooleanField source="flag_suspect" label={"Suspect"} FalseIcon={null}
                                      TrueIcon={DoDisturbOnIcon}/>
                        <ReferenceField source="moderator_id" reference="moderators"
                                        link={(record, reference) => `/${reference}/${record.moderator_id}`} >
                            <TextField source={"archive"} />
                            {"/"}
                            <TextField source={"subject_class"} />
                        </ReferenceField>

                    </Datagrid>
                )}
            </List>
        </div>
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
    return (
    <Table>
        <TableHead>
            <TableCell>
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
                Last login
            </TableCell>
            <TableCell>
                <LastLoginField source={"id"} />
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


function UserEndorsements() {
    const record = useRecordContext<any>();
    const [endorsements, setEndorsements] = useState<any[]>([]);
    const dataProvider = useDataProvider();

    useEffect(() => {
        const fetchEndorsements = async (userId: number) => {
            try {
                const response = await dataProvider.getList('endorsements', {
                    filter: {endorsee_id: userId}, sort: {field: 'archive,subject_class', order: 'ASC'},
                });
                setEndorsements(response.data);
            } catch (error) {
                console.error("Error fetching endorsements data:", error);
            }
        };

        if (record)
            fetchEndorsements(record.id);
    }, [dataProvider, record]);

    function Endorsement(props: any) {
        return (
                <RecordContextProvider value={props.endorsement} >
                    <Grid>
                        <ReferenceField source="id" reference="endorsements" label={""}
                                        link={(record, reference) => `/${reference}/${record.id}`}>
                            <CategoryField source="id" sourceCategory="archive" sourceClass="subject_class" renderAs={"chip"}/>
                        </ReferenceField>
                    </Grid>
                </RecordContextProvider>
        );
    }

    return (
        <Grid container size={{xs: 12}}>
            <Grid size={{xs: 2}}>Endorsed for</Grid>
            {
                endorsements.map((endorsement, _index) => (
                    <Grid size={{xs: 2}}>
                        <Endorsement endorsement={endorsement} />
                    </Grid>
                ))
            }
        </Grid>
    );
}


const UserEditToolbar = () => {
    const notify = useNotify();
    const record = useRecordContext();
    const runtimeProps = useContext(RuntimeContext);


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
            <DeleteButton />
        </Toolbar>
    );
};


export const UserEdit = () => {
    const switchProps = {
        '& .MuiSwitch-root': {
            transform: 'scale(0.7)', // smaller than small
        },
        flex: 4,
        size: "small",
    };

    const statusInputs = [
        [
            {source: "flag_banned", label: "Suspended"},
            {source: "flag_deleted", label: "Deleted"},
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

    const adminInputs = [
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


    return (
    <Edit title={<UserTitle />} actions={false}>
        <SimpleForm toolbar={<UserEditToolbar />}>
            <Grid container>
                <Grid size={{xs: 6}} >
                    <Box display="flex" flexDirection="row" gap={1} justifyItems={"baseline"}>
                        <TextInput source="email" helperText={false} />
                        <IconButton  color="primary" aria-label="send email" onClick={() => {}} >
                            <EmailIcon />
                        </IconButton>
                        <BooleanInput source="flag_email_verified" label={"Email verified"} helperText={false} options={{size: "small"}} />
                        <BooleanInput source="email_bouncing" label={"Email bouncing"} helperText={false} options={{size: "small"}} />
                    </Box>

                    <Table size="small">
                        <TableRow>
                            <TableCell>
                                <TextInput source="first_name" helperText={false} />
                            </TableCell>
                            <TableCell>
                                <TextInput source="last_name" helperText={false}  />
                            </TableCell>
                            <TableCell>
                                <TextInput source="suffix_name" helperText={false}  />
                            </TableCell>
                        </TableRow>
                    </Table>

                    <Table size="small">
                        <TableRow>
                            <TableCell>
                                <Typography component={"span"} >Login: </Typography>
                                <TextField source="username" fontFamily={"monospace"} />
                            </TableCell>
                        </TableRow>
                    </Table>

                    <Table size="small">
                        <TableRow>
                            <TableCell />
                            <TableCell>
                                <SelectInput source="policy_class" choices={policyClassChoices} helperText={false} />
                            </TableCell>
                            <TableCell>
                            <Grid size={{xs: 3}} >
                                <Typography component={"span"} >Moderator
                                    <BooleanField source="flag_is_mod" label={"Moderator"} />
                                </Typography>
                            </Grid>
                            </TableCell>

                        </TableRow>
                    </Table>

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
                                                                       helperText={false} sx={switchProps} size="small" />)

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

                    <UserEndorsements />

                    <Divider />

                    <AdminAuditList />
                </Grid>

                <Grid size={{xs: 6}}>
                    <UserDemographic />
                    <Grid size={{xs: 12}}>
                        <PaperOwnersList />
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


