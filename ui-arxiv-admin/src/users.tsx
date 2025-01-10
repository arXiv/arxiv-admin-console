import {
    useMediaQuery,
    ToggleButton,
    ToggleButtonGroup,
    Grid,
    Table,
    TableRow,
    TableCell,
    TableHead, Box, Button
} from '@mui/material';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    BooleanField,
    SortPayload,
    useRecordContext,
    useEditContext,
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
    useDataProvider, IconButtonWithTooltip, useListContext, useRedirect
} from 'react-admin';

import DoDisturbOnIcon from '@mui/icons-material/DoDisturbOn';
import React, {useEffect, useState} from "react";
import CategoryField from "./bits/CategoryField";
import PersonNameField from "./bits/PersonNameField";
import CareereStatusField from "./bits/CareereStatusField";
import LastLoginField from "./bits/LastLoginField";

const UserFilter = (props: any) => (
    <Filter {...props}>
        <BooleanInput label="Admin" source="flag_edit_users" defaultValue={true} />
        <BooleanInput label="Mod" source="flag_is_mod"  defaultValue={true} />
        <BooleanInput label="Email verified" source="flag_email_verified" defaultValue={true} />
        <TextInput label="Search by Email" source="email" alwaysOn />
        <TextInput label="Search by First name" source="first_name"/>
        <TextInput label="Search by Last Name" source="last_name"/>
        <BooleanInput label="Email bouncing" source="email_bouncing" defaultValue={true} />
        <BooleanInput label="Suspect" source="suspect" defaultValue={true} />
        <BooleanInput label="Non-academit email" source="is_non_academic" defaultValue={true} />
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
                    <Grid item>
                        <ReferenceField source="id" reference="endorsements" label={""}
                                        link={(record, reference) => `/${reference}/${record.id}`}>
                            <CategoryField source="id" sourceCategory="archive" sourceClass="subject_class"/>
                        </ReferenceField>

                    </Grid>
                </RecordContextProvider>
        );
    }

    return (
        <Grid container item xs={12}>
            <Grid item xs={2}>Endorsed for</Grid>
            {
                endorsements.map((endorsement, index) => (
                    <Grid item xs={2}>
                        <Endorsement endorsement={endorsement} />
                    </Grid>
                ))
            }
        </Grid>);
}


export const UserEdit = () => {
    /*
    const record = useRecordContext();
    const redirect = useRedirect();


    const previousRecordId = currentIndex > 0 ? ids[currentIndex - 1] : null;
    const nextRecordId = currentIndex < ids.length - 1 ? ids[currentIndex + 1] : null;

    const goToPrevious = () => {
        if (previousRecordId) {
            redirect('edit', 'users', previousRecordId);
        }
    };

    const goToNext = () => {
        if (nextRecordId) {
            redirect('edit', 'users', nextRecordId);
        }
    };
    <Box display="flex" justifyContent="space-between" mt={2}>
                <IconButtonWithTooltip onClick={goToPrevious} disabled={currentIndex <= 0} label="Prev"/>
                <Button onClick={goToNext} disabled={currentIndex >= (ids.length - 1) }>Next</Button>
            </Box>
     */

    return (
    <Edit title={<UserTitle />}>
        <SimpleForm>

            <Grid container>
                <Grid item xs={6}>
                    <Table>
                        <TableRow>
                            <TableCell>
                                email
                            </TableCell>
                            <TableCell>
                                <TextInput source="email" />
                                <BooleanInput source="flag_email_verified" label={"Email verified"} />
                                <BooleanInput source="email_bouncing" label={"Email bouncing"} />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                name
                            </TableCell>
                            <TableCell>
                                <TextInput source="first_name" />
                                <TextInput source="last_name" />
                            </TableCell>
                        </TableRow>
                        <TableRow>
                            <TableCell>
                                User name
                            </TableCell>
                            <TableCell>
                                <TextField source="username" />
                            </TableCell>
                        </TableRow>

                        <TableRow>
                            <TableCell>
                                Permissions
                            </TableCell>
                            <TableCell>
                                <Grid container>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_veto_status" label={"Veto status"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_edit_users" label={"Edit Users"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_edit_system" label={"Edit System"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_banned" label={"Suspended"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_proxy" label={"Proxy"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_suspect" label={"Suspect"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_xml" label={"XML"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_group_test" label={"Test"}/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_internal"/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_approved"/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_deleted"/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_allow_tex_produced"/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanInput source="flag_can_lock"/>
                                    </Grid>
                                    <Grid item xs={3}>
                                        <BooleanField source="flag_is_mod"/>
                                    </Grid>
                                </Grid>
                                <SelectInput source="policy_class" choices={policyClassChoices} />
                            </TableCell>
                        </TableRow>
                    </Table>
                </Grid>

                <Grid item xs={6}>
                    <UserDemographic />
                </Grid>
            </Grid>
            <Grid container >
                <Grid item xs={12}>
                    <UserEndorsements />
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


