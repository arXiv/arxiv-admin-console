import React, {useState, useEffect} from 'react';

import {Grid, useMediaQuery, Table, TableRow, TableCell} from '@mui/material';
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
    useListContext,
    ReferenceField,
    NumberInput,
    Show,
    SimpleShowLayout, useGetOne, RecordContextProvider, Identifier,
} from 'react-admin';

import CategoryField from "../bits/CategoryField";

import { addDays } from 'date-fns';
import PointValueBooleanField from "../bits/PointValueBooleanField";

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


const EndorsementRequestFilter = (props: any) => {
    const { setFilters, filterValues } = useListContext();
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
            <BooleanInput label="Open" source="not_positive" alwaysOn/>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />
            <DateInput label="Start Date" source="start_date" />
            <DateInput label="End Date" source="end_date" />
            <BooleanInput label="Valid" source="flag_valid" defaultValue="true"/>

            <TextInput label="First Name" source="endorsee_first_name" />
            <TextInput label="Last Name" source="endorsee_last_name" />
            <TextInput label="Email Address" source="endorsee_email" />
        </Filter>
    );
};


export const EndorsementRequestList = () => {
    const sorter: SortPayload = {field: 'endorsementRequest_id', order: 'ASC'};
    const isSmall = useMediaQuery<any>(theme => theme.breakpoints.down('sm'));
    return (
        <List filters={<EndorsementRequestFilter />}
              filterDefaultValues={{not_positive: true}}
              sort={{field: 'id', order: 'DESC'}}>
            {isSmall ? (
                <SimpleList
                    primaryText={record => record.name}
                    secondaryText={record => record.endorsementRequestname}
                    tertiaryText={record => record.email}
                />
            ) : (
                <Datagrid rowClick="edit" sort={sorter} >
                    <NumberField source="id" label={"ID"}/>
                    <ReferenceField source="endorsee_id" reference="users"
                                    link={(record, reference) => `/${reference}/${record.id}`} >
                        <TextField source={"last_name"} />
                        {", "}
                        <TextField source={"first_name"} />
                        {"  ("}
                        <TextField source={"username"} />
                        {") <"}
                        <TextField source={"email"} />
                        {">"}
                    </ReferenceField>

                    <CategoryField label={"Category"} source="id" sourceCategory="archive" sourceClass="subject_class" />
                    <DateField source="issued_when" label={"Issued"}/>

                    <TextField source={"secret"} />

                    <ReferenceField source="id" reference="endorsement_requests_audit" label={"Remote host"}>
                        <TextField source={"remote_host"} label={"Remote host"}/>
                    </ReferenceField>
                    <BooleanField source="flag_valid" label={"Valid"} FalseIcon={null} />
                    <PointValueBooleanField source="point_value" label={"Open"} />
                </Datagrid>
            )}
        </List>
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
            Endorsement Request {user ? `"${user.last_name}, ${user.first_name}" - ${user.email}` : ''}
        </span>
    );
};


export const ShowDemographic = () => {
    const record = useRecordContext();
    const dataProvider = useDataProvider();
    const [demographic, setDemographic] = useState<any>(null);
    const [loading, setLoading] = useState(true);

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

        if (record) {
            fetchDemographic(record.endorsee_id);
        }
    }, [dataProvider, record]);


    return (
        <Table>
            <TableRow>
                <TableCell>Session ID</TableCell>
                <TableCell>
                    <ReferenceField source={"id"} reference="endorsement_requests_audit">
                        <TextField source={"session_id"}/>
                    </ReferenceField>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Remote Hostname</TableCell>
                <TableCell>
                    <ReferenceField source={"id"} reference="endorsement_requests_audit">
                        <TextField source={"remote_host"}/>
                    </ReferenceField>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Remote Address</TableCell>
                <TableCell>
                    <ReferenceField source={"id"} reference="endorsement_requests_audit">
                        <TextField source={"remote_addr"}/>
                    </ReferenceField>
                </TableCell>
            </TableRow>
            <TableRow>
                <TableCell>Endorsement Code</TableCell>
                <TableCell>
                    <TextField source={"secret"}/>
                </TableCell>
            </TableRow>
            <RecordContextProvider value={demographic}>
                <TableRow>
                    <TableCell>Affiliation</TableCell>
                    <TableCell>
                            <TextField source={"affiliation"}/>
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableCell>Country</TableCell>
                    <TableCell>
                        <TextField source={"country"}/>
                    </TableCell>
                </TableRow>
                <TableRow>
                    <TableCell>URL</TableCell>
                    <TableCell>
                        <RecordContextProvider value={demographic}>
                            <TextField source={"url"}/>
                        </RecordContextProvider>
                    </TableCell>
                </TableRow>
            </RecordContextProvider>
        </Table>
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
                    <TableCell><CategoryField sourceCategory={"archive"} sourceClass={"subject_class"} source={"id"} /> </TableCell>
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
        <Table >
            {endorsements?.map((endorsement: any) => <Endorsement endorsement={endorsement} />)}
        </Table>
    );
}



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
        <Edit title={<EndorsementRequestTitle />}>
            <Grid container>
                <Grid item xs={6}>
                    <SimpleForm>
                        <Grid container item xs={12}>
                            <Grid item xs={4}>
                                <BooleanInput name={"flag-Valid"} source={"flag_valid"} label={"Valid"} />
                            </Grid>
                            <Grid item xs={4}>
                                <BooleanInput name={"flag-Open"} source={"flag_open"} label={"Open"} />
                            </Grid>
                        </Grid>
                        <Grid container item xs={12}>
                            <Grid item xs={2}>ID:</Grid>
                            <Grid item xs={4}><TextField source="id" /></Grid>
                            <Grid item xs={2}>Category:</Grid>
                            <Grid item xs={4}>
                                <CategoryField sourceCategory={"archive"} sourceClass={"subject_class"} source={"id"} label={"Category"}/>
                            </Grid>
                        </Grid>
                        <Grid container item xs={12}>
                            <ReferenceField source="endorsee_id" reference="users"
                                            link={(record, reference) => `/${reference}/${record.id}`} >
                                <TextField source={"last_name"} fontStyle={{fontSize: '1rem'}} />
                                {", "}
                                <TextField source={"first_name"} fontStyle={{fontSize: '1rem'}} />
                            </ReferenceField>
                        </Grid>

                        <Grid container item xs={12}>
                            <ReferenceInput source="endorser_id" reference="users">
                                <TextField source={"last_name"} fontStyle={{fontSize: '1rem'}} />
                                <TextField source={"first_name"} fontStyle={{fontSize: '1rem'}} />
                            </ReferenceInput>
                        </Grid>
                        <Grid container item xs={12}>
                            Issued when: <DateField source="issued_when"  label={"Issued"}/>
                        </Grid>
                    </SimpleForm>
                    <Grid >
                        <ListEndorsements />
                    </Grid>
                </Grid>
                <Grid item xs={6}>
                    <ShowDemographic />
                </Grid>
            </Grid>
        </Edit>
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
            <DateField source="issued_when" />
            <NumberField source="point_value" />
            <BooleanField source="flag_suspect" />
            <TextField source="arXiv_categories" />
        </SimpleShowLayout>
    </Show>
);
