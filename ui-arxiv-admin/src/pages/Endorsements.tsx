import {ReactNode, useEffect, useState, useContext} from 'react';
import {
    useMediaQuery,
    Card,
    CardContent,
    CardHeader,
    Chip,
    IconButton,
    Divider,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    ToggleButton,
    TableSortLabel
} from '@mui/material';
import {NavigateBefore, NavigateNext, FirstPage, LastPage} from '@mui/icons-material';
import {useNavigate} from 'react-router-dom';
import {
    List,
    SimpleList,
    Datagrid,
    TextField,
    EmailField,
    SortPayload,
    NumberInput,
    useRecordContext,
    Edit,
    SimpleForm,
    TextInput,
    ReferenceInput,
    Create,
    Filter,
    BooleanInput,
    ReferenceField,
    NumberField,
    DateInput, useListContext, SelectInput, SelectField,
    NullableBooleanInput, Identifier, Toolbar, SaveButton, TopToolbar
} from 'react-admin';

import BooleanField from "../bits/BooleanNumberField";
import React from "react";
import CategoryField from "../bits/CategoryField";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Tooltip from '@mui/material/Tooltip';
import UserNameField from "../bits/UserNameField";
import UserStatusField from "../bits/UserStatusField";
import ISODateField from "../bits/ISODateFiled";
import {RuntimeContext} from "../RuntimeContext";

/*
    endorser_id: Optional[int] # Mapped[Optional[int]] = mapped_column(ForeignKey('tapir_users.user_id'), index=True)
    endorsee_id: int # Mapped[int] = mapped_column(ForeignKey('tapir_users.user_id'), nullable=False, index=True, server_default=FetchedValue())
    archive: str #  mapped_column(String(16), nullable=False, server_default=FetchedValue())
    subject_class: str # Mapped[str] = mapped_column(String(16), nullable=False, server_default=FetchedValue())
    flag_valid: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    type: str | None # Mapped[Optional[Literal['user', 'admin', 'auto']]] = mapped_column(Enum('user', 'admin', 'auto'))
    point_value: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    issued_when: int # Mapped[int] = mapped_column(Integer, nullable=False, server_default=FetchedValue())
    request_id: int | None # Mapped[Optional[int]] = mapped_column(ForeignKey('arXiv_endorsement_requests.request_id'), index=True)

 */

const presetOptions = [
    {id: 'last_1_day', name: 'Last 1 Day'},
    {id: 'last_7_days', name: 'Last 7 Days'},
    {id: 'last_28_days', name: 'Last 28 Days'},
];

const endorsementTypeOptions = [
    {id: 'user', name: 'By User'},
    {id: 'admin', name: 'By Admin'},
    {id: 'auto', name: 'Auto'},
];


const EndorsementFilter = (props: any) => {
    const {setFilters, filterValues} = useListContext();
    const handlePresetChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const preset_value = event?.target.value;
        setFilters({
            ...filterValues,
            preset: preset_value,
        });
    };

    const handleEndorsementTypeChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
        const et_value = event?.target.value;
        setFilters({
            ...filterValues,
            "type": et_value,
        });
    };


    return (
        <Filter {...props}>
            <SelectInput
                label="Preset Date Range"
                source="preset"
                choices={presetOptions}
                onChange={(event) => handlePresetChange(event as React.ChangeEvent<HTMLSelectElement>)}
            />
            <SelectInput
                label="Endorsement Type"
                source="type"
                choices={endorsementTypeOptions}
                onChange={(event) => handleEndorsementTypeChange(event as React.ChangeEvent<HTMLSelectElement>)}
                alwaysOn
            />

            <NullableBooleanInput label="Positive" source="positive_endorsement" alwaysOn/>
            <TextInput label={"Name"} source={"endorsee_name"} alwaysOn size={"small"}/>
            <TextInput label={"Email"} source={"endorsee_email"} alwaysOn/>
            <TextInput label={"Category"} source={"category"} alwaysOn/>

            <DateInput label="Start Date" source="start_date"/>
            <DateInput label="End Date" source="end_date"/>
            <BooleanInput label="Valid" source="flag_valid"/>
            <BooleanInput label="Flagged" source="by_suspct"/>
        </Filter>
    );
};

const WithTooltip = ({children}: { children: ReactNode }) => {
    const record = useRecordContext();
    if (!record) return null;

    return (
        <Tooltip title={record.comment || ''} arrow placement="top">
            <span>{children}</span>
        </Tooltip>
    );
};

// Hook to fetch and cache endorsement IDs
const useEndorsementIds = (filters: any) => {
    const runtimeProps = useContext(RuntimeContext);
    const [endorsementIds, setEndorsementIds] = useState<number[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchIds = async () => {
            if (!filters) return;

            setLoading(true);
            setError(null);

            try {
                const getIds = runtimeProps.adminFetcher.path('/v1/endorsements/ids/').method('get').create();
                const response = await getIds(filters);

                if (response.ok) {
                    setEndorsementIds(response.data);
                } else {
                    setError('Failed to fetch endorsement IDs');
                }
            } catch (err) {
                setError('Error fetching endorsement IDs');
                console.error('Error fetching endorsement IDs:', err);
            } finally {
                setLoading(false);
            }
        };

        fetchIds();
    }, [JSON.stringify(filters), runtimeProps.adminFetcher]);

    return {endorsementIds, loading, error};
};

// Navigation component for showing cached IDs
const EndorsementNavigation = ({currentId, filters}: { currentId?: Identifier, filters: any }) => {
    const navigate = useNavigate();
    const {endorsementIds, loading, error} = useEndorsementIds(filters);

    const currentIndex = currentId ? endorsementIds.findIndex(id => id === Number(currentId)) : -1;
    const prevId = currentIndex > 0 ? endorsementIds[currentIndex - 1] : null;
    const nextId = currentIndex >= 0 && currentIndex < endorsementIds.length - 1 ? endorsementIds[currentIndex + 1] : null;

    const handleNavigate = (id: number) => {
        navigate(`/endorsements/${id}/edit`);
    };

    const handlePrevious = () => prevId && handleNavigate(prevId);
    const handleNext = () => nextId && handleNavigate(nextId);

    // Scroll current record into view
    useEffect(() => {
        if (currentIndex >= 0 && endorsementIds.length > 0) {
            const currentElement = document.querySelector(`[data-endorsement-id="${currentId}"]`);
            if (currentElement) {
                currentElement.scrollIntoView({behavior: 'smooth', block: 'center'});
            }
        }
    }, [currentIndex, currentId, endorsementIds.length]);

    if (loading) return <Typography variant="body2">Loading navigation...</Typography>;
    if (error) return <Typography variant="body2" color="error">{error}</Typography>;
    if (!endorsementIds.length) return <Typography variant="body2">No endorsements found</Typography>;

    return (
        <Card sx={{width: '100%', maxHeight: 600, overflow: 'hidden', display: 'flex', flexDirection: 'column'}}>
            <CardHeader
                title={null}
                titleTypographyProps={{variant: 'subtitle2'}}
                subheader={`${endorsementIds.length} IDs`}
                subheaderTypographyProps={{variant: 'caption'}}
                sx={{padding: 1}}
            />
            <Divider/>
            <CardContent sx={{flex: 1, overflow: 'auto', padding: 0.5}}>
                <Box display="flex" flexDirection="column" gap={0.25}>
                    {endorsementIds.map((id, index) => {
                        const isCurrent = Number(id) === Number(currentId);
                        const isPrev = Number(id) === Number(prevId);
                        const isNext = Number(id) === Number(nextId);

                        return (
                            <Chip
                                key={id}
                                data-endorsement-id={id}
                                label={`${id}`}
                                size="small"
                                variant={isCurrent ? "filled" : "outlined"}
                                color={isCurrent ? "primary" : isPrev || isNext ? "secondary" : "default"}
                                onClick={() => handleNavigate(id)}
                                sx={{
                                    width: '100%',
                                    justifyContent: 'flex-start',
                                    cursor: 'pointer',
                                    fontSize: '0.7rem',
                                    height: '20px',
                                    backgroundColor: isCurrent ? 'primary.main' : 'transparent',
                                    color: isCurrent ? 'primary.contrastText' : 'inherit',
                                    fontWeight: isCurrent ? 'bold' : 'normal',
                                    border: isCurrent ? '2px solid' : '1px solid',
                                    borderColor: isCurrent ? 'primary.dark' : 'divider',
                                    '&:hover': {
                                        backgroundColor: isCurrent ? 'primary.dark' : 'action.hover',
                                        borderColor: isCurrent ? 'primary.dark' : 'primary.light'
                                    }
                                }}
                            />
                        );
                    })}
                </Box>
            </CardContent>
        </Card>
    );
};


export const EndorsementList = () => {
    return (
        <List
            filters={<EndorsementFilter/>}
            filterDefaultValues={{
                type: "user",
                positive_endorsement: false
            }}
        >
            <Datagrid rowClick="edit" bulkActionButtons={false}>
                <NumberField source={"id"}/>
                <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                                link={(record, reference) => `/${reference}/${record.id}`}>
                    <UserNameField withUsername/>
                </ReferenceField>

                <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                                link={(record, reference) => `/${reference}/${record.id}`}>
                    <UserNameField withUsername/>
                </ReferenceField>

                <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category"/>
                <ISODateField source="issued_when" label={"Issued"} showTime/>
                <BooleanField source="flag_valid" label={"Valid"} FalseIcon={null}/>

                <TextField source="type"/>
                <NumberField source="point_value" label={"Point"}/>

                <ReferenceField source="request_id" reference="endorsement_requests" label={"Request"}
                                link={(record, reference) => `/${reference}/${record.id}`}>
                    Show
                </ReferenceField>
            </Datagrid>
        </List>
    );
};


const EndorsementTitle = () => {
    const record = useRecordContext();
    if (!record) return null;
    const action = record.positive_endorsement ? " trusts " : " dosen't trust ";

    const endorser = record["type"] === "user" ? (
        <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                        link={(record, reference) => `/${reference}/${record.id}`}>
            <TextField source={"first_name"}/>
            {" "}
            <TextField source={"last_name"}/>
        </ReferenceField>
    ) : (
        record["type"] === "admin" ? "EUST" : "arXiv system"
    );

    return (
        <Box sx={{flex: 8, display: 'flex', flexDirection: 'row', gap: 1, alignItems: 'baseline'}}>
            {endorser}
            {action}
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"first_name"}/>
                {" "}
                <TextField source={"last_name"}/>
            </ReferenceField>
            {" for "}
            <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id" label="Category"/>
        </Box>
    )

};

// Component that accesses record context and sets the current ID
const CurrentIdSetter = ({setCurrentId}: { setCurrentId: (id: Identifier) => void }) => {
    const record = useRecordContext();

    useEffect(() => {
        if (record?.id) {
            setCurrentId(record.id);
        }
    }, [record?.id, setCurrentId]);

    return null; // This component doesn't render anything
};

// Custom form toolbar with only Save button (no Delete)
const EndorsementFormToolbar = () => (
    <Toolbar>
        <SaveButton />
    </Toolbar>
);

// Custom toolbar for navigation filters
const EndorsementEditToolbar = ({ 
    navigationFilters, 
    setNavigationFilters,
    currentId,
    endorsementIds
}: { 
    navigationFilters: any, 
    setNavigationFilters: (filters: any) => void,
    currentId?: Identifier,
    endorsementIds: number[]
}) => {
    const navigate = useNavigate();
    
    // Navigation logic
    const currentIndex = currentId ? endorsementIds.findIndex(id => id === Number(currentId)) : -1;
    const firstId = endorsementIds.length > 0 ? endorsementIds[0] : null;
    const lastId = endorsementIds.length > 0 ? endorsementIds[endorsementIds.length - 1] : null;
    const prevId = currentIndex > 0 ? endorsementIds[currentIndex - 1] : null;
    const nextId = currentIndex >= 0 && currentIndex < endorsementIds.length - 1 ? endorsementIds[currentIndex + 1] : null;

    const handleNavigate = (id: number) => {
        navigate(`/endorsements/${id}/edit`);
    };

    const handleFirst = () => firstId && handleNavigate(firstId);
    const handlePrevious = () => prevId && handleNavigate(prevId);
    const handleNext = () => nextId && handleNavigate(nextId);
    const handleLast = () => lastId && handleNavigate(lastId);

    const handleTypeChange = (event: any) => {
        const value = event.target.value;
        setNavigationFilters({
            ...navigationFilters,
            type: value === '' ? null : value
        });
    };

    const handlePresetChange = (event: any) => {
        setNavigationFilters({
            ...navigationFilters,
            preset: event.target.value
        });
    };

    const handleFlaggedToggle = () => {
        setNavigationFilters({
            ...navigationFilters,
            by_suspect: !navigationFilters.by_suspect
        });
    };

    const handlePositiveChange = (event: any) => {
        const value = event.target.value;
        setNavigationFilters({
            ...navigationFilters,
            positive_endorsement: value === '' ? null : value === 'true'
        });
    };

    const handleReverseSort = () => {
        setNavigationFilters({
            ...navigationFilters,
            _order: navigationFilters?._order != 'ASC' ? 'ASC' : 'DESC'
        });
    };

    return (
        <TopToolbar sx={{ justifyContent: 'flex-start' }}>
            <Box display="flex" gap={2} alignItems="center">
                {/* Navigation buttons */}
                <Box display="flex" gap={0.5}>
                    <IconButton 
                        onClick={handleFirst} 
                        disabled={!firstId || currentId === firstId} 
                        size="small"
                        title="First"
                    >
                        <FirstPage fontSize="small" />
                    </IconButton>
                    <IconButton 
                        onClick={handlePrevious} 
                        disabled={!prevId} 
                        size="small"
                        title="Previous"
                    >
                        <NavigateBefore fontSize="small" />
                    </IconButton>
                    <IconButton 
                        onClick={handleNext} 
                        disabled={!nextId} 
                        size="small"
                        title="Next"
                    >
                        <NavigateNext fontSize="small" />
                    </IconButton>
                    <IconButton 
                        onClick={handleLast} 
                        disabled={!lastId || currentId === lastId} 
                        size="small"
                        title="Last"
                    >
                        <LastPage fontSize="small" />
                    </IconButton>
                </Box>

                <TableSortLabel
                    active={true}
                    direction={navigationFilters?._order !== 'ASC' ? 'desc' : 'asc'}
                    onClick={handleReverseSort}
                >
                    ID
                </TableSortLabel>

                <FormControl size="small" sx={{ minWidth: 100 }}>
                    <InputLabel>Type</InputLabel>
                    <Select
                        value={navigationFilters.type || ''}
                        label="Type"
                        onChange={handleTypeChange}
                    >
                        <MenuItem value="">All</MenuItem>
                        {endorsementTypeOptions.map(option => (
                            <MenuItem key={option.id} value={option.id}>
                                {option.name}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 120 }}>
                    <InputLabel>Preset</InputLabel>
                    <Select
                        value={navigationFilters.preset || ''}
                        label="Preset"
                        onChange={handlePresetChange}
                    >
                        <MenuItem value="">None</MenuItem>
                        {presetOptions.map(option => (
                            <MenuItem key={option.id} value={option.id}>
                                {option.name}
                            </MenuItem>
                        ))}
                    </Select>
                </FormControl>

                <FormControl size="small" sx={{ minWidth: 80 }}>
                    <InputLabel>Positive</InputLabel>
                    <Select
                        value={
                            navigationFilters.positive_endorsement === null || navigationFilters.positive_endorsement === undefined
                                ? ''
                                : navigationFilters.positive_endorsement.toString()
                        }
                        label="Positive"
                        onChange={handlePositiveChange}
                    >
                        <MenuItem value="">All</MenuItem>
                        <MenuItem value="true">Yes</MenuItem>
                        <MenuItem value="false">No</MenuItem>
                    </Select>
                </FormControl>

                <ToggleButton
                    value="by_suspect"
                    selected={navigationFilters.by_suspect || false}
                    onChange={handleFlaggedToggle}
                    size="small"
                >
                    Flagged
                </ToggleButton>
            </Box>
        </TopToolbar>
    );
};

export const EndorsementEdit = () => {
    const leftWidth = "80px";
    const [currentId, setCurrentId] = useState<Identifier | undefined>(undefined);
    const [navigationFilters, setNavigationFilters] = useState<any>(
        {type: null, positive_endorsement: false}
    );
    
    // Get endorsement IDs for navigation
    const { endorsementIds } = useEndorsementIds(navigationFilters);


    return (
        <Box display="flex" flexDirection="row" gap={2}>
            <Box width={90}>
                <EndorsementNavigation currentId={currentId}
                                       filters={navigationFilters}/>
            </Box>
            <Box flex={1}>
                <Edit 
                    title={<EndorsementTitle/>}
                    actions={<EndorsementEditToolbar 
                        navigationFilters={navigationFilters} 
                        setNavigationFilters={setNavigationFilters}
                        currentId={currentId}
                        endorsementIds={endorsementIds}
                    />}
                >
                    <SimpleForm toolbar={<EndorsementFormToolbar />}>
                        <CurrentIdSetter setCurrentId={setCurrentId}/>
                        <div style={{
                            display: 'grid',
                            gridTemplateColumns: '1fr 1fr',
                            gridTemplateRows: 'repeat(2, 1fr)',
                            height: '100%',
                            minWidth: '60%',
                            gap: '0px 8px',
                        }}>
                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"ID: "}</Typography>
                                <NumberField source="id"/>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Request ID: "}</Typography>
                                <ReferenceField source="request_id" reference="endorsement_requests"
                                                label={"Endorsement Request"}
                                                link={(record, reference) => `/${reference}/${record.id}`}>
                                    <NumberField source={"id"}/>
                                </ReferenceField>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Category: "}</Typography>
                                <CategoryField sourceCategory="archive" sourceClass="subject_class" source="id"
                                               label="Category"/>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Issued on: "}</Typography>
                                <ISODateField source="issued_when"/>
                            </Box>


                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Endorser: "}</Typography>

                                <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                                                link={(record, reference) => `/${reference}/${record.id}`}>
                                    <UserNameField/>
                                    <UserStatusField source={"id"}/>
                                </ReferenceField>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Session: "}</Typography>
                                <ReferenceField source="session_id" reference="tapir_sessions" label={"Session ID"}
                                                link={(record, reference) => `/${reference}/${record.id}/edit`}>
                                    <NumberField source="id"/>
                                </ReferenceField>

                                <ReferenceField source="session_id" reference="tapir_sessions" label={"Session ID"} link={false}>
                                    {" "}
                                    <ISODateField source="start_time" showTime/>
                                    {" - "}
                                    <ISODateField source="end_time" showTime/>
                                </ReferenceField>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Endorsee: "}</Typography>
                                <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                                                link={(record, reference) => `/${reference}/${record.id}`}>
                                    <UserNameField/>
                                    <UserStatusField source={"id"}/>
                                </ReferenceField>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Remote Hostname: "}</Typography>
                                <TextField source={"remote_host"}/>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Endorsement type: "}</Typography>
                                <SelectField source="type" choices={endorsementTypeOptions}/>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Remote Address: "}</Typography>
                                <TextField source={"remote_addr"}/>
                            </Box>
                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Knows Presonally: "}</Typography>
                                <BooleanField source="flag_knows_personally"/>
                                <Typography minWidth={leftWidth}>{"Seen Paper: "}</Typography>
                                <BooleanField source="flag_seen_paper"/>
                            </Box>

                            <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                                <Typography minWidth={leftWidth}>{"Tracking Cookie: "}</Typography>
                                <TextField source="tracking_cookie"/>
                            </Box>
                        </div>
                        <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                            <Typography minWidth={leftWidth}>{"Point Value: "}</Typography>
                            <NumberField source={"point_value"}/>
                        </Box>

                        <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                            <Typography minWidth={leftWidth}>{"Comment: "}</Typography>
                            <TextField source={"comment"}/>
                        </Box>

                        <Box display="flex" justifyContent="left" alignItems="center" gap={1}>
                            <BooleanInput source="flag_valid" label={"Valid"} size={"small"} helperText={false}/>
                            <BooleanInput source="positive_endorsement" label={"Positive"} size={"small"}
                                          helperText={false}/>
                        </Box>

                    </SimpleForm>
                </Edit>
            </Box>
        </Box>
    );
}


export const EndorsementCreate = () => (
    <Create>
        <SimpleForm>
            <ReferenceField source="endorsee_id" reference="users" label={"Endorsee"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <ReferenceField source="endorser_id" reference="users" label={"Endorser"}
                            link={(record, reference) => `/${reference}/${record.id}`}>
                <TextField source={"last_name"}/>
                {", "}
                <TextField source={"first_name"}/>
            </ReferenceField>

            <TextInput source="archive"/>

            <TextInput source="subject_class"/>
            <BooleanInput source="flag_valid" label={"Valid"}/>

            <TextInput source="type"/>
            <NumberInput source="point_value" label={"Point"}/>
            <DateInput source="issued_when" label={"Issued"}/>

        </SimpleForm>
    </Create>
);


