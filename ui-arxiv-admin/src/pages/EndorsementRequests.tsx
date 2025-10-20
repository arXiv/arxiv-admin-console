import React, {useState, useEffect} from 'react';

import {
    useDataProvider,
    List,
    Datagrid,
    TextField,
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
    useListContext,
    ReferenceField,
    Show,
    SimpleShowLayout, useGetOne, RecordContextProvider, Identifier,
    Toolbar,
    SaveButton,
    useNotify,
    useRefresh,
    useUnselectAll,
} from 'react-admin';

import Box from "@mui/material/Box";
import Paper from "@mui/material/Paper";
import Table from "@mui/material/Table";
import TableRow from "@mui/material/TableRow";
import TableCell from "@mui/material/TableCell";
import Button from "@mui/material/Button";
import LinearProgress from "@mui/material/LinearProgress";
import Typography from "@mui/material/Typography";
import ConsoleTitle from "../bits/ConsoleTitle";

import BooleanField from "../bits/BooleanNumberField";
import CategoryField from "../bits/CategoryField";

import PointValueBooleanField from "../bits/PointValueBooleanField";
import ISODateField from "../bits/ISODateFiled";
import UserNameField from "../bits/UserNameField";
import Card from '@mui/material/Card';
import CardHeader from '@mui/material/CardHeader';
import CardContent from "@mui/material/CardContent";
import {DottedLineRow} from "../components/DottedLineRow";

interface Category {
    id: string;
    name: string;
    description: string;
}

interface CategorySubject {
    id: string;
    name: string;
    description: string;
}

const presetOptions = [
    { id: 'last_1_day', name: 'Last 1 Day' },
    { id: 'last_7_days', name: 'Last 7 Days' },
    { id: 'last_28_days', name: 'Last 28 Days' },
];

const EndorsementRequestBulkActionButtons = () => {
    const listContext = useListContext();
    const notify = useNotify();
    const refresh = useRefresh();
    const unselectAll = useUnselectAll('endorsement_requests');
    const dataProvider = useDataProvider();
    const [isUpdating, setIsUpdating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentAction, setCurrentAction] = useState('');

    const handleBulkUpdate = async (
        actionName: string,
        updateData: Record<string, any>,
        previousData?: Record<string, any>
    ) => {
        const selectedIds = listContext.selectedIds;
        console.log(`${actionName} - Selected IDs:`, selectedIds);
        
        if (selectedIds.length === 0) {
            notify("No endorsement requests selected", { type: 'warning' });
            return;
        }

        setIsUpdating(true);
        setCurrentAction(`Marking as ${actionName.toLowerCase()}`);
        setProgress(0);

        const successes: string[] = [];
        const errors: string[] = [];
        const total = selectedIds.length;
        
        for (let i = 0; i < selectedIds.length; i++) {
            const id = selectedIds[i];
            try {
                await dataProvider.update('endorsement_requests', {
                    id: id,
                    data: updateData,
                    previousData: previousData || {},
                });
                successes.push(id);
            } catch (error) {
                errors.push(id);
            }
            
            // Update progress
            const completed = i + 1;
            const progressPercent = Math.round((completed / total) * 100);
            setProgress(progressPercent);
        }
        
        // Show final results
        if (successes.length > 0) {
            notify(`Marked ${successes.length} endorsement requests as ${actionName.toLowerCase()}`, { type: 'info' });
        }
        if (errors.length > 0) {
            notify(`Failed to mark ${errors.length} endorsement requests as ${actionName.toLowerCase()}`, { type: 'warning' });
        }
        
        // Clean up
        setIsUpdating(false);
        setProgress(0);
        setCurrentAction('');
        unselectAll();
        refresh();
    };

    const handleMarkValid = () => handleBulkUpdate(
        'Valid',
        { flag_valid: true },
        { flag_valid: false }
    );

    const handleMarkInvalid = () => handleBulkUpdate(
        'Invalid',
        { flag_valid: false },
        { flag_valid: true }
    );

    const handleMarkOpen = () => handleBulkUpdate(
        'Open',
        { flag_open: true },
        { flag_open: false }
    );

    const handleMarkClosed = () => handleBulkUpdate(
        'Closed',
        { flag_open: false },
        { flag_open: true }
    );

    return (
        <Box display="flex" flexDirection="column" sx={{ gap: 1, m: 1 }}>
            {/* Progress Indicator */}
            {isUpdating && (
                <Box sx={{ width: '100%', mb: 2 }}>
                    <Box display="flex" alignItems="center" sx={{ mb: 1 }}>
                        <Typography variant="body2" sx={{ mr: 1 }}>
                            {currentAction}... ({progress}%)
                        </Typography>
                    </Box>
                    <LinearProgress 
                        variant="determinate" 
                        value={progress} 
                        sx={{ height: 6, borderRadius: 3 }}
                    />
                </Box>
            )}
            
            {/* Action Buttons */}
            <Box display="flex" flexDirection="row" sx={{ gap: 1 }}>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleMarkValid}
                    disabled={isUpdating}
                >
                    Mark Valid
                </Button>
                <Button
                    variant="contained"
                    color="secondary"
                    onClick={handleMarkInvalid}
                    disabled={isUpdating}
                >
                    Mark Invalid
                </Button>
                <Button
                    variant="contained"
                    color="primary"
                    onClick={handleMarkOpen}
                    disabled={isUpdating}
                >
                    Mark Open
                </Button>
                <Button
                    variant="contained"
                    color="secondary"
                    onClick={handleMarkClosed}
                    disabled={isUpdating}
                >
                    Mark Closed
                </Button>
            </Box>
        </Box>
    );
};

const EndorsementRequestFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const preset = event.target.value;
        setFilters({
            ...filterValues,
            preset: preset,
        });
    };

    return (
        <Filter {...props}>
            <TextInput label="First Name" source="endorsee_first_name" alwaysOn />
            <TextInput label="Last Name" source="endorsee_last_name" alwaysOn />
            <TextInput label="Email Address" source="endorsee_email" alwaysOn />
            <TextInput label="Username" source="endorsee_username"/>
            <TextInput label="Category" source="category"  />

            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <BooleanInput label="Closed" source="positive" />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" defaultValue="true"/>
            <BooleanInput label="Suspect" source="suspected" defaultValue="false"/>
            <TextInput label="Secret" source="secret" />

        </Filter>
    );
};


export const EndorsementRequestList = () => {
    const sorter: SortPayload = {field: 'endorsementRequest_id', order: 'DESC'};
    return (
        <Box maxWidth={"xl"} sx={{ margin: '0 auto'}}>
            <ConsoleTitle>Endorsement Requests</ConsoleTitle>
            <List filters={<EndorsementRequestFilter />}
              filterDefaultValues={{positive: false}}
              sort={sorter}
              >
            <Datagrid rowClick="edit" bulkActionButtons={<EndorsementRequestBulkActionButtons />}>
                <NumberField source="id" label={"ID"}/>
                <ReferenceField source="endorsee_id" reference="users"
                                link={(record, reference) => `/${reference}/${record.id}`} >
                    <UserNameField withEmail withUsername />
                </ReferenceField>

                <CategoryField label={"Category"} source="archive" sourceCategory="archive" sourceClass="subject_class" />
                <ISODateField source="issued_when" label={"Issued"}/>

                <TextField source={"secret"} />

                <ReferenceField source="id" reference="endorsement_requests_audit" label={"Remote IP"}>
                    <TextField source={"remote_addr"} label={"Remote IP"}/>
                </ReferenceField>
                <ReferenceField source="id" reference="endorsement_requests_audit" label={"Remote host"}>
                    <TextField source={"remote_host"} label={"Remote host"}/>
                </ReferenceField>
                <BooleanField source="flag_valid" label={"Valid"} FalseIcon={null} />
                <PointValueBooleanField source="point_value" label={"Open"} />
            </Datagrid>
        </List>
        </Box>
    );
};


const EndorsementRequestTitle = () => {
    const record = useRecordContext();

    // Fetch the user data based on user_id from the record
    const { data: user, isLoading } = useGetOne('users', { id: record?.endorsee_id });

    if (!record) {
        return <span>Endorsement Request - no record</span>;
    }

    if (isLoading) {
        return <span>Endorsement Request - Loading endorsee...</span>;
    }

    return (
        <span>
            Endorsement Request: {user ? `${user.first_name} ${user.last_name} in ${record.archive}.${record.subject_class || "*"}` : ''}
        </span>
    );
};


export const ShowDemographic = () => {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [demographic, setDemographic] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchDemographic = async () => {
            if (record) {
                console.log("fetchDemo " + JSON.stringify(record));
                const userId = record.endorsee_id;
                try {
                    const response = await dataProvider.getOne('demographics', {id: userId});
                    setDemographic(response.data);
                    setLoading(false);
                } catch (error) {
                    console.error("Error fetching demographic data:", error);
                    setLoading(false);
                }
            }
        };

        fetchDemographic();
    }, [dataProvider, record]);


    return (
        <Card sx={{backgroundColor: '#1c1a17', borderRadius: '16px', mb: 2}}>
            <CardHeader
                title="Demographic"
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
                    <DottedLineRow label="Session ID">
                        <ReferenceField source={"id"} reference="endorsement_requests_audit" link={(record, reference) => `/tapir_sessions/${record.id}/edit`}>
                            <TextField source={"session_id"}/>
                        </ReferenceField>
                    </DottedLineRow>

                    <DottedLineRow label="Session Start/End">
                        <ReferenceField source={"id"} reference="endorsement_requests_audit" >
                            <ReferenceField source={"id"} reference="tapir_sessions">
                                <ISODateField source={"start_time"} showTime />
                            </ReferenceField>
                        </ReferenceField>
                        <ReferenceField source={"id"} reference="endorsement_requests_audit" >
                            <ReferenceField source={"id"} reference="tapir_sessions">
                                <ISODateField source={"end_time"} showTime />
                            </ReferenceField>
                        </ReferenceField>
                    </DottedLineRow>

                    <DottedLineRow label="Remote Hostname">
                        <ReferenceField source={"id"} reference="endorsement_requests_audit">
                            <TextField source={"remote_host"}/>
                        </ReferenceField>
                    </DottedLineRow>

                    <DottedLineRow label="Remote Address">
                        <ReferenceField source={"id"} reference="endorsement_requests_audit">
                            <TextField source={"remote_addr"}/>
                        </ReferenceField>
                    </DottedLineRow>

                    <DottedLineRow label="Endorsement Code">
                        <TextField source={"secret"}/>
                    </DottedLineRow>

                    <RecordContextProvider value={demographic}>
                        <DottedLineRow label="Affiliation">
                            <TextField source={"affiliation"}/>
                        </DottedLineRow>

                        <DottedLineRow label="Country">
                            <TextField source={"country"}/>
                        </DottedLineRow>

                        <DottedLineRow label="URL">
                            <TextField source={"url"}/>
                        </DottedLineRow>
                    </RecordContextProvider>
                </Box>
            </CardContent>
        </Card>
    );
}


export const ListEndorsements = () => {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [endorsements, setEndorsements] = useState<any[] | undefined>(undefined);
    const [loadingEndorsements, setLoadingEndorsements] = useState(true);

    useEffect(() => {
        const fetchEndorsements = async (requestId: Identifier) => {
            try {
                const response = await dataProvider.getList('endorsements',
                    {
                        filter: {request_id: requestId, _start: 0, _end: 10},
                    });
                const data = response.data;
                setEndorsements(data);
                setLoadingEndorsements(false);
            } catch (error) {
                console.error("Error fetching demographic data:", error);
                setLoadingEndorsements(false);
            }
        };

        if (record) {
            console.log(JSON.stringify(record));
            fetchEndorsements(record.id);
        }
    }, [dataProvider, record]);

    const Endorsement = (endorsement: any) => {
        return (
            <RecordContextProvider value={endorsement.endorsement}>
                <TableRow>
                    <TableCell>
                        <ReferenceField reference={"endorsements"} source={"id"}
                                        link={(record, reference) => `/${reference}/${record.id}`} >
                            <NumberField source={"id"} />
                        </ReferenceField>
                    </TableCell>
                    <TableCell><CategoryField sourceCategory={"archive"} sourceClass={"subject_class"} source={"archive"} /> </TableCell>
                    <TableCell>
                        <ReferenceField reference={"users"} source={"endorser_id"}
                            link={(record, reference) => `/${reference}/${record.id}`} >
                            <TextField source={"last_name"} fontStyle={{fontSize: '1rem'}} />
                            {", "}
                            <TextField source={"first_name"} fontStyle={{fontSize: '1rem'}} />

                        </ReferenceField>
                    </TableCell>
                    <TableCell>
                        <ReferenceField reference={"users"} source={"endorsee_id"}
                                        link={(record, reference) => `/${reference}/${record.id}`} >
                            <TextField source={"last_name"} fontStyle={{fontSize: '1rem'}} />
                            {", "}
                            <TextField source={"first_name"} fontStyle={{fontSize: '1rem'}} />
                        </ReferenceField>
                    </TableCell>
                </TableRow>
            </RecordContextProvider>
        );
    }

    return (
        <Card >
            <CardHeader title="Endorsements" />
            {endorsements && endorsements.length > 0 ? (
                <Table >
                    {endorsements.map((endorsement: any) => <Endorsement endorsement={endorsement} />)}
                </Table>
            ) : (
                <Typography sx={{ m: 1, p: 1 }} variant={"body2"} fontWeight={"700"}>No existing endorsements</Typography>
            )}
        </Card>
    );
}



const EndorsementRequestEditToolbar = () => (
    <Toolbar>
        <SaveButton />
    </Toolbar>
);

export const EndorsementRequestEdit = () => {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [categoryChoices, setCategoryChoices] = useState<Category[]>([]);
    const [categoryChoice, setCategoryChoice] = useState<Category>();
    const [subjectChoices, setSubjectChoices] = useState<CategorySubject[]>([]);
    const [demographic, setDemographic] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchCategories = async () => {
            try {
                const { data } = await dataProvider.getList<Category>('categories', {
                    filter: {},
                    sort: { field: 'name', order: 'ASC' },
                });
                setCategoryChoices(data);
            } catch (error) {
                console.error("Error fetching categories:", error);
            }
        };

        fetchCategories();
    }, [dataProvider]);

    useEffect(() => {
        if (categoryChoice?.id) {

            dataProvider.getList<CategorySubject>('subject_class', {
                filter: {archive: categoryChoice.id},
                sort: {field: 'name', order: 'ASC'},
            }).then(result => {
                console.log("subject_class: " + result);
                setSubjectChoices(result.data);
            });
        }
    }, [dataProvider, categoryChoice]);

    useEffect(() => {
        const fetchDemographic = async (userId: number) => {
            try {
                const response = await dataProvider.getOne('demographics', {id: userId});
                setDemographic(response.data);
                setLoading(false);
            } catch (error) {
                console.error("Error fetching demographic data:", error);
                setLoading(false);
            }
        };

        if (record)
            fetchDemographic(record.endorsee_id);
    }, [dataProvider, record]);



    const handleCategoryChange = async (event: React.ChangeEvent<HTMLSelectElement>) => {
        const categoryId = event.target.value;
        setCategoryChoice(categoryChoices.find((c) => c.id === categoryId));
    };


    return (
        <Box width={"80%"} ml={"10%"} maxWidth={"md"} gap={2}>
            <Edit title={false} actions={false} component={"div"}>
                <ConsoleTitle sx={{ml: 2}}>
                    Edit Endorsement Request
                </ConsoleTitle>

                <Typography variant="h2" ml={"1em"}>
                    <EndorsementRequestTitle/>
                </Typography>

                <Box display="flex" flexDirection="row" gap={2} m={2}>
                    <Paper elevation={3} sx={{ mb: 1, pb: 0, alignSelf: 'flex-start' }}>
                        <SimpleForm toolbar={<EndorsementRequestEditToolbar />}>
                            <Box ml={3} flexGrow={1} display="flex" flexDirection="row" justifyContent="space-between">
                                <BooleanInput source={"flag_valid"} label={"Valid"} />
                                <BooleanInput source={"flag_open"} label={"Open"} />
                            </Box>

                            <Table size={"small"}>
                                <TableRow>
                                    <TableCell>
                                        ID
                                    </TableCell>
                                    <TableCell>
                                        <TextField source="id" />
                                    </TableCell>
                                </TableRow>

                                <TableRow>
                                    <TableCell>
                                        Category
                                    </TableCell>
                                    <TableCell>
                                        <CategoryField sourceCategory={"archive"} sourceClass={"subject_class"} source={"archive"} label={"Category"}/>
                                    </TableCell>
                                </TableRow>

                                <TableRow>
                                    <TableCell>
                                        Endorsee
                                    </TableCell>
                                    <TableCell>
                                        <ReferenceField source="endorsee_id" reference="users"
                                                        link={(record, reference) => `/${reference}/${record.id}`} >
                                            <UserNameField withEmail withUsername />
                                        </ReferenceField>
                                    </TableCell>
                                </TableRow>

                                <TableRow>
                                    <TableCell>
                                        Endorser
                                    </TableCell>
                                    <TableCell>
                                        <ReferenceInput source="endorser_id" reference="users">
                                            <UserNameField withEmail withUsername />
                                        </ReferenceInput>
                                    </TableCell>
                                </TableRow>

                                <TableRow>
                                    <TableCell>
                                        Issued when
                                    </TableCell>
                                    <TableCell>
                                        <ISODateField source="issued_when"  label={"Issued"}/>
                                    </TableCell>
                                </TableRow>

                            </Table>
                        </SimpleForm>
                    </Paper>

                    <ShowDemographic />
                </Box>

                <Box mt={2}>
                    <ListEndorsements />
                </Box>

            </Edit>

        </Box>
    );
}


export const EndorsementRequestCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceInput source="endorsementRequestname" reference="endorsementRequests" />
            <TextInput source="first_name" />
            <TextInput source="last_name" />
            <TextInput source="email" />
        </SimpleForm>
    </Create>
);


export const EndorsementRequestShow = () => (
    <Show>
        <SimpleShowLayout>
            <TextField source="id" />
            <ReferenceField source="endorsee_id" reference="users"
                            link={(record, reference) => `/${reference}/${record.id}`} >
                <TextField source={"last_name"} />
                {", "}
                <TextField source={"first_name"} />
            </ReferenceField>
            <TextField source="archive" />
            <TextField source="subject_class" />
            <BooleanField source="flag_valid" />
            <ISODateField source="issued_when" />
            <NumberField source="point_value" />
            <BooleanField source="flag_suspect" />
            <TextField source="arXiv_categories" />
        </SimpleShowLayout>
    </Show>
);
